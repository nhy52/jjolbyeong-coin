<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ApiError } from '@/lib/http'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await auth.login(email.value.trim(), password.value)
    router.replace(auth.isBoss ? '/boss' : '/home')
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : '로그인에 실패했어요. 다시 시도해 주세요.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="auth">
    <div class="auth__hero">
      <div class="coin-mini">🪙</div>
      <h1 class="auth__brand">쫄병코인</h1>
      <p class="auth__tag">칭찬이 코인으로 쌓이는 곳</p>
    </div>

    <form class="jc-card auth__form" @submit.prevent="submit">
      <label class="jc-label" for="email">이메일</label>
      <input
        id="email"
        v-model="email"
        class="jc-input"
        type="email"
        autocomplete="email"
        placeholder="you@example.com"
        required
      />

      <label class="jc-label" for="pw">비밀번호</label>
      <input
        id="pw"
        v-model="password"
        class="jc-input"
        type="password"
        autocomplete="current-password"
        placeholder="비밀번호"
        required
      />

      <p v-if="error" class="jc-error">{{ error }}</p>

      <button class="jc-btn jc-btn--primary auth__submit" type="submit" :disabled="busy">
        {{ busy ? '로그인 중…' : '로그인' }}
      </button>
    </form>

    <p class="auth__switch">
      아직 계정이 없나요?
      <router-link to="/register" class="auth__link">회원가입</router-link>
    </p>
  </div>
</template>

<style scoped>
.auth {
  max-width: 26rem;
  margin: 0 auto;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 24px 20px 40px;
}
.auth__hero {
  text-align: center;
  margin-bottom: 22px;
}
.coin-mini {
  width: 66px;
  height: 66px;
  margin: 0 auto 12px;
  display: grid;
  place-items: center;
  font-size: 34px;
  border-radius: 50%;
  background: radial-gradient(circle at 34% 28%, var(--gold-hi), var(--gold) 45%, var(--gold-deep) 85%);
  box-shadow:
    inset 0 3px 6px rgba(255, 255, 255, 0.7),
    inset 0 -6px 12px rgba(150, 85, 10, 0.4),
    0 12px 22px -12px rgba(184, 111, 22, 0.7);
}
.auth__brand {
  font-family: var(--font-display);
  font-size: 30px;
  margin: 0;
}
.auth__tag {
  margin: 4px 0 0;
  color: var(--ink-soft);
  font-size: 14px;
}
.auth__form .jc-label:not(:first-child) {
  margin-top: 14px;
}
.auth__submit {
  margin-top: 20px;
}
.auth__switch {
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
  color: var(--ink-soft);
}
.auth__link {
  color: var(--coral-deep);
  font-weight: 700;
  text-decoration: none;
}
</style>
