import { onUnmounted, ref } from 'vue'
import { tokens } from '@/lib/http'

export interface CoinUpdate {
  type: 'coin.updated'
  balance: number
  delta: number
  reason: string | null
}

/**
 * 로그인한 사용자의 실시간 이벤트를 SSE로 구독하는 컴포저블.
 *
 * EventSource는 헤더를 실을 수 없어 access token을 query(`token`)로 전달한다.
 * 연결이 끊기면 EventSource가 자동 재연결한다. (기획서 9장)
 */
export function useCoinStream() {
  const balance = ref<number>(0)
  const connected = ref(false)
  const lastReason = ref<string | null>(null)
  const lastDelta = ref<number | null>(null)
  const approved = ref(false) // 승인 이벤트 수신 여부

  let es: EventSource | null = null

  function connect() {
    disconnect()
    const token = tokens.access
    if (!token) return
    es = new EventSource(`/api/stream?token=${encodeURIComponent(token)}`)

    es.addEventListener('ready', () => {
      connected.value = true
    })

    es.addEventListener('coin.updated', (e) => {
      const data = JSON.parse((e as MessageEvent).data) as CoinUpdate
      balance.value = data.balance
      lastDelta.value = data.delta
      lastReason.value = data.reason
    })

    es.addEventListener('minion.approved', () => {
      approved.value = true
    })

    es.onerror = () => {
      connected.value = false
      // EventSource가 자동 재연결하므로 별도 처리 불필요
    }
  }

  function disconnect() {
    es?.close()
    es = null
    connected.value = false
  }

  onUnmounted(disconnect)

  return { balance, connected, lastReason, lastDelta, approved, connect, disconnect }
}
