<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { adminApi, type GroupSummary } from '@/api/admin'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const summary = ref<GroupSummary | null>(null)
const loading = ref(true)
const copied = ref(false)

async function load() {
  loading.value = true
  try {
    summary.value = await adminApi.summary()
  } finally {
    loading.value = false
  }
}

async function copyCode() {
  const code = summary.value?.invite_code
  if (!code) return
  try {
    await navigator.clipboard.writeText(code)
    copied.value = true
    setTimeout(() => (copied.value = false), 1600)
  } catch {
    /* 클립보드 미지원 시 무시 */
  }
}

onMounted(load)
</script>

<template>
  <main class="jc-shell">
    <p class="greet">
      <b>{{ auth.user?.username }}</b> 대장님, 반가워요 👑
    </p>

    <!-- 초대 코드 -->
    <section class="invite">
      <p class="invite__label">우리 그룹 초대 코드</p>
      <p class="invite__code">{{ summary?.invite_code ?? '·····' }}</p>
      <p class="invite__desc">쫄병에게 이 코드를 알려주면 우리 그룹으로 가입할 수 있어요.</p>
      <button class="jc-btn jc-btn--gold invite__copy" @click="copyCode">
        {{ copied ? '복사됨! ✓' : '초대 코드 복사' }}
      </button>
    </section>

    <!-- 그룹 현황 -->
    <section class="stats">
      <div class="stat">
        <span class="stat__num">{{ summary?.total_minions ?? 0 }}</span>
        <span class="stat__label">전체 쫄병</span>
      </div>
      <div class="stat">
        <span class="stat__num">{{ summary?.active_minions ?? 0 }}</span>
        <span class="stat__label">활동 중</span>
      </div>
      <div class="stat" :class="{ 'stat--alert': (summary?.pending_minions ?? 0) > 0 }">
        <span class="stat__num">{{ summary?.pending_minions ?? 0 }}</span>
        <span class="stat__label">승인 대기</span>
      </div>
    </section>

    <button
      v-if="(summary?.pending_minions ?? 0) > 0"
      class="jc-btn jc-btn--primary"
      @click="router.push('/admin')"
    >
      승인 대기 {{ summary?.pending_minions }}명 확인하기 →
    </button>

    <section class="jc-card actions">
      <p class="actions__title">관리</p>
      <button class="action" @click="router.push('/admin')">
        <span class="action__icon">🛠️</span>
        <span class="action__text">
          <b>관리자 페이지</b>
          <small>쫄병 승인 · 코인 지급</small>
        </span>
        <span class="action__arrow">›</span>
      </button>
      <button class="action" @click="router.push('/market')">
        <span class="action__icon">🛍️</span>
        <span class="action__text">
          <b>대장마켓</b>
          <small>상품 등록 (준비 중)</small>
        </span>
        <span class="action__arrow">›</span>
      </button>
    </section>
  </main>
</template>

<style scoped>
.greet {
  margin: 4px 0 16px;
  font-size: 16px;
  color: var(--ink-soft);
}
.greet b {
  color: var(--ink);
  font-family: var(--font-display);
}

.invite {
  text-align: center;
  padding: 22px 20px;
  border-radius: 24px;
  background: linear-gradient(180deg, #fff6e2 0%, #fffdf7 100%);
  border: 1px solid #f5e4c0;
  box-shadow: var(--shadow-card);
  margin-bottom: 14px;
}
.invite__label {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--gold-edge);
  letter-spacing: 0.04em;
}
.invite__code {
  margin: 6px 0 4px;
  font-family: var(--font-display);
  font-size: 44px;
  letter-spacing: 0.22em;
  color: var(--ink);
  text-indent: 0.22em;
}
.invite__desc {
  margin: 0 0 16px;
  font-size: 13px;
  color: var(--ink-soft);
}
.invite__copy {
  max-width: 240px;
  margin: 0 auto;
}

.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 14px;
}
.stat {
  padding: 16px 8px;
  text-align: center;
  border-radius: 16px;
  background: var(--paper);
  border: 1px solid var(--line);
}
.stat__num {
  display: block;
  font-family: var(--font-display);
  font-size: 28px;
  color: var(--ink);
}
.stat__label {
  font-size: 12px;
  color: var(--ink-soft);
}
.stat--alert {
  border-color: #ffd2cb;
  background: #fff4f2;
}
.stat--alert .stat__num {
  color: var(--coral-deep);
}

.actions {
  margin-top: 14px;
  padding: 12px;
}
.actions__title {
  margin: 6px 8px 8px;
  font-size: 13px;
  font-weight: 700;
  color: var(--ink-soft);
}
.action {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: none;
  background: transparent;
  border-radius: 14px;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
}
.action:hover {
  background: #f7f8fa;
}
.action__icon {
  font-size: 24px;
}
.action__text {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.action__text b {
  font-size: 15px;
  color: var(--ink);
}
.action__text small {
  font-size: 12px;
  color: var(--ink-faint);
}
.action__arrow {
  font-size: 22px;
  color: var(--ink-faint);
}
</style>
