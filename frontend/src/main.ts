import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
import { router } from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
app.use(createPinia())

// 저장된 토큰으로 세션을 먼저 복구한 뒤 라우터/앱을 마운트한다.
const auth = useAuthStore()
auth.init().finally(() => {
  app.use(router)
  app.mount('#app')
})
