import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

const fetchAdmin = vi.fn()

vi.mock('../../api/admin', () => ({
  fetchAdmin: (...args: Parameters<typeof fetchAdmin>) => fetchAdmin(...args),
}))

import AdminCalendarView from './AdminCalendarView.vue'

describe('AdminCalendarView', () => {
  it('loads schedule and renders working hours, exceptions and bookings', async () => {
    fetchAdmin.mockImplementation((path: string) => {
      if (path.includes('/schedule?')) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              week: '2040-01',
              days: [
                {
                  date: '2040-01-01',
                  day_of_week: 0,
                  open_time: '09:00:00',
                  close_time: '18:00:00',
                },
              ],
              exceptions: [
                {
                  id: 7,
                  start: '2040-01-01T12:00:00',
                  end: '2040-01-01T13:00:00',
                  comment: 'Break',
                  created_at: '2040-01-01T08:00:00',
                },
              ],
              bookings: [
                {
                  id: 42,
                  start: '2040-01-01T10:00:00',
                  end: '2040-01-01T10:45:00',
                  client_name: 'Ada',
                  client_email: 'a@a.com',
                  client_phone: '555',
                  service_type: 'haircut',
                  location: 'salon',
                  status: 'confirmed',
                  slot_id: 1,
                },
              ],
            }),
            { status: 200 },
          ),
        )
      }
      return Promise.resolve(new Response('', { status: 404 }))
    })

    const wrapper = mount(AdminCalendarView, {
      global: { stubs: { RouterLink: true } },
    })
    await flushPromises()

    expect(fetchAdmin).toHaveBeenCalledWith(expect.stringContaining('/schedule?week='))
    expect(wrapper.find('.layer-working').exists()).toBe(true)
    expect(wrapper.find('.block-exception').exists()).toBe(true)
    expect(wrapper.find('.block-booking').exists()).toBe(true)
    expect(wrapper.text()).toContain('Ada')
    expect(wrapper.text()).toContain('Exceptions this week')

    await wrapper.get('.block-booking').trigger('click')
    expect(wrapper.text()).toContain('Booking #42')

    const callsBefore = fetchAdmin.mock.calls.length
    await wrapper.get('button.btn').trigger('click')
    await flushPromises()
    expect(fetchAdmin.mock.calls.length).toBeGreaterThan(callsBefore)
  })
})
