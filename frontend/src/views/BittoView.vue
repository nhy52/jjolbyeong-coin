<script setup lang="ts"></script>

<template>
  <main class="jc-shell">
    <h1 class="jc-title page-title">빗토코인</h1>
    <section class="jc-card soon">
      <div class="soon__emoji">📈</div>
      <p class="soon__title">곧 열려요</p>
      <p class="soon__desc">
        5초마다 오르내리는 빗토코인에 코인을 투자하고<br />
        실시간 시세 차트로 손익을 확인할 수 있어요.
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
