import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import { Button } from '.'

describe('Button', () => {
  it('renders slot content', () => {
    const wrapper = mount(Button, {
      slots: { default: 'Book now' },
    })
    expect(wrapper.text()).toContain('Book now')
    expect(wrapper.find('[data-slot="button"]').exists()).toBe(true)
  })
})
