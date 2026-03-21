import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { token: 'magic-token' } }),
  useRouter: () => ({ push }),
}))

vi.mock('../../api/client', () => ({
  getBookingByToken: vi.fn(() =>
    Promise.resolve({
      id: 1,
      slot_id: 9,
      service_id: 1,
      location: 'salon',
      home_address: null,
      client_name: 'Ada',
      client_email: 'ada@test.com',
      client_phone: '555',
      marketing_opt_in: false,
      client_note: null,
      current_hairstyle_media_id: null,
      inspiration_media_id: null,
      status: 'confirmed',
      price_at_booking: '40',
      salon_address_at_booking: 'Salon',
      edit_token: 'magic-token',
    }),
  ),
  fetchPublicServices: vi.fn(() =>
    Promise.resolve([{ id: 1, type: 'haircut' as const, gender: 'male' as const, base_duration_minutes: 30 }]),
  ),
  updateBookingByToken: vi.fn(() => Promise.resolve({})),
  cancelBookingByToken: vi.fn(() => Promise.resolve()),
}))

import * as clientApi from '../../api/client'
import ClientEditView from './ClientEditView.vue'

describe('ClientEditView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('confirm', vi.fn(() => true))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('loads booking and submits update', async () => {
    const wrapper = mount(ClientEditView)
    await flushPromises()
    await nextTick()
    expect(clientApi.getBookingByToken).toHaveBeenCalledWith('magic-token')
    const nameField = wrapper.findAll('input').find((w) => (w.element as HTMLInputElement).value === 'Ada')
    expect(nameField).toBeTruthy()

    await wrapper.get('form').trigger('submit.prevent')
    await flushPromises()
    expect(clientApi.updateBookingByToken).toHaveBeenCalled()
    expect(push).toHaveBeenCalledWith({ name: 'client-home' })
  })

  it('confirm cancel calls API', async () => {
    const wrapper = mount(ClientEditView)
    await flushPromises()
    await wrapper.get('button.danger').trigger('click')
    await flushPromises()
    expect(clientApi.cancelBookingByToken).toHaveBeenCalledWith('magic-token')
    expect(push).toHaveBeenCalledWith({ name: 'client-home' })
  })
})
