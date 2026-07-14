import { onUnmounted, ref } from 'vue'

export interface CoinUpdate {
  type: 'coin.updated'
  balance: number
  delta: number
  reason: string | null
}

/**
 * 쫄병 코인 잔액을 SSE로 실시간 구독하는 컴포저블.
 *
 * EventSource는 연결이 끊기면 자동 재연결한다. (기획서 9장 참고)
 * PoC 단계라 user_id/group_id/role을 query로 넘긴다 — 추후 JWT로 교체.
 */
export function useCoinStream() {
  const balance = ref<number>(0)
  const connected = ref(false)
  const lastReason = ref<string | null>(null)
  const lastDelta = ref<number | null>(null)

  let es: EventSource | null = null

  function connect(userId: number, groupId: number, role = 'minion') {
    disconnect()
    const url = `/api/stream?user_id=${userId}&group_id=${groupId}&role=${role}`
    es = new EventSource(url)

    es.addEventListener('ready', () => {
      connected.value = true
    })

    es.addEventListener('coin.updated', (e) => {
      const data = JSON.parse((e as MessageEvent).data) as CoinUpdate
      balance.value = data.balance
      lastDelta.value = data.delta
      lastReason.value = data.reason
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

  return { balance, connected, lastReason, lastDelta, connect, disconnect }
}
