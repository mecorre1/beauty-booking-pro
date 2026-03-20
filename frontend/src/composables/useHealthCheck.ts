import { ref } from 'vue'

import { publicApiUrl } from '../api/client'

/** Example composable: verify API is up (optional dev aid). */
export function useHealthCheck() {
  const status = ref<string | null>(null)
  const error = ref<string | null>(null)

  async function check() {
    error.value = null
    try {
      const res = await fetch(publicApiUrl('/health'))
      status.value = res.ok ? 'ok' : `HTTP ${res.status}`
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
    }
  }

  return { status, error, check }
}
