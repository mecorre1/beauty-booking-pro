/** Shared TypeScript types aligned with API schemas (SPEC / Pydantic). */

export type ServiceType = 'haircut' | 'haircut_hairdressing' | 'color'
export type ServiceGender = 'male' | 'female'
export type BookingLocation = 'salon' | 'home'

export type PublicService = {
  id: number
  type: ServiceType
  gender: ServiceGender
  base_duration_minutes: number
}

export type PublicSlot = {
  id: number
  date: string
  start_time: string
  end_time: string
  duration_minutes: number
  price: number
  is_available: boolean
}
