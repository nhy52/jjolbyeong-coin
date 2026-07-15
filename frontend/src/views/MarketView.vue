<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import BossMarket from '@/views/boss/BossMarket.vue'
import MinionShop from '@/views/minion/MinionShop.vue'

const auth = useAuthStore()
</script>

<template>
  <BossMarket v-if="auth.isBoss" />
  <MinionShop v-else />
</template>
