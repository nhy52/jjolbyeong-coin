<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const statusLabel: Record<string, string> = {
  active: '활동 중',
  pending: '승인 대기',
  suspended: '정지됨',
  left: '탈퇴',
}

function logout() {
  auth.logout()
  router.replace('/login')
}
</script>

<template>
  <main class="jc-shell">
    <h1 class="jc-title page-title">내정보</h1>

    <section class="profile">
      <div class="avatar">{{ auth.isBoss ? '👑' : '🧒' }}</div>
      <p class="profile__name">{{ auth.user?.username }}</p>
      <p class="profile__role">{{ auth.isBoss ? '대장' : '쫄병' }} · {{ statusLabel[auth.user?.status ?? ''] }}</p>
    </section>

    <section class="jc-card info">
      <div class="info__row">
        <span class="info__k">이메일</span>
        <span class="info__v">{{ auth.user?.email }}</span>
      </div>
      <div class="info__row">
        <span class="info__k">그룹</span>
        <span class="info__v">{{ auth.user?.group_name ?? '-' }}</span>
      </div>
      <div v-if="!auth.isBoss" class="info__row">
        <span class="info__k">내 코인</span>
        <span class="info__v gold">🪙 {{ (auth.user?.balance ?? 0).toLocaleString() }}</span>
      </div>
      <div v-if="auth.isBoss" class="info__row">
        <span class="info__k">초대 코드</span>
        <span class="info__v code">{{ auth.user?.invite_code }}</span>
      </div>
    </section>

    <button class="jc-btn jc-btn--ghost logout" @click="logout">로그아웃</button>
  </main>
</template>

<style scoped>
.page-title {
  font-size: 26px;
  margin: 4px 0 18px;
}
.profile {
  text-align: center;
  margin-bottom: 18px;
}
.avatar {
  width: 74px;
  height: 74px;
  margin: 0 auto 10px;
  display: grid;
  place-items: center;
  font-size: 38px;
  border-radius: 50%;
  background: var(--paper);
  border: 1px solid var(--line);
  box-shadow: var(--shadow-card);
}
.profile__name {
  margin: 0;
  font-family: var(--font-display);
  font-size: 22px;
  color: var(--ink);
}
.profile__role {
  margin: 2px 0 0;
  font-size: 13.5px;
  color: var(--ink-soft);
}

.info {
  padding: 6px 18px;
}
.info__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
}
.info__row:last-child {
  border-bottom: none;
}
.info__k {
  font-size: 13.5px;
  color: var(--ink-soft);
}
.info__v {
  font-size: 14.5px;
  color: var(--ink);
  font-weight: 600;
}
.info__v.gold {
  font-family: var(--font-display);
  color: var(--gold-deep);
}
.info__v.code {
  font-family: var(--font-display);
  letter-spacing: 0.14em;
}
.logout {
  margin-top: 18px;
}
</style>
