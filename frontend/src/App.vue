<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { demoApi } from '@/api/demo'
import { useCoinStream } from '@/composables/useCoinStream'

const ready = ref(false)
const minionId = ref<number>(0)
const groupId = ref<number>(0)

const { balance, connected, lastReason, lastDelta, connect } = useCoinStream()

// 대장 입력
const amount = ref<number>(100)
const reason = ref<string>('숙제 완료')
const granting = ref(false)

const presets = [10, 50, 100, 500]

// 화면에 표시되는(카운트업 중인) 숫자 — 실제 balance와 분리
const display = ref<number>(0)
const coinPop = ref(false) // 코인 튕김 애니메이션
const bursts = ref<{ id: number; delta: number; reason: string | null }[]>([]) // 떠오르는 +N
let burstSeq = 0
let initialized = false

const reduceMotion =
  typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

let raf = 0
function animateTo(to: number) {
  if (reduceMotion) {
    display.value = to
    return
  }
  cancelAnimationFrame(raf)
  const from = display.value
  const dur = 680
  const start = performance.now()
  const ease = (t: number) => 1 - Math.pow(1 - t, 3)
  const step = (now: number) => {
    const t = Math.min(1, (now - start) / dur)
    display.value = Math.round(from + (to - from) * ease(t))
    if (t < 1) raf = requestAnimationFrame(step)
    else display.value = to
  }
  raf = requestAnimationFrame(step)
}

onMounted(async () => {
  const seed = await demoApi.seed()
  minionId.value = seed.minion_id
  groupId.value = seed.group_id
  balance.value = seed.minion_balance
  display.value = seed.minion_balance // 첫 값은 애니메이션 없이
  initialized = true
  connect(seed.minion_id, seed.group_id, 'minion')
  ready.value = true
})

// 잔액이 바뀌면: 카운트업 + 코인 튕김 + 보상 버스트
watch(balance, (next, prev) => {
  if (!initialized) return
  animateTo(next)

  if (next > prev) {
    coinPop.value = false
    requestAnimationFrame(() => (coinPop.value = true))
    setTimeout(() => (coinPop.value = false), 700)

    const id = ++burstSeq
    bursts.value.push({ id, delta: lastDelta.value ?? next - prev, reason: lastReason.value })
    setTimeout(() => {
      bursts.value = bursts.value.filter((b) => b.id !== id)
    }, 1400)
  }
})

async function grant() {
  if (amount.value <= 0) return
  granting.value = true
  try {
    // 지급 응답의 잔액을 직접 쓰지 않는다.
    // SSE로 도착하는 coin.updated가 쫄병 화면을 갱신 → 실시간 검증
    await demoApi.grant(minionId.value, amount.value, reason.value || null)
  } finally {
    granting.value = false
  }
}
</script>

<template>
  <div class="page">
    <header class="topbar">
      <div class="brand">
        <span class="brand__mark">🪙</span>
        <span class="brand__name">쫄병코인</span>
      </div>
      <span class="live" :class="{ 'live--on': connected }">
        <span class="live__dot" />
        {{ connected ? '실시간 연결됨' : '연결 중…' }}
      </span>
    </header>

    <p v-if="!ready" class="loading">코인 지갑을 여는 중…</p>

    <main v-else class="stack">
      <!-- 쫄병 화면: 보상의 순간 -->
      <section class="hero">
        <span class="hero__eyebrow">쫄병 화면 · 내 지갑</span>

        <div class="coin-stage">
          <div class="coin" :class="{ 'coin--pop': coinPop }">
            <span class="coin__shine" aria-hidden="true" />
            <span class="coin__stamp">쫄</span>
          </div>

          <!-- 지급 시 떠오르는 +N -->
          <transition-group name="burst" tag="div" class="burst-layer">
            <span v-for="b in bursts" :key="b.id" class="burst">+{{ b.delta.toLocaleString() }}</span>
          </transition-group>
        </div>

        <div class="balance">
          <span class="balance__num">{{ display.toLocaleString() }}</span>
          <span class="balance__unit">코인</span>
        </div>

        <p v-if="lastDelta" class="hero__last">
          방금 <b>+{{ lastDelta.toLocaleString() }}</b>
          <template v-if="lastReason"> · {{ lastReason }}</template>
        </p>
        <p class="hero__hint">대장이 칭찬하면 새로고침 없이 바로 쌓여요.</p>
      </section>

      <!-- 대장 화면: 지급 -->
      <section class="card">
        <div class="card__head">
          <span class="card__eyebrow">대장 화면</span>
          <h2 class="card__title">코인 지급하기</h2>
        </div>

        <label class="field-label" for="amount">지급할 코인</label>
        <div class="amount">
          <span class="amount__unit">🪙</span>
          <input id="amount" v-model.number="amount" type="number" min="1" inputmode="numeric" />
        </div>

        <div class="presets">
          <button
            v-for="p in presets"
            :key="p"
            type="button"
            class="preset"
            :class="{ 'preset--active': amount === p }"
            @click="amount = p"
          >
            +{{ p }}
          </button>
        </div>

        <label class="field-label" for="reason">사유 <span class="opt">(선택)</span></label>
        <input id="reason" v-model="reason" class="text-input" type="text" placeholder="예: 숙제 완료" />

        <button class="grant" :disabled="granting || amount <= 0" @click="grant">
          <span v-if="granting">지급하는 중…</span>
          <span v-else>🪙 {{ amount.toLocaleString() }} 코인 칭찬하기</span>
        </button>
      </section>

      <p class="footnote">
        지급은 <b>대장 화면</b>에서, 반영은 <b>쫄병 화면</b>에서 실시간으로 일어나요.
      </p>
    </main>
  </div>
</template>

<style scoped>
.page {
  position: relative;
  max-width: 30rem;
  min-height: 100vh;
  margin: 0 auto;
  padding: 22px 18px 40px;
}

/* ── 상단바 ── */
.topbar {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 7px;
}
.brand__mark {
  font-size: 22px;
}
.brand__name {
  font-family: var(--font-display);
  font-size: 22px;
  color: var(--ink);
  letter-spacing: -0.01em;
}
.live {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 11px;
  border-radius: 999px;
  background: var(--paper);
  border: 1px solid var(--line-strong);
  color: var(--ink-soft);
  font-size: 12px;
  font-weight: 600;
}
.live__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #c3cad6;
}
.live--on {
  color: #0f8f52;
  background: rgba(35, 194, 116, 0.16);
}
.live--on .live__dot {
  background: var(--mint);
  box-shadow: 0 0 0 0 rgba(35, 194, 116, 0.5);
  animation: pulse 1.8s ease-out infinite;
}
@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(35, 194, 116, 0.5);
  }
  100% {
    box-shadow: 0 0 0 8px rgba(35, 194, 116, 0);
  }
}

.loading {
  position: relative;
  z-index: 1;
  margin-top: 40px;
  text-align: center;
  color: var(--ink-soft);
  font-size: 15px;
}

.stack {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── 히어로: 보상의 순간 ── */
.hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px 22px 26px;
  border-radius: 24px;
  background: var(--paper);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--line);
}
.hero__eyebrow {
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--ink-faint);
  text-transform: uppercase;
}

.coin-stage {
  position: relative;
  margin: 16px 0 8px;
}

/* 시그니처: 촉각적인 황금 코인 */
.coin {
  position: relative;
  width: 138px;
  height: 138px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at 34% 28%, var(--gold-hi) 0%, var(--gold) 42%, var(--gold-deep) 82%);
  box-shadow:
    inset 0 5px 10px rgba(255, 255, 255, 0.75),
    inset 0 -9px 16px rgba(150, 85, 10, 0.5),
    0 16px 26px -10px rgba(184, 111, 22, 0.65);
  border: 5px solid var(--gold-edge);
  animation: coin-idle 4.5s ease-in-out infinite;
}
.coin::before {
  /* 코인 안쪽 테두리(음각) */
  content: '';
  position: absolute;
  inset: 12px;
  border-radius: 50%;
  border: 3px dashed rgba(150, 85, 10, 0.35);
}
.coin__shine {
  position: absolute;
  top: 16px;
  left: 24px;
  width: 40px;
  height: 22px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.75);
  filter: blur(2px);
  transform: rotate(-24deg);
}
.coin__stamp {
  font-family: var(--font-display);
  font-size: 58px;
  color: #7a4a10;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.5);
}
@keyframes coin-idle {
  0%,
  100% {
    transform: translateY(0) rotate(-3deg);
  }
  50% {
    transform: translateY(-6px) rotate(3deg);
  }
}
.coin--pop {
  animation: coin-pop 0.7s cubic-bezier(0.34, 1.56, 0.64, 1);
}
@keyframes coin-pop {
  0% {
    transform: scale(1) rotateY(0);
  }
  35% {
    transform: scale(1.18) rotateY(180deg);
  }
  70% {
    transform: scale(0.96) rotateY(360deg);
  }
  100% {
    transform: scale(1) rotateY(360deg);
  }
}

/* +N 버스트 */
.burst-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.burst {
  position: absolute;
  left: 50%;
  top: -6px;
  transform: translateX(-50%);
  font-family: var(--font-display);
  font-size: 30px;
  color: var(--coral);
  text-shadow: 0 2px 0 rgba(255, 255, 255, 0.7);
  white-space: nowrap;
}
.burst-enter-active {
  animation: burst-rise 1.4s ease-out forwards;
}
@keyframes burst-rise {
  0% {
    opacity: 0;
    transform: translate(-50%, 10px) scale(0.6);
  }
  20% {
    opacity: 1;
    transform: translate(-50%, -6px) scale(1.1);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -78px) scale(1);
  }
}

.balance {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-top: 6px;
}
.balance__num {
  font-family: var(--font-display);
  font-size: 60px;
  line-height: 1;
  color: var(--ink);
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}
.balance__unit {
  font-family: var(--font-display);
  font-size: 20px;
  color: var(--gold-deep);
}
.hero__last {
  margin: 10px 0 0;
  font-size: 14px;
  color: var(--ink-soft);
}
.hero__last b {
  color: var(--coral-deep);
}
.hero__hint {
  margin: 4px 0 0;
  font-size: 12.5px;
  color: #93a0b5;
}

/* ── 대장 지급 카드 ── */
.card {
  padding: 20px 18px 18px;
  border-radius: var(--radius);
  background: var(--paper);
  border: 1px solid var(--line);
  box-shadow: var(--shadow-card);
}
.card__head {
  margin-bottom: 14px;
}
.card__eyebrow {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(255, 107, 91, 0.12);
  color: var(--coral-deep);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.card__title {
  margin: 8px 0 0;
  font-family: var(--font-display);
  font-size: 24px;
  color: var(--ink);
  letter-spacing: -0.01em;
}

.field-label {
  display: block;
  margin: 0 0 6px;
  font-size: 13px;
  font-weight: 700;
  color: var(--ink-soft);
}
.opt {
  font-weight: 500;
  color: #a9b3c2;
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
.amount input {
  width: 100%;
  padding: 13px 14px 13px 44px;
  border: 2px solid var(--line);
  border-radius: 15px;
  background: #fff;
  color: var(--ink);
  font-family: var(--font-display);
  font-size: 24px;
  outline: none;
  transition: border-color 0.15s;
}
.amount input:focus {
  border-color: var(--gold);
}

.presets {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 16px;
}
.preset {
  padding: 10px 0;
  border: 2px solid var(--line);
  border-radius: 13px;
  background: #fff;
  color: var(--ink-soft);
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  transition:
    transform 0.12s,
    border-color 0.15s,
    background 0.15s,
    color 0.15s;
}
.preset:hover {
  border-color: var(--gold);
}
.preset:active {
  transform: scale(0.94);
}
.preset--active {
  background: var(--gold);
  border-color: var(--gold-deep);
  color: #6b4208;
}

.text-input {
  width: 100%;
  padding: 12px 14px;
  margin-bottom: 18px;
  border: 2px solid var(--line);
  border-radius: 15px;
  background: #fff;
  color: var(--ink);
  font-family: var(--font-body);
  font-size: 15px;
  outline: none;
  transition: border-color 0.15s;
}
.text-input::placeholder {
  color: #b6bfcc;
}
.text-input:focus {
  border-color: var(--gold);
}

.grant {
  width: 100%;
  padding: 15px;
  border: none;
  border-radius: 16px;
  background: var(--coral);
  color: #fff;
  font-family: var(--font-display);
  font-size: 18px;
  letter-spacing: 0.01em;
  cursor: pointer;
  box-shadow: 0 8px 18px -10px rgba(240, 79, 62, 0.65);
  transition:
    transform 0.12s,
    box-shadow 0.15s,
    filter 0.15s;
}
.grant:hover:not(:disabled) {
  filter: brightness(1.04);
}
.grant:active:not(:disabled) {
  transform: translateY(2px);
  box-shadow: 0 4px 10px -8px rgba(240, 79, 62, 0.7);
}
.grant:disabled {
  filter: grayscale(0.5);
  opacity: 0.6;
  cursor: not-allowed;
}

.footnote {
  margin: 2px 0 0;
  text-align: center;
  font-size: 12.5px;
  color: #7f8da3;
}
.footnote b {
  color: var(--ink-soft);
}

/* 접근성: 모션 최소화 */
@media (prefers-reduced-motion: reduce) {
  .coin,
  .floaty,
  .coin--pop,
  .live--on .live__dot {
    animation: none !important;
  }
  .burst-enter-active {
    animation-duration: 0.01ms;
  }
}

:focus-visible {
  outline: 3px solid var(--gold);
  outline-offset: 2px;
}
</style>
