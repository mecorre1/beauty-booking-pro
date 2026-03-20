import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)
app.use(router)

if (import.meta.env.DEV) {
  app.config.errorHandler = (err, instance, info) => {
    console.error('[Vue error]', err, info, instance)
  }
}

void router.isReady().then(() => {
  app.mount('#app')
})
