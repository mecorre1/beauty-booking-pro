import { flushPromises, mount } from '@vue/test-utils'
import { ref } from 'vue'
import { describe, expect, it, vi } from 'vitest'

vi.mock('vue-router', () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
}))

vi.mock('../../composables/useBookingSelection', () => {
  const selectedSlot = ref({
    id: 9,
    date: '2030-06-01',
    start_time: '09:00:00',
    end_time: '10:00:00',
    duration_minutes: 60,
    price: 40,
    is_available: true,
  })
  const selectedService = ref({
    id: 1,
    type: 'haircut' as const,
    gender: 'male' as const,
    base_duration_minutes: 30,
  })
  const location = ref<'salon' | 'home'>('salon')
  return {
    useBookingSelection: () => ({
      selectedSlot,
      selectedService,
      location,
      displayTotalEur: ref(40),
      canContinue: ref(true),
      resetBookingSelection: vi.fn(),
    }),
  }
})

vi.mock('../../api/client', () => ({
  createBooking: vi.fn(() =>
    Promise.resolve({
      id: 1,
      edit_token: 'tok',
      status: 'confirmed',
    }),
  ),
}))

import { createBooking } from '../../api/client'
import ClientConfirmView from './ClientConfirmView.vue'

describe('ClientConfirmView', () => {
  it('submits booking and shows success with edit link', async () => {
    const wrapper = mount(ClientConfirmView)
    await wrapper.get('input[autocomplete="name"]').setValue('Ada')
    await wrapper.get('input[type="email"]').setValue('ada@test.com')
    await wrapper.get('input[autocomplete="tel"]').setValue('555')
    await wrapper.get('form').trigger('submit.prevent')
    await flushPromises()
    expect(createBooking).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Booking confirmed')
    expect(wrapper.text()).toContain('/book/edit/tok')
  })
})
