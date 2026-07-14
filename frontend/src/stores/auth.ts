import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  authApi,
  type AuthResult,
  type BossRegisterInput,
  type Me,
  type MinionRegisterInput,
} from '@/api/auth'
import { tokens } from '@/lib/http'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<Me | null>(null)
  const ready = ref(false) // 초기 세션 복구 완료 여부

  const isAuthed = computed(() => user.value !== null)
  const isBoss = computed(() => user.value?.role === 'boss')
  const isMinion = computed(() => user.value?.role === 'minion')
  const isActive = computed(() => user.value?.status === 'active')

  function apply(result: AuthResult) {
    tokens.set(result.tokens.access_token, result.tokens.refresh_token)
    user.value = result.user
  }

  /** 저장된 토큰으로 세션 복구. 앱 시작 시 1회 호출. */
  async function init() {
    if (tokens.access) {
      try {
        user.value = await authApi.me()
      } catch {
        tokens.clear()
        user.value = null
      }
    }
    ready.value = true
  }

  async function login(email: string, password: string) {
    apply(await authApi.login(email, password))
  }

  async function registerBoss(data: BossRegisterInput) {
    apply(await authApi.registerBoss(data))
  }

  async function registerMinion(data: MinionRegisterInput) {
    apply(await authApi.registerMinion(data))
  }

  /** 잔액/상태 등 최신화 (승인 반영 등). */
  async function refreshMe() {
    if (tokens.access) user.value = await authApi.me()
  }

  function logout() {
    tokens.clear()
    user.value = null
  }

  return {
    user,
    ready,
    isAuthed,
    isBoss,
    isMinion,
    isActive,
    init,
    login,
    registerBoss,
    registerMinion,
    refreshMe,
    logout,
  }
})
