<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()

interface Tab {
  to: string
  label: string
  icon: string
}

const minionTabs: Tab[] = [
  { to: '/home', label: '홈', icon: '🏠' },
  { to: '/market', label: '대장마켓', icon: '🛍️' },
  { to: '/bitto', label: '빗토코인', icon: '📈' },
  { to: '/me', label: '내정보', icon: '👤' },
]

const bossTabs: Tab[] = [
  { to: '/boss', label: '홈', icon: '🏠' },
  { to: '/market', label: '대장마켓', icon: '🛍️' },
  { to: '/admin', label: '관리자', icon: '🛠️' },
  { to: '/me', label: '내정보', icon: '👤' },
]

const tabs = computed(() => (auth.isBoss ? bossTabs : minionTabs))

function isActive(to: string) {
  return route.path === to
}
</script>

<template>
  <div class="frame">
    <header class="topbar">
      <div class="brand">
        <span class="brand__mark">🪙</span>
        <span class="brand__name">쫄병코인</span>
      </div>
      <span class="role-chip" :class="auth.isBoss ? 'role-chip--boss' : 'role-chip--minion'">
        {{ auth.isBoss ? '대장' : '쫄병' }}
      </span>
    </header>

    <router-view />

    <nav class="tabbar">
      <div class="tabbar__inner">
        <router-link
          v-for="t in tabs"
          :key="t.to"
          :to="t.to"
          class="tab"
          :class="{ 'tab--active': isActive(t.to) }"
        >
          <span class="tab__icon">{{ t.icon }}</span>
          <span class="tab__label">{{ t.label }}</span>
        </router-link>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.frame {
  min-height: 100vh;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  max-width: 30rem;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  background: color-mix(in srgb, var(--bg) 82%, transparent);
  backdrop-filter: blur(8px);
}
.brand {
  display: flex;
  align-items: center;
  gap: 7px;
}
.brand__mark {
  font-size: 21px;
}
.brand__name {
  font-family: var(--font-display);
  font-size: 21px;
}
.role-chip {
  padding: 4px 12px;
  border-radius: 999px;
  font-family: var(--font-display);
  font-size: 13px;
}
.role-chip--boss {
  background: rgba(255, 107, 91, 0.12);
  color: var(--coral-deep);
}
.role-chip--minion {
  background: rgba(232, 149, 43, 0.15);
  color: var(--gold-edge);
}

/* 하단 탭바 */
.tabbar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  border-top: 1px solid var(--line);
  background: color-mix(in srgb, var(--paper) 92%, transparent);
  backdrop-filter: blur(10px);
}
.tabbar__inner {
  max-width: 30rem;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  padding: 6px 8px calc(6px + env(safe-area-inset-bottom));
}
.tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 7px 0;
  border-radius: 12px;
  text-decoration: none;
  color: var(--ink-faint);
  transition: color 0.15s;
}
.tab__icon {
  font-size: 21px;
  filter: grayscale(0.5);
  opacity: 0.7;
  transition:
    filter 0.15s,
    opacity 0.15s,
    transform 0.15s;
}
.tab__label {
  font-size: 11px;
  font-weight: 700;
}
.tab--active {
  color: var(--ink);
}
.tab--active .tab__icon {
  filter: none;
  opacity: 1;
  transform: translateY(-1px) scale(1.08);
}
</style>
