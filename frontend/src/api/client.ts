/** Public (client) API — no admin credentials. */

import type { PublicService, PublicSlot } from '../types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export function publicApiUrl(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE.replace(/\/$/, '')}${p}`
}

export function fetchPublic(path: string, init?: RequestInit): Promise<Response> {
  return fetch(publicApiUrl(path), init)
}

export async function fetchPublicSlots(week: string): Promise<PublicSlot[]> {
  const res = await fetchPublic(`/api/public/slots?week=${encodeURIComponent(week)}`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || res.statusText)
  }
  return res.json() as Promise<PublicSlot[]>
}

export async function fetchPublicServices(): Promise<PublicService[]> {
  const res = await fetchPublic('/api/public/services')
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || res.statusText)
  }
  return res.json() as Promise<PublicService[]>
}

export type PricingMeta = { at_home_surcharge_eur: number }

export async function fetchPricingMeta(): Promise<PricingMeta> {
  const res = await fetchPublic('/api/public/pricing-meta')
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || res.statusText)
  }
  return res.json() as Promise<PricingMeta>
}

export type CreateBookingPayload = {
  slot_id: number
  service_id: number
  location: 'salon' | 'home'
  home_address?: string | null
  client_name: string
  client_email: string
  client_phone: string
}

export type BookingPublic = {
  id: number
  slot_id: number
  service_id: number
  location: 'salon' | 'home'
  home_address: string | null
  client_name: string
  client_email: string
  client_phone: string
  status: string
  price_at_booking: string
  salon_address_at_booking: string
  edit_token: string
}

export async function createBooking(body: CreateBookingPayload): Promise<BookingPublic> {
  const res = await fetchPublic('/api/public/bookings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || res.statusText)
  }
  return res.json() as Promise<BookingPublic>
}

export async function getBookingByToken(token: string): Promise<BookingPublic> {
  const res = await fetchPublic(`/api/public/bookings/by-token/${encodeURIComponent(token)}`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || res.statusText)
  }
  return res.json() as Promise<BookingPublic>
}

export async function updateBookingByToken(
  token: string,
  body: CreateBookingPayload,
): Promise<BookingPublic> {
  const res = await fetchPublic(`/api/public/bookings/by-token/${encodeURIComponent(token)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || res.statusText)
  }
  return res.json() as Promise<BookingPublic>
}

export async function cancelBookingByToken(token: string): Promise<void> {
  const res = await fetchPublic(`/api/public/bookings/by-token/${encodeURIComponent(token)}/cancel`, {
    method: 'POST',
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || res.statusText)
  }
}
