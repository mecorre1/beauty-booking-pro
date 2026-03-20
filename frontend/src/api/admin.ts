/** Authenticated admin API — Bearer token from login/register. */

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
const ADMIN_API_BASE = `${API_BASE.replace(/\/$/, '')}/api/admin`

const TOKEN_KEY = 'beauty_admin_token'

export function adminApiUrl(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`
  return `${ADMIN_API_BASE}${p}`
}

export function getAdminToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setAdminToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export function fetchAdmin(path: string, init?: RequestInit): Promise<Response> {
  const token = getAdminToken()
  return fetch(adminApiUrl(path), {
    ...init,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  })
}

export async function loginAdmin(email: string, password: string): Promise<string> {
  const res = await fetch(adminApiUrl('/auth/login'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const t = await res.text()
    throw new Error(t || res.statusText)
  }
  const data = (await res.json()) as { access_token: string }
  return data.access_token
}
