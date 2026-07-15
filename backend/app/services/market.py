"""대장마켓 도메인 로직.

- 상품: 대장이 자기 그룹 상품을 등록/수정/삭제. 등록 시 그룹 쫄병에게 SSE 알림.
- 구매: 쫄병 잔액 검증 → 코인 차감(PURCHASE 원장) → 주문 생성 → 대장에게 SSE 알림.
- 주문: 대장이 수령완료(purchased → fulfilled) 처리.

잔액 변경은 services.coin을 재사용한다. coin.apply_transaction이 세션을 커밋하므로,
구매 시 주문·재고 변경을 먼저 flush한 뒤 차감을 호출해 한 번에 커밋되도록 한다.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.events.bus import bus
from app.models import (
    CoinTxType,
    MinionProfile,
    Order,
    OrderStatus,
    Product,
    ProductStatus,
    User,
)
from app.schemas import OrderOut, ProductCreate, ProductOut, ProductUpdate, PurchaseResult
from app.services import coin


# ----- 직렬화 헬퍼 -----
def to_product_out(p: Product) -> ProductOut:
    return ProductOut(
        id=p.id,
        name=p.name,
        price_coin=p.price_coin,
        description=p.description,
        image_url=p.image_url,
        status=p.status,
        stock=p.stock,
        created_at=p.created_at,
    )


def _order_out(order: Order, product: Product, buyer_name: str) -> OrderOut:
    return OrderOut(
        id=order.id,
        product_id=product.id,
        product_name=product.name,
        product_image_url=product.image_url,
        buyer_user_id=order.buyer_user_id,
        buyer_name=buyer_name,
        price_paid=order.price_paid,
        status=order.status,
        created_at=order.created_at,
        fulfilled_at=order.fulfilled_at,
    )


# ----- 상품 조회 -----
def _load_group_product(db: Session, group_id: int, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None or product.group_id != group_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "상품을 찾을 수 없습니다.")
    return product


def list_products_for_boss(db: Session, group_id: int) -> list[ProductOut]:
    rows = db.scalars(
        select(Product)
        .where(Product.group_id == group_id)
        .order_by(Product.created_at.desc())
    ).all()
    return [to_product_out(p) for p in rows]


def list_products_for_shop(db: Session, group_id: int) -> list[ProductOut]:
    """쫄병에게 노출되는 판매 중 상품(숨김/품절 제외는 상태로 표시)."""
    rows = db.scalars(
        select(Product)
        .where(
            Product.group_id == group_id,
            Product.status != ProductStatus.hidden,
        )
        .order_by(Product.created_at.desc())
    ).all()
    return [to_product_out(p) for p in rows]


def get_shop_product(db: Session, group_id: int, product_id: int) -> ProductOut:
    product = _load_group_product(db, group_id, product_id)
    if product.status == ProductStatus.hidden:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "상품을 찾을 수 없습니다.")
    return to_product_out(product)


# ----- 상품 CRUD (대장) -----
async def create_product(db: Session, group_id: int, data: ProductCreate) -> ProductOut:
    product = Product(
        group_id=group_id,
        name=data.name,
        price_coin=data.price_coin,
        description=data.description,
        image_url=data.image_url,
        stock=data.stock,
        status=ProductStatus.on_sale,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    out = to_product_out(product)
    # 그룹 쫄병 화면에 실시간 추가
    await bus.publish_to_group(
        group_id, {"type": "product.created", "product": out.model_dump(mode="json")}
    )
    return out


async def update_product(
    db: Session, group_id: int, product_id: int, data: ProductUpdate
) -> ProductOut:
    product = _load_group_product(db, group_id, product_id)
    fields = data.model_dump(exclude_unset=True)
    for key, value in fields.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)

    out = to_product_out(product)
    await bus.publish_to_group(
        group_id, {"type": "product.updated", "product": out.model_dump(mode="json")}
    )
    return out


async def delete_product(db: Session, group_id: int, product_id: int) -> None:
    """주문 이력이 없으면 완전 삭제, 있으면 숨김 처리(FK 보존)."""
    product = _load_group_product(db, group_id, product_id)
    has_orders = db.scalar(
        select(Order.id).where(Order.product_id == product_id).limit(1)
    )
    if has_orders:
        product.status = ProductStatus.hidden
        db.commit()
        payload = {"type": "product.updated", "product": to_product_out(product).model_dump(mode="json")}
    else:
        db.delete(product)
        db.commit()
        payload = {"type": "product.deleted", "product_id": product_id}
    await bus.publish_to_group(group_id, payload)


# ----- 구매 (쫄병) -----
async def purchase(db: Session, buyer: User, product_id: int) -> PurchaseResult:
    if buyer.group_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "소속 그룹이 없습니다.")

    product = _load_group_product(db, buyer.group_id, product_id)
    if product.status != ProductStatus.on_sale:
        raise HTTPException(status.HTTP_409_CONFLICT, "지금은 구매할 수 없는 상품이에요.")
    if product.stock is not None and product.stock <= 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "품절된 상품이에요.")
    if coin.get_balance(db, buyer.id) < product.price_coin:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "코인이 부족해요.")

    # 주문 생성 (아직 커밋 전) → 재고 차감 → 코인 차감(여기서 일괄 커밋)
    order = Order(
        product_id=product.id,
        buyer_user_id=buyer.id,
        price_paid=product.price_coin,
        status=OrderStatus.purchased,
    )
    db.add(order)
    db.flush()  # order.id 확보

    sold_out = False
    if product.stock is not None:
        product.stock -= 1
        if product.stock <= 0:
            product.status = ProductStatus.sold_out
            sold_out = True

    # 코인 차감 + 원장 기록 + 세션 커밋(order/재고 포함)
    new_balance = coin.apply_transaction(
        db,
        buyer.id,
        CoinTxType.PURCHASE,
        -product.price_coin,
        reason=f"{product.name} 구매",
        ref_id=order.id,
    )
    db.refresh(order)
    db.refresh(product)

    # 구매자 지갑 실시간 갱신
    await bus.publish_to_user(
        buyer.id,
        {
            "type": "coin.updated",
            "balance": new_balance,
            "delta": -product.price_coin,
            "reason": f"{product.name} 구매",
        },
    )
    # 대장에게 신규 주문 알림
    buyer_name = buyer.profile.name if buyer.profile else buyer.username
    await bus.publish_to_group_boss(
        buyer.group_id,
        {
            "type": "order.created",
            "order": _order_out(order, product, buyer_name).model_dump(mode="json"),
        },
    )
    # 품절 시 그룹 상품 상태 실시간 반영
    if sold_out:
        await bus.publish_to_group(
            buyer.group_id,
            {"type": "product.updated", "product": to_product_out(product).model_dump(mode="json")},
        )

    return PurchaseResult(
        order_id=order.id,
        product_id=product.id,
        price_paid=order.price_paid,
        balance=new_balance,
    )


# ----- 주문 (대장) -----
def list_orders_for_boss(db: Session, group_id: int) -> list[OrderOut]:
    rows = db.execute(
        select(Order, Product, User.username, MinionProfile.name)
        .join(Product, Product.id == Order.product_id)
        .join(User, User.id == Order.buyer_user_id)
        .join(MinionProfile, MinionProfile.user_id == User.id, isouter=True)
        .where(Product.group_id == group_id)
        .order_by(Order.created_at.desc())
    ).all()
    return [
        _order_out(order, product, name or username)
        for (order, product, username, name) in rows
    ]


async def fulfill_order(db: Session, group_id: int, order_id: int) -> OrderOut:
    row = db.execute(
        select(Order, Product)
        .join(Product, Product.id == Order.product_id)
        .where(Order.id == order_id, Product.group_id == group_id)
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "주문을 찾을 수 없습니다.")
    order, product = row
    if order.status == OrderStatus.purchased:
        order.status = OrderStatus.fulfilled
        order.fulfilled_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(order)
        await bus.publish_to_user(
            order.buyer_user_id,
            {"type": "order.updated", "order_id": order.id, "status": "fulfilled"},
        )

    buyer = db.get(User, order.buyer_user_id)
    buyer_name = (
        buyer.profile.name if (buyer and buyer.profile) else (buyer.username if buyer else "")
    )
    return _order_out(order, product, buyer_name)


def list_my_orders(db: Session, buyer_id: int) -> list[OrderOut]:
    rows = db.execute(
        select(Order, Product)
        .join(Product, Product.id == Order.product_id)
        .where(Order.buyer_user_id == buyer_id)
        .order_by(Order.created_at.desc())
    ).all()
    return [_order_out(order, product, "") for (order, product) in rows]
