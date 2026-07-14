export interface SeedResult {
  group_id: number
  boss_id: number
  minion_id: number
  minion_balance: number
}

export interface GrantResult {
  minion_id: number
  balance: number
  delta: number
}

async function post<T>(url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`)
  return res.json() as Promise<T>
}

export const demoApi = {
  seed: () => post<SeedResult>('/api/demo/seed'),
  grant: (minionId: number, amount: number, reason: string | null) =>
    post<GrantResult>('/api/demo/grant', {
      minion_id: minionId,
      amount,
      reason,
    }),
}
