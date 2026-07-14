<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ApiError } from '@/lib/http'
import type { Role } from '@/api/auth'

const auth = useAuthStore()
const router = useRouter()

const role = ref<Role>('minion')
const error = ref('')
const busy = ref(false)

const form = reactive({
  email: '',
  username: '',
  password: '',
  // 대장
  group_name: '',
  // 쫄병
  invite_code: '',
  name: '',
  age: '' as number | '',
})

async function submit() {
  error.value = ''
  busy.value = true
  try {
    if (role.value === 'boss') {
      await auth.registerBoss({
        email: form.email.trim(),
        username: form.username.trim(),
        password: form.password,
        group_name: form.group_name.trim() || null,
      })
      router.replace('/boss')
    } else {
      await auth.registerMinion({
        email: form.email.trim(),
        username: form.username.trim(),
        password: form.password,
        invite_code: form.invite_code.trim().toUpperCase(),
        name: form.name.trim(),
        age: form.age === '' ? null : Number(form.age),
      })
      router.replace('/home')
    }
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : '회원가입에 실패했어요.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="auth">
    <h1 class="auth__brand">회원가입</h1>
    <p class="auth__tag">역할을 골라주세요.</p>

    <div class="role-switch">
      <button
        type="button"
        class="role-opt"
        :class="{ 'role-opt--on': role === 'minion' }"
        @click="role = 'minion'"
      >
        <span class="role-opt__emoji">🧒</span>
        <span class="role-opt__name">쫄병</span>
        <span class="role-opt__desc">코인 받고 쓰기</span>
      </button>
      <button
        type="button"
        class="role-opt"
        :class="{ 'role-opt--on': role === 'boss' }"
        @click="role = 'boss'"
      >
        <span class="role-opt__emoji">👑</span>
        <span class="role-opt__name">대장</span>
        <span class="role-opt__desc">그룹 만들고 지급</span>
      </button>
    </div>

    <form class="jc-card auth__form" @submit.prevent="submit">
      <label class="jc-label" for="username">이름(닉네임)</label>
      <input id="username" v-model="form.username" class="jc-input" placeholder="화면에 표시될 이름" required />

      <label class="jc-label" for="email">이메일</label>
      <input id="email" v-model="form.email" class="jc-input" type="email" placeholder="you@example.com" required />

      <label class="jc-label" for="pw">비밀번호 <span class="opt">(6자 이상)</span></label>
      <input id="pw" v-model="form.password" class="jc-input" type="password" placeholder="비밀번호" minlength="6" required />

      <!-- 대장 전용 -->
      <template v-if="role === 'boss'">
        <label class="jc-label" for="gname">그룹 이름 <span class="opt">(선택)</span></label>
        <input id="gname" v-model="form.group_name" class="jc-input" placeholder="예: 우리집, 3팀" />
      </template>

      <!-- 쫄병 전용 -->
      <template v-else>
        <label class="jc-label" for="invite">초대 코드</label>
        <input
          id="invite"
          v-model="form.invite_code"
          class="jc-input invite-input"
          placeholder="대장에게 받은 6자리"
          maxlength="12"
          required
        />
        <label class="jc-label" for="name">실명</label>
        <input id="name" v-model="form.name" class="jc-input" placeholder="이름" required />
        <label class="jc-label" for="age">나이 <span class="opt">(선택)</span></label>
        <input id="age" v-model="form.age" class="jc-input" type="number" min="0" placeholder="나이" />
      </template>

      <p v-if="error" class="jc-error">{{ error }}</p>

      <button class="jc-btn jc-btn--primary auth__submit" type="submit" :disabled="busy">
        {{ busy ? '가입 중…' : role === 'boss' ? '대장으로 시작하기' : '쫄병으로 가입하기' }}
      </button>
    </form>

    <p class="auth__switch">
      이미 계정이 있나요?
      <router-link to="/login" class="auth__link">로그인</router-link>
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
  padding: 32px 20px 40px;
}
.auth__brand {
  font-family: var(--font-display);
  font-size: 27px;
  margin: 0;
  text-align: center;
}
.auth__tag {
  margin: 4px 0 18px;
  color: var(--ink-soft);
  font-size: 14px;
  text-align: center;
}

.role-switch {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 16px;
}
.role-opt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 16px 8px;
  border: 2px solid var(--line);
  border-radius: 18px;
  background: var(--paper);
  cursor: pointer;
  transition:
    border-color 0.15s,
    transform 0.12s,
    box-shadow 0.15s;
}
.role-opt:active {
  transform: scale(0.97);
}
.role-opt__emoji {
  font-size: 30px;
}
.role-opt__name {
  font-family: var(--font-display);
  font-size: 17px;
  color: var(--ink);
}
.role-opt__desc {
  font-size: 11.5px;
  color: var(--ink-faint);
}
.role-opt--on {
  border-color: var(--gold);
  box-shadow: 0 8px 20px -14px rgba(232, 149, 43, 0.9);
}

.auth__form .jc-label:not(:first-child) {
  margin-top: 13px;
}
.invite-input {
  font-family: var(--font-display);
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
.auth__submit {
  margin-top: 20px;
}
.auth__switch {
  margin-top: 18px;
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
