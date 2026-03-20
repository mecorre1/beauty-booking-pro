import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import { useBookingSelection } from '../../composables/useBookingSelection'
import type { PublicService } from '../../types'
import ClientConfirmView from './ClientConfirmView.vue'
import ClientHomeView from './ClientHomeView.vue'
import ClientServiceView from './ClientServiceView.vue'

vi.mock('../../api/client', () => ({
  fetchPublicServices: vi.fn(),
}))

import * as client from '../../api/client'

function catalog(): PublicService[] {
  return [
    { id: 1, type: 'haircut', gender: 'male', base_duration_minutes: 30 },
    { id: 2, type: 'haircut', gender: 'female', base_duration_minutes: 45 },
    { id: 3, type: 'haircut_hairdressing', gender: 'male', base_duration_minutes: 45 },
    { id: 4, type: 'haircut_hairdressing', gender: 'female', base_duration_minutes: 60 },
    { id: 5, type: 'color', gender: 'male', base_duration_minutes: 90 },
    { id: 6, type: 'color', gender: 'female', base_duration_minutes: 120 },
  ]
}

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'client-home', component: ClientHomeView },
      { path: '/book/service', name: 'book-service', component: ClientServiceView },
      { path: '/book/confirm', name: 'book-confirm', component: ClientConfirmView },
    ],
  })
}

describe('ClientServiceView', () => {
  const { setSelectedSlot, resetBookingSelection } = useBookingSelection()

  beforeEach(() => {
    vi.mocked(client.fetchPublicServices).mockReset()
    vi.mocked(client.fetchPublicServices).mockResolvedValue(catalog())
    resetBookingSelection()
  })

  afterEach(() => {
    resetBookingSelection()
  })

  it('redirects to home when no slot is selected', async () => {
    const router = makeRouter()
    await router.push('/book/service')
    await router.isReady()

    mount(ClientServiceView, { global: { plugins: [router] } })
    await flushPromises()

    expect(router.currentRoute.value.name).toBe('client-home')
    expect(router.currentRoute.value.path).toBe('/')
  })

  it('renders service, gender, and location choices after loading', async () => {
    setSelectedSlot({
      id: 1,
      date: '2026-05-11',
      start_time: '10:00:00',
      end_time: '11:00:00',
      duration_minutes: 60,
      price: 48,
      is_available: true,
    })

    const router = makeRouter()
    await router.push('/book/service')
    await router.isReady()

    const wrapper = mount(ClientServiceView, { global: { plugins: [router] } })
    await flushPromises()

    expect(wrapper.text()).toContain('Regular haircut')
    expect(wrapper.text()).toContain('Male')
    expect(wrapper.text()).toContain('At the salon')
  })

  it('keeps Continue disabled until type, gender, and location are valid for the slot', async () => {
    setSelectedSlot({
      id: 1,
      date: '2026-05-11',
      start_time: '10:00:00',
      end_time: '10:30:00',
      duration_minutes: 30,
      price: 40,
      is_available: true,
    })

    const router = makeRouter()
    await router.push('/book/service')
    await router.isReady()

    const wrapper = mount(ClientServiceView, { global: { plugins: [router] } })
    await flushPromises()

    const btn = wrapper.get('button.btn-primary')
    expect(btn.attributes('disabled')).toBeDefined()

    await wrapper.get('input[name="serviceType"][value="haircut"]').setValue()
    await wrapper.get('input[name="gender"][value="male"]').setValue()
    await wrapper.get('input[name="location"][value="salon"]').setValue()

    expect(btn.attributes('disabled')).toBeUndefined()
  })

  it('navigates to /book/confirm when Continue is submitted with a valid session', async () => {
    setSelectedSlot({
      id: 1,
      date: '2026-05-11',
      start_time: '10:00:00',
      end_time: '11:00:00',
      duration_minutes: 60,
      price: 48,
      is_available: true,
    })

    const router = makeRouter()
    await router.push('/book/service')
    await router.isReady()

    const wrapper = mount(ClientServiceView, { global: { plugins: [router] } })
    await flushPromises()

    await wrapper.get('input[name="serviceType"][value="haircut"]').setValue()
    await wrapper.get('input[name="gender"][value="female"]').setValue()
    await wrapper.get('input[name="location"][value="salon"]').setValue()

    await wrapper.get('form').trigger('submit.prevent')
    await flushPromises()

    expect(router.currentRoute.value.name).toBe('book-confirm')
    expect(router.currentRoute.value.path).toBe('/book/confirm')
  })
})
