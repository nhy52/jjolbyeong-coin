<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { adminApi, type MinionSummary } from '@/api/admin'
import { ApiError } from '@/lib/http'

const minions = ref<MinionSummary[]>([])
const loading = ref(true)
const busyId = ref<number | null>(null)

const pending = computed(() => minions.value.filter((m) => m.status === 'pending'))
const active = computed(() => minions.value.filter((m) => m.status === 'active'))

// 지급 패널 상태
const grantTarget = ref<MinionSummary | null>(null)
const amount = ref<number>(100)
const reason = ref('')
const granting = ref(false)
const grantError = ref('')
const presets = [10, 50, 100, 500]

async function load() {
  loading.value = true
  try {
    minions.value = await adminApi.minions()
  } finally {
    loading.value = false
  }
}

async function approve(m: MinionSummary) {
  busyId.value = m.id
  try {
    const updated = await adminApi.approve(m.id)
    m.status = updated.status
  } finally {
    busyId.value = null
  }
}

async function reject(m: MinionSummary) {
  busyId.value = m.id
  try {
    await adminApi.reject(m.id)
    minions.value = minions.value.filter((x) => x.id !== m.id)
  } finally {
    busyId.value = null
  }
}

function openGrant(m: MinionSummary) {
  grantTarget.value = m
  amount.value = 100
  reason.value = ''
  grantError.value = ''
}

function closeGrant() {
  grantTarget.value = null
}

async function submitGrant() {
  if (!grantTarget.value || amount.value <= 0) return
  granting.value = true
  grantError.value = ''
  try {
    const res = await adminApi.grant(grantTarget.value.id, amount.value, reason.value || null)
    const row = minions.value.find((x) => x.id === grantTarget.value!.id)
    if (row) row.balance = res.balance
    closeGrant()
  } catch (e) {
    grantError.value = e instanceof ApiError ? e.message : '지급에 실패했어요.'
  } finally {
    granting.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="jc-shell">
    <h1 class="jc-title page-title">관리자</h1>

    <p v-if="loading" class="jc-muted center">불러오는 중…</p>

    <template v-else>
      <!-- 승인 대기 -->
      <section class="block">
        <div class="block__head">
          <h2 class="block__title">승인 대기</h2>
          <span v-if="pending.length" class="badge">{{ pending.length }}</span>
        </div>
        <p v-if="!pending.length" class="empty">대기 중인 쫄병이 없어요.</p>
        <div v-for="m in pending" :key="m.id" class="row row--pending">
          <div class="row__info">
            <b class="row__name">{{ m.name || m.username }}</b>
            <small class="row__sub">@{{ m.username }}</small>
          </div>
          <div class="row__actions">
            <button class="mini mini--ghost" :disabled="busyId === m.id" @click="reject(m)">거절</button>
            <button class="mini mini--approve" :disabled="busyId === m.id" @click="approve(m)">승인</button>
          </div>
        </div>
      </section>

      <!-- 활동 중 쫄병 -->
      <section class="block">
        <div class="block__head">
          <h2 class="block__title">쫄병 ({{ active.length }})</h2>
        </div>
        <p v-if="!active.length" class="empty">아직 활동 중인 쫄병이 없어요.</p>
        <div v-for="m in active" :key="m.id" class="row">
          <div class="row__info">
            <b class="row__name">{{ m.name || m.username }}</b>
            <small class="row__sub">🪙 {{ m.balance.toLocaleString() }} 코인</small>
          </div>
          <button class="mini mini--grant" @click="openGrant(m)">지급</button>
        </div>
      </section>
    </template>

    <!-- 코인 지급 바텀시트 -->
    <transition name="sheet">
      <div v-if="grantTarget" class="sheet-wrap" @click.self="closeGrant">
        <div class="sheet">
          <div class="sheet__grab" />
          <p class="sheet__title">
            <b>{{ grantTarget.name || grantTarget.username }}</b> 에게 코인 지급
          </p>

          <label class="jc-label">지급할 코인</label>
          <div class="amount">
            <span class="amount__unit">🪙</span>
            <input v-model.number="amount" class="amount__input" type="number" min="1" inputmode="numeric" />
          </div>
          <div class="presets">
            <button
              v-for="p in presets"
              :key="p"
              class="preset"
              :class="{ 'preset--on': amount === p }"
              @click="amount = p"
            >
              +{{ p }}
            </button>
          </div>

          <label class="jc-label">사유 <span class="opt">(선택)</span></label>
          <input v-model="reason" class="jc-input" placeholder="예: 숙제 완료" />

          <p v-if="grantError" class="jc-error">{{ grantError }}</p>

          <button class="jc-btn jc-btn--primary sheet__submit" :disabled="granting || amount <= 0" @click="submitGrant">
            {{ granting ? '지급 중…' : `🪙 ${amount.toLocaleString()} 코인 칭찬하기` }}
          </button>
          <button class="jc-btn jc-btn--ghost" @click="closeGrant">취소</button>
        </div>
      </div>
    </transition>
  </main>
</template>

<style scoped>
.page-title {
  font-size: 26px;
  margin: 4px 0 18px;
}
.center {
  text-align: center;
  margin-top: 30px;
}

.block {
  margin-bottom: 22px;
}
.block__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.block__title {
  font-family: var(--font-display);
  font-size: 17px;
  margin: 0;
  color: var(--ink);
}
.badge {
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: var(--coral);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
}
.empty {
  padding: 18px;
  text-align: center;
  font-size: 13.5px;
  color: var(--ink-faint);
  background: var(--paper);
  border: 1px dashed var(--line-strong);
  border-radius: 14px;
}

.row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 14px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 14px;
  margin-bottom: 8px;
}
.row--pending {
  border-color: #ffe0d9;
  background: #fff8f6;
}
.row__info {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.row__name {
  font-size: 15px;
  color: var(--ink);
}
.row__sub {
  font-size: 12.5px;
  color: var(--ink-faint);
}
.row__actions {
  display: flex;
  gap: 6px;
}
.mini {
  padding: 8px 14px;
  border-radius: 11px;
  border: none;
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  transition:
    filter 0.15s,
    transform 0.1s;
}
.mini:active {
  transform: scale(0.95);
}
.mini:disabled {
  opacity: 0.5;
}
.mini--approve {
  background: var(--mint);
  color: #fff;
}
.mini--grant {
  background: var(--gold);
  color: #6b4208;
}
.mini--ghost {
  background: #fff;
  border: 1.5px solid var(--line-strong);
  color: var(--ink-soft);
}

/* 바텀시트 */
.sheet-wrap {
  position: fixed;
  inset: 0;
  z-index: 40;
  background: rgba(22, 32, 46, 0.4);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.sheet {
  width: 100%;
  max-width: 30rem;
  background: var(--paper);
  border-radius: 26px 26px 0 0;
  padding: 10px 20px calc(24px + env(safe-area-inset-bottom));
  box-shadow: 0 -12px 40px -12px rgba(22, 32, 46, 0.4);
}
.sheet__grab {
  width: 40px;
  height: 4px;
  border-radius: 999px;
  background: var(--line-strong);
  margin: 4px auto 14px;
}
.sheet__title {
  margin: 0 0 16px;
  font-size: 15px;
  color: var(--ink-soft);
}
.sheet__title b {
  font-family: var(--font-display);
  color: var(--ink);
  font-size: 17px;
}
.amount {
  position: relative;
  margin-bottom: 10px;
}
.amount__unit {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
}
.amount__input {
  width: 100%;
  padding: 13px 14px 13px 44px;
  border: 2px solid var(--line);
  border-radius: 14px;
  background: #fff;
  color: var(--ink);
  font-family: var(--font-display);
  font-size: 24px;
  outline: none;
  transition: border-color 0.15s;
}
.amount__input:focus {
  border-color: var(--gold);
}
.presets {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 14px;
}
.preset {
  padding: 10px 0;
  border: 2px solid var(--line);
  border-radius: 12px;
  background: #fff;
  color: var(--ink-soft);
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  transition:
    border-color 0.15s,
    background 0.15s;
}
.preset--on {
  background: var(--gold);
  border-color: var(--gold-deep);
  color: #6b4208;
}
.sheet__submit {
  margin: 6px 0 8px;
}

.sheet-enter-active,
.sheet-leave-active {
  transition: opacity 0.2s ease;
}
.sheet-enter-active .sheet,
.sheet-leave-active .sheet {
  transition: transform 0.24s cubic-bezier(0.32, 0.72, 0, 1);
}
.sheet-enter-from,
.sheet-leave-to {
  opacity: 0;
}
.sheet-enter-from .sheet,
.sheet-leave-to .sheet {
  transform: translateY(100%);
}
</style>
