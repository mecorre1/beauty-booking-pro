import { computed, shallowRef } from 'vue'

import { AT_HOME_DISPLAY_SURCHARGE_EUR } from '../constants/pricing'
import type { BookingLocation, PublicService, PublicSlot, ServiceGender, ServiceType } from '../types'

const selectedSlot = shallowRef<PublicSlot | null>(null)
const selectedService = shallowRef<PublicService | null>(null)
const location = shallowRef<BookingLocation | null>(null)

export function useBookingSelection() {
  const displayTotalEur = computed(() => {
    const slot = selectedSlot.value
    if (!slot) return null
    const extra = location.value === 'home' ? AT_HOME_DISPLAY_SURCHARGE_EUR : 0
    return slot.price + extra
  })

  const slotFitsServiceDuration = computed(() => {
    const slot = selectedSlot.value
    const svc = selectedService.value
    if (!slot || !svc) return false
    return slot.duration_minutes >= svc.base_duration_minutes
  })

  const canContinue = computed(
    () =>
      Boolean(
        selectedSlot.value &&
          selectedService.value &&
          location.value &&
          slotFitsServiceDuration.value,
      ),
  )

  function setSelectedSlot(slot: PublicSlot | null) {
    selectedSlot.value = slot
  }

  function setSelectedService(service: PublicService | null) {
    selectedService.value = service
  }

  function setLocation(loc: BookingLocation | null) {
    location.value = loc
  }

  /** Pick catalog row from parallel type + gender controls. */
  function syncServiceFromChoices(
    services: PublicService[],
    type: ServiceType | null,
    gender: ServiceGender | null,
  ) {
    if (!type || !gender) {
      selectedService.value = null
      return
    }
    selectedService.value = services.find((s) => s.type === type && s.gender === gender) ?? null
  }

  function resetBookingSelection() {
    selectedSlot.value = null
    selectedService.value = null
    location.value = null
  }

  return {
    selectedSlot,
    selectedService,
    location,
    displayTotalEur,
    slotFitsServiceDuration,
    canContinue,
    setSelectedSlot,
    setSelectedService,
    setLocation,
    syncServiceFromChoices,
    resetBookingSelection,
  }
}
