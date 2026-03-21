import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

vi.mock('../../api/admin', () => ({
  fetchAdmin: vi.fn((path: string) => {
    if (path.includes('upcoming=true')) {
      return Promise.resolve(
        new Response(
          JSON.stringify([
            {
              id: 1,
              slot_date: '2040-06-01',
              slot_start_time: '09:00:00',
              client_name: 'Ada',
              client_email: 'ada@test.com',
              client_phone: '555',
              client_note: null,
              status: 'confirmed',
              service_type: 'haircut',
            },
          ]),
          { status: 200 },
        ),
      )
    }
    return Promise.resolve(new Response(JSON.stringify([]), { status: 200 }))
  }),
}))

import AdminDashboardView from './AdminDashboardView.vue'

describe('AdminDashboardView', () => {
  it('renders upcoming and past sections', async () => {
    const wrapper = mount(AdminDashboardView)
    await flushPromises()
    expect(wrapper.text()).toContain('Upcoming')
    expect(wrapper.text()).toContain('Past')
    expect(wrapper.text()).toContain('Ada')
    expect(wrapper.text()).toContain('No past bookings')
  })
})
