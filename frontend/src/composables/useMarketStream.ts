import { onUnmounted } from 'vue'
import { tokens } from '@/lib/http'
import type { Order, Product } from '@/api/market'

/**
 * 대장마켓 실시간 이벤트 구독 컴포저블.
 *
 * - 쫄병: product.created / product.updated / product.deleted (상점 목록 갱신)
 * - 대장: order.created (신규 주문 알림)
 *
 * SSE(EventSource)는 헤더를 못 실어 access token을 query로 전달한다.
 * (홈 화면의 useCoinStream과 별개 연결이지만, 이벤트 버스가 사용자당
 *  다중 구독을 허용하므로 문제없다.)
 */
export interface MarketHandlers {
  onProductCreated?: (p: Product) => void
  onProductUpdated?: (p: Product) => void
  onProductDeleted?: (productId: number) => void
  onOrderCreated?: (o: Order) => void
}

export function useMarketStream(handlers: MarketHandlers) {
  let es: EventSource | null = null

  function connect() {
    disconnect()
    const token = tokens.access
    if (!token) return
    es = new EventSource(`/api/stream?token=${encodeURIComponent(token)}`)

    es.addEventListener('product.created', (e) => {
      const d = JSON.parse((e as MessageEvent).data)
      handlers.onProductCreated?.(d.product as Product)
    })
    es.addEventListener('product.updated', (e) => {
      const d = JSON.parse((e as MessageEvent).data)
      handlers.onProductUpdated?.(d.product as Product)
    })
    es.addEventListener('product.deleted', (e) => {
      const d = JSON.parse((e as MessageEvent).data)
      handlers.onProductDeleted?.(d.product_id as number)
    })
    es.addEventListener('order.created', (e) => {
      const d = JSON.parse((e as MessageEvent).data)
      handlers.onOrderCreated?.(d.order as Order)
    })
  }

  function disconnect() {
    es?.close()
    es = null
  }

  onUnmounted(disconnect)

  return { connect, disconnect }
}
