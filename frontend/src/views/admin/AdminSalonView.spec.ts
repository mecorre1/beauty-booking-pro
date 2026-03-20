import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

const fetchAdmin = vi.fn()

vi.mock('../../api/admin', () => ({
  fetchAdmin: (...args: Parameters<typeof fetchAdmin>) => fetchAdmin(...args),
}))

import AdminSalonView from './AdminSalonView.vue'

describe('AdminSalonView', () => {
  it('loads salon and saves', async () => {
    fetchAdmin.mockImplementation((path: string, init?: RequestInit) => {
      if (path === '/salon' && init?.method === 'PUT') {
        return Promise.resolve(
          new Response(JSON.stringify({ id: 1, name: 'New', address: 'A', phone: 'P', email: 'e@e.com' }), {
            status: 200,
          }),
        )
      }
      if (path === '/salon') {
        return Promise.resolve(
          new Response(JSON.stringify({ id: 1, name: 'Old', address: 'Street', phone: '1', email: 'o@o.com' }), {
            status: 200,
          }),
        )
      }
      return Promise.resolve(new Response('null', { status: 404 }))
    })

    const wrapper = mount(AdminSalonView)
    await flushPromises()

    await wrapper.findAll('input')[0]!.setValue('New')
    await wrapper.get('form').trigger('submit.prevent')
    await flushPromises()
    expect(wrapper.text()).toContain('Saved')
    expect(fetchAdmin).toHaveBeenCalledWith(
      '/salon',
      expect.objectContaining({ method: 'PUT' }),
    )
  })
})
