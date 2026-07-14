<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCoinStream } from '@/composables/useCoinStream'

const auth = useAuthStore()
const { balance, connected, lastReason, lastDelta, approved, connect } = useCoinStream()

const display = ref(0)
const coinPop = ref(false)
const bursts = ref<{ id: number; delta: number }[]>([])
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

onMounted(() => {
  balance.value = auth.user?.balance ?? 0
  display.value = balance.value
  initialized = true
  if (auth.isActive) connect()
})

watch(balance, (next, prev) => {
  if (!initialized) return
  animateTo(next)
  if (next > prev) {
    coinPop.value = false
    requestAnimationFrame(() => (coinPop.value = true))
    setTimeout(() => (coinPop.value = false), 700)
    const id = ++burstSeq
    bursts.value.push({ id, delta: lastDelta.value ?? next - prev })
    setTimeout(() => (bursts.value = bursts.value.filter((b) => b.id !== id)), 1400)
  }
})

// 승인 이벤트가 오면 내 정보를 갱신하고 스트림 재연결
watch(approved, async (v) => {
  if (v) {
    await auth.refreshMe()
    connect()
  }
})
</script>

<template>
  <main class="jc-shell">
    <!-- 승인 대기 상태 -->
    <section v-if="!auth.isActive" class="jc-card pending">
      <div class="pending__emoji">⏳</div>
      <h2 class="jc-title pending__title">승인 대기 중이에요</h2>
      <p class="pending__desc">
        대장이 가입을 승인하면 코인 지갑이 열려요.<br />
        조금만 기다려 주세요.
      </p>
      <p class="pending__hint">승인되면 이 화면이 자동으로 바뀝니다.</p>
    </section>

    <!-- 코인 지갑 -->
    <template v-else>
      <section class="hero">
        <div class="hero__top">
          <span class="hero__eyebrow">내 지갑</span>
          <span class="live" :class="{ 'live--on': connected }">
            <span class="live__dot" />{{ connected ? '실시간' : '연결 중' }}
          </span>
        </div>

        <div class="coin-stage">
          <div class="coin" :class="{ 'coin--pop': coinPop }">
            <span class="coin__shine" aria-hidden="true" />
            <span class="coin__stamp">쫄</span>
          </div>
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

      <section class="jc-card next">
        <p class="next__title">이 코인으로 할 수 있어요</p>
        <div class="next__row">
          <router-link to="/market" class="next__item">
            <span class="next__icon">🛍️</span><span>대장마켓</span>
          </router-link>
          <router-link to="/bitto" class="next__item">
            <span class="next__icon">📈</span><span>빗토코인</span>
          </router-link>
        </div>
      </section>
    </template>
  </main>
</template>

<style scoped>
/* 승인 대기 */
.pending {
  text-align: center;
  margin-top: 32px;
  padding: 36px 22px;
}
.pending__emoji {
  font-size: 46px;
}
.pending__title {
  font-size: 22px;
  margin: 12px 0 8px;
}
.pending__desc {
  color: var(--ink-soft);
  font-size: 14.5px;
  line-height: 1.6;
  margin: 0;
}
.pending__hint {
  margin: 16px 0 0;
  font-size: 12.5px;
  color: var(--ink-faint);
}

/* 코인 히어로 */
.hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 22px 22px 26px;
  border-radius: 24px;
  background: var(--paper);
  border: 1px solid var(--line);
  box-shadow: var(--shadow-card);
  margin-bottom: 14px;
}
.hero__top {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.hero__eyebrow {
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--ink-faint);
  text-transform: uppercase;
}
.live {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 999px;
  background: #f1f3f6;
  color: var(--ink-faint);
  font-size: 11px;
  font-weight: 700;
}
.live__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #c3cad6;
}
.live--on {
  background: rgba(35, 194, 116, 0.14);
  color: #0f8f52;
}
.live--on .live__dot {
  background: var(--mint);
}

.coin-stage {
  position: relative;
  margin: 14px 0 6px;
}
.coin {
  position: relative;
  width: 132px;
  height: 132px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: radial-gradient(circle at 34% 28%, var(--gold-hi) 0%, var(--gold) 42%, var(--gold-deep) 82%);
  box-shadow:
    inset 0 5px 10px rgba(255, 255, 255, 0.75),
    inset 0 -9px 16px rgba(150, 85, 10, 0.5),
    0 16px 26px -12px rgba(184, 111, 22, 0.6);
  border: 5px solid var(--gold-edge);
  animation: coin-idle 4.5s ease-in-out infinite;
}
.coin::before {
  content: '';
  position: absolute;
  inset: 11px;
  border-radius: 50%;
  border: 3px dashed rgba(150, 85, 10, 0.35);
}
.coin__shine {
  position: absolute;
  top: 16px;
  left: 22px;
  width: 38px;
  height: 20px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.75);
  filter: blur(2px);
  transform: rotate(-24deg);
}
.coin__stamp {
  font-family: var(--font-display);
  font-size: 56px;
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
  margin-top: 4px;
}
.balance__num {
  font-family: var(--font-display);
  font-size: 58px;
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
  color: var(--ink-faint);
}

/* 안내 카드 */
.next__title {
  margin: 0 0 12px;
  font-size: 13px;
  font-weight: 700;
  color: var(--ink-soft);
}
.next__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.next__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  padding: 16px 8px;
  border-radius: 15px;
  background: #f7f8fa;
  text-decoration: none;
  color: var(--ink);
  font-weight: 700;
  font-size: 14px;
  transition: background 0.15s;
}
.next__item:hover {
  background: #eef1f5;
}
.next__icon {
  font-size: 26px;
}
</style>
