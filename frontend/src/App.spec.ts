import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'
import { createApp } from 'vue'

import './style.css'
import App from './App.vue'
import router from './router'

describe('App', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="app"></div>'
  })

  it('renders admin login at /admin/login', async () => {
    const app = createApp(App)
    app.use(router)
    await router.push('/admin/login')
    await router.isReady()
    app.mount('#app')
    await flushPromises()
    expect(document.body.textContent).toContain('Admin sign in')
  })
})
