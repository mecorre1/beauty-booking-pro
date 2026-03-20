import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
  useRoute: () => ({ query: {} }),
}))

vi.mock('../../api/admin', () => ({
  loginAdmin: vi.fn(() => Promise.resolve('test-token')),
  setAdminToken: vi.fn(),
}))

import { loginAdmin, setAdminToken } from '../../api/admin'
import AdminLoginView from './AdminLoginView.vue'

describe('AdminLoginView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('submits credentials and stores token', async () => {
    const wrapper = mount(AdminLoginView)
    await wrapper.get('input[type="email"]').setValue('admin@test.com')
    await wrapper.get('input[type="password"]').setValue('password12')
    await wrapper.get('form').trigger('submit.prevent')
    await flushPromises()
    expect(loginAdmin).toHaveBeenCalledWith('admin@test.com', 'password12')
    expect(setAdminToken).toHaveBeenCalledWith('test-token')
    expect(push).toHaveBeenCalled()
  })
})
