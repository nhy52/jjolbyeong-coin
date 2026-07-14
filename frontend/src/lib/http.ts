/**
 * 인증 토큰을 붙여 /api 를 호출하는 fetch 래퍼.
 * 401이면 refresh 토큰으로 access 토큰을 한 번 갱신 후 재시도한다.
 */

const ACCESS_KEY = 'jc_access'
const REFRESH_KEY = 'jc_refresh'

export const tokens = {
  get access(): string | null {
    return localStorage.getItem(ACCESS_KEY)
  },
  get refresh(): string | null {
    return localStorage.getItem(REFRESH_KEY)
  },
  set(access: string, refresh: string) {
    localStorage.setItem(ACCESS_KEY, access)
    localStorage.setItem(REFRESH_KEY, refresh)
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

interface Options {
  method?: string
  body?: unknown
  auth?: boolean
}

async function raw(path: string, opts: Options): Promise<Response> {
  const headers: Record<string, string> = {}
  if (opts.body !== undefined) headers['Content-Type'] = 'application/json'
  if (opts.auth !== false && tokens.access) {
    headers['Authorization'] = `Bearer ${tokens.access}`
  }
  return fetch(`/api${path}`, {
    method: opts.method ?? 'GET',
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  })
}

async function tryRefresh(): Promise<boolean> {
  if (!tokens.refresh) return false
  const res = await fetch('/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: tokens.refresh }),
  })
  if (!res.ok) return false
  const data = await res.json()
  tokens.set(data.access_token, data.refresh_token)
  return true
}

export async function api<T = unknown>(path: string, opts: Options = {}): Promise<T> {
  let res = await raw(path, opts)

  if (res.status === 401 && opts.auth !== false && tokens.refresh) {
    if (await tryRefresh()) {
      res = await raw(path, opts)
    }
  }

  if (!res.ok) {
    let detail = `${res.status}`
    try {
      const err = await res.json()
      if (typeof err.detail === 'string') detail = err.detail
      else if (Array.isArray(err.detail)) detail = err.detail[0]?.msg ?? detail
    } catch {
      /* 본문 없음 */
    }
    throw new ApiError(res.status, detail)
  }

  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}
