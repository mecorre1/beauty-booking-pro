import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

const fetchAdmin = vi.fn()

vi.mock('../../api/admin', () => ({
  fetchAdmin: (...args: Parameters<typeof fetchAdmin>) => fetchAdmin(...args),
}))

import AdminScheduleView from './AdminScheduleView.vue'

describe('AdminScheduleView', () => {
  it('creates template and applies week', async () => {
    fetchAdmin.mockImplementation((path: string, init?: RequestInit) => {
      if (path === '/schedule/templates' && init?.method === 'POST') {
        return Promise.resolve(
          new Response(JSON.stringify({ id: 7, name: 'Standard week', slots: [] }), { status: 201 }),
        )
      }
      if (path === '/schedule/templates') {
        return Promise.resolve(
          new Response(
            JSON.stringify([{ id: 7, name: 'Demo', slots: [{ id: 1, day_of_week: 0, start_time: '09:00:00', duration_minutes: 60 }] }]),
            { status: 200 },
          ),
        )
      }
      if (path === '/schedule/apply') {
        return Promise.resolve(new Response(JSON.stringify({ slots_created: 2 }), { status: 201 }))
      }
      return Promise.resolve(new Response('null', { status: 404 }))
    })

    const wrapper = mount(AdminScheduleView)
    await flushPromises()
    expect(wrapper.text()).toContain('Demo')

    await wrapper.get('button.secondary').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Template created')

    const applyBtn = wrapper.findAll('button').find((b) => b.text().trim() === 'Apply')
    expect(applyBtn).toBeTruthy()
    await applyBtn!.trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Applied: 2 slot(s)')
  })
})
