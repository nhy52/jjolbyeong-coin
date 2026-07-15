"""대장마켓 라우터.

- 대장(require_boss): 상품 CRUD, 이미지 업로드, 주문 목록/수령완료.
- 쫄병(require_active + minion): 상품 목록/상세, 구매, 내 주문.

상품 이미지는 backend/uploads/products/ 에 저장하고 /api/uploads/... 로 서빙한다
(개발 시 Vite가 /api 를 프록시하므로 같은 경로로 접근 가능).
"""

from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_active, require_boss
from app.models import User, UserRole
from app.schemas import (
    ImageUploadResult,
    OrderOut,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    PurchaseResult,
)
from app.services import market

router = APIRouter()

# 업로드 저장 위치: backend/uploads/products
UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads"
PRODUCT_IMAGE_DIR = UPLOAD_ROOT / "products"
_ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5MB


def _require_group(user: User) -> int:
    if user.group_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "소속 그룹이 없습니다.")
    return user.group_id


# ===== 대장: 상품 관리 =====
@router.get("/products", response_model=list[ProductOut])
def list_products(boss: User = Depends(require_boss), db: Session = Depends(get_db)):
    return market.list_products_for_boss(db, _require_group(boss))


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate, boss: User = Depends(require_boss), db: Session = Depends(get_db)
):
    return await market.create_product(db, _require_group(boss), data)


@router.patch("/products/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    boss: User = Depends(require_boss),
    db: Session = Depends(get_db),
):
    return await market.update_product(db, _require_group(boss), product_id, data)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int, boss: User = Depends(require_boss), db: Session = Depends(get_db)
):
    await market.delete_product(db, _require_group(boss), product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/upload", response_model=ImageUploadResult)
async def upload_image(
    file: UploadFile = File(...), boss: User = Depends(require_boss)
) -> ImageUploadResult:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in _ALLOWED_EXT:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "이미지 형식은 jpg/png/webp/gif만 가능해요."
        )
    data = await file.read()
    if len(data) > _MAX_IMAGE_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "이미지는 5MB 이하만 올릴 수 있어요.")

    PRODUCT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{secrets.token_hex(16)}{ext}"
    (PRODUCT_IMAGE_DIR / name).write_bytes(data)
    return ImageUploadResult(image_url=f"/api/uploads/products/{name}")


# ===== 대장: 주문 관리 =====
@router.get("/orders", response_model=list[OrderOut])
def list_orders(boss: User = Depends(require_boss), db: Session = Depends(get_db)):
    return market.list_orders_for_boss(db, _require_group(boss))


@router.post("/orders/{order_id}/fulfill", response_model=OrderOut)
async def fulfill_order(
    order_id: int, boss: User = Depends(require_boss), db: Session = Depends(get_db)
):
    return await market.fulfill_order(db, _require_group(boss), order_id)


# ===== 쫄병: 상점 =====
def _require_active_minion(user: User = Depends(require_active)) -> User:
    if user.role != UserRole.minion:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "쫄병 전용 기능이에요.")
    return user


@router.get("/shop", response_model=list[ProductOut])
def shop(minion: User = Depends(_require_active_minion), db: Session = Depends(get_db)):
    return market.list_products_for_shop(db, _require_group(minion))


@router.get("/shop/{product_id}", response_model=ProductOut)
def shop_detail(
    product_id: int,
    minion: User = Depends(_require_active_minion),
    db: Session = Depends(get_db),
):
    return market.get_shop_product(db, _require_group(minion), product_id)


@router.post("/shop/{product_id}/purchase", response_model=PurchaseResult)
async def purchase(
    product_id: int,
    minion: User = Depends(_require_active_minion),
    db: Session = Depends(get_db),
):
    return await market.purchase(db, minion, product_id)


@router.get("/my-orders", response_model=list[OrderOut])
def my_orders(minion: User = Depends(_require_active_minion), db: Session = Depends(get_db)):
    return market.list_my_orders(db, minion.id)
