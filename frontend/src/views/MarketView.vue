<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
</script>

<template>
  <main class="jc-shell">
    <h1 class="jc-title page-title">대장마켓</h1>
    <section class="jc-card soon">
      <div class="soon__emoji">🛍️</div>
      <p class="soon__title">곧 열려요</p>
      <p class="soon__desc">
        {{ auth.isBoss ? '여기서 상품을 등록하면 쫄병들이 코인으로 구매할 수 있어요.' : '대장이 등록한 상품을 코인으로 살 수 있어요.' }}
      </p>
    </section>
  </main>
</template>

<style scoped>
.page-title {
  font-size: 26px;
  margin: 4px 0 18px;
}
.soon {
  text-align: center;
  padding: 40px 24px;
  margin-top: 8px;
}
.soon__emoji {
  font-size: 46px;
}
.soon__title {
  font-family: var(--font-display);
  font-size: 20px;
  margin: 12px 0 6px;
  color: var(--ink);
}
.soon__desc {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--ink-soft);
}
</style>
