import { api } from '@/lib/http'
import type { UserStatus } from '@/api/auth'

export interface MinionSummary {
  id: number
  username: string
  name: string | null
  status: UserStatus
  balance: number
  created_at: string
}

export interface GroupSummary {
  group_id: number
  group_name: string
  invite_code: string
  total_minions: number
  active_minions: number
  pending_minions: number
}

export const adminApi = {
  summary: () => api<GroupSummary>('/admin/summary'),
  minions: () => api<MinionSummary[]>('/admin/minions'),
  approve: (id: number) => api<MinionSummary>(`/admin/minions/${id}/approve`, { method: 'POST' }),
  reject: (id: number) => api(`/admin/minions/${id}/reject`, { method: 'POST' }),
  grant: (id: number, amount: number, reason: string | null) =>
    api<{ minion_id: number; balance: number; delta: number }>(
      `/admin/minions/${id}/coins`,
      { method: 'POST', body: { amount, reason } },
    ),
}
