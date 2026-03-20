import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

const fetchAdmin = vi.fn()

vi.mock('../../api/admin', () => ({
  fetchAdmin: (...args: Parameters<typeof fetchAdmin>) => fetchAdmin(...args),
}))

import AdminPricingView from './AdminPricingView.vue'

describe('AdminPricingView', () => {
  it('lists entries and creates one', async () => {
    let listed = false
    fetchAdmin.mockImplementation((path: string, init?: RequestInit) => {
      if (path === '/services/price-entries' && init?.method === 'POST') {
        return Promise.resolve(
          new Response(
            JSON.stringify({ id: 99, service_id: 1, valid_from: '2030-01-01T00:00:00', valid_to: null, price: '40.00' }),
            { status: 201 },
          ),
        )
      }
      if (path === '/services/price-entries') {
        if (listed) {
          return Promise.resolve(
            new Response(
              JSON.stringify([
                { id: 1, service_id: 1, valid_from: '2000-01-01T00:00:00', valid_to: null, price: '35.00' },
                { id: 99, service_id: 1, valid_from: '2030-01-01T00:00:00', valid_to: null, price: '40.00' },
              ]),
              { status: 200 },
            ),
          )
        }
        listed = true
        return Promise.resolve(
          new Response(
            JSON.stringify([{ id: 1, service_id: 1, valid_from: '2000-01-01T00:00:00', valid_to: null, price: '35.00' }]),
            { status: 200 },
          ),
        )
      }
      return Promise.resolve(new Response('null', { status: 404 }))
    })

    const wrapper = mount(AdminPricingView)
    await flushPromises()
    expect(wrapper.text()).toContain('35.00')

    await wrapper.get('button.btn').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Price entry created')
  })
})
