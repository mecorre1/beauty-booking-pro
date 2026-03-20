import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

const fetchAdmin = vi.fn()

vi.mock('../../api/admin', () => ({
  fetchAdmin: (...args: Parameters<typeof fetchAdmin>) => fetchAdmin(...args),
}))

import AdminCalendarView from './AdminCalendarView.vue'

describe('AdminCalendarView', () => {
  it('loads week and styles booked rows; prev triggers another fetch', async () => {
    fetchAdmin.mockResolvedValue(
      new Response(
        JSON.stringify({
          slots: [
            {
              id: 1,
              date: '2040-01-01',
              start_time: '09:00:00',
              end_time: '10:00:00',
              is_available: false,
              booking_id: 42,
            },
          ],
        }),
        { status: 200 },
      ),
    )

    const wrapper = mount(AdminCalendarView)
    await flushPromises()

    expect(fetchAdmin).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Booking #42')
    const booked = wrapper.find('.item.booked')
    expect(booked.exists()).toBe(true)

    const callsBefore = fetchAdmin.mock.calls.length
    await wrapper.get('button.btn').trigger('click')
    await flushPromises()
    expect(fetchAdmin.mock.calls.length).toBeGreaterThan(callsBefore)
  })
})
