import { api } from '@/lib/http'

export type Role = 'boss' | 'minion'
export type UserStatus = 'pending' | 'active' | 'suspended' | 'left'

export interface Me {
  id: number
  role: Role
  username: string
  email: string
  status: UserStatus
  group_id: number | null
  group_name: string | null
  invite_code: string | null
  balance: number
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface AuthResult {
  tokens: TokenPair
  user: Me
}

export interface BossRegisterInput {
  email: string
  username: string
  password: string
  group_name?: string | null
}

export interface MinionRegisterInput {
  email: string
  username: string
  password: string
  invite_code: string
  name: string
  phone?: string | null
  gender?: string | null
  age?: number | null
}

export const authApi = {
  login: (email: string, password: string) =>
    api<AuthResult>('/auth/login', { method: 'POST', body: { email, password }, auth: false }),

  registerBoss: (data: BossRegisterInput) =>
    api<AuthResult>('/auth/boss/register', { method: 'POST', body: data, auth: false }),

  registerMinion: (data: MinionRegisterInput) =>
    api<AuthResult>('/auth/minion/register', { method: 'POST', body: data, auth: false }),

  me: () => api<Me>('/auth/me'),
}
