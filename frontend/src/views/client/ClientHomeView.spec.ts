import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import ClientHomeView from './ClientHomeView.vue'
import ClientServiceView from './ClientServiceView.vue'

vi.mock('../../api/client', () => ({
  fetchPublicSlots: vi.fn(),
}))

import * as client from '../../api/client'

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'client-home', component: ClientHomeView },
      { path: '/book/service', name: 'book-service', component: ClientServiceView },
    ],
  })
}

describe('ClientHomeView', () => {
  beforeEach(() => {
    vi.mocked(client.fetchPublicSlots).mockReset()
    vi.useFakeTimers({ shouldAdvanceTime: true })
    vi.setSystemTime(new Date('2026-05-13T12:00:00'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders disabled state correctly when is_available is false', async () => {
    vi.mocked(client.fetchPublicSlots).mockResolvedValue([
      {
        id: 1,
        date: '2026-05-11',
        start_time: '09:00:00',
        end_time: '10:00:00',
        duration_minutes: 60,
        price: 40,
        is_available: false,
      },
    ])

    const router = makeRouter()
    router.push('/')
    await router.isReady()

    const wrapper = mount(ClientHomeView, {
      global: { plugins: [router] },
    })

    await flushPromises()

    const btn = wrapper.find('button.slot-card')
    expect(btn.exists()).toBe(true)
    expect(btn.attributes('aria-disabled')).toBe('true')
    expect(btn.classes()).toContain('disabled')
    expect(btn.attributes('disabled')).toBeDefined()
  })
})
