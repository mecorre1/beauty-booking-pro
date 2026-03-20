<script setup lang="ts">
import { onBeforeMount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { fetchPublicServices } from '../../api/client'
import PageTitle from '../../components/shared/PageTitle.vue'
import { AT_HOME_DISPLAY_SURCHARGE_EUR } from '../../constants/pricing'
import { useBookingSelection } from '../../composables/useBookingSelection'
import type { PublicService, ServiceGender, ServiceType } from '../../types'

const router = useRouter()
const {
  selectedSlot,
  location,
  displayTotalEur,
  slotFitsServiceDuration,
  canContinue,
  syncServiceFromChoices,
} = useBookingSelection()

const services = ref<PublicService[]>([])
const loadError = ref<string | null>(null)
const serviceType = ref<ServiceType | null>(null)
const gender = ref<ServiceGender | null>(null)

const serviceTypeOptions: { value: ServiceType; label: string }[] = [
  { value: 'haircut', label: 'Regular haircut' },
  { value: 'haircut_hairdressing', label: 'Haircut + hairdressing' },
  { value: 'color', label: 'Color' },
]

onBeforeMount(() => {
  if (!selectedSlot.value) {
    void router.replace({ name: 'client-home' })
  }
})

onMounted(async () => {
  try {
    services.value = await fetchPublicServices()
  } catch (e) {
    loadError.value = e instanceof Error ? e.message : 'Could not load services'
    services.value = []
  }
})

watch(
  [services, serviceType, gender],
  () => {
    syncServiceFromChoices(services.value, serviceType.value, gender.value)
  },
  { flush: 'sync' },
)

function goConfirm() {
  if (!canContinue.value) return
  void router.push({ name: 'book-confirm' })
}

const homeSurchargeLabel = AT_HOME_DISPLAY_SURCHARGE_EUR.toFixed(2)
</script>

<template>
  <main v-if="selectedSlot" class="page">
    <PageTitle>Choose your session</PageTitle>

    <section class="recap card">
      <h2 class="h2">Selected time</h2>
      <p class="recap-line">
        {{ selectedSlot.date }} · {{ selectedSlot.start_time.slice(0, 5) }} –
        {{ selectedSlot.end_time.slice(0, 5) }}
      </p>
      <p class="muted">Window: {{ selectedSlot.duration_minutes }} min · base €{{ selectedSlot.price.toFixed(2) }}</p>
    </section>

    <p v-if="loadError" class="error">{{ loadError }}</p>

    <form class="form card" @submit.prevent="goConfirm">
      <fieldset class="fieldset" :disabled="!services.length">
        <legend class="legend">Service</legend>
        <div class="options">
          <label v-for="opt in serviceTypeOptions" :key="opt.value" class="radio">
            <input v-model="serviceType" type="radio" name="serviceType" :value="opt.value" />
            <span>{{ opt.label }}</span>
          </label>
        </div>
      </fieldset>

      <fieldset class="fieldset" :disabled="!services.length">
        <legend class="legend">Gender</legend>
        <div class="options">
          <label class="radio">
            <input v-model="gender" type="radio" name="gender" value="male" />
            <span>Male</span>
          </label>
          <label class="radio">
            <input v-model="gender" type="radio" name="gender" value="female" />
            <span>Female</span>
          </label>
        </div>
      </fieldset>

      <fieldset class="fieldset" :disabled="!services.length">
        <legend class="legend">Location</legend>
        <div class="options">
          <label class="radio">
            <input v-model="location" type="radio" name="location" value="salon" />
            <span>At the salon</span>
          </label>
          <label class="radio">
            <input v-model="location" type="radio" name="location" value="home" />
            <span>At home</span>
          </label>
        </div>
      </fieldset>

      <p v-if="serviceType && gender && !slotFitsServiceDuration" class="warn">
        This slot is shorter than the service duration (
        {{ services.find((s) => s.type === serviceType && s.gender === gender)?.base_duration_minutes }} min required).
        Choose another time on the calendar.
      </p>

      <div v-if="displayTotalEur != null" class="total">
        <span class="total-label">Estimated total</span>
        <span class="total-value">€{{ displayTotalEur.toFixed(2) }}</span>
        <span v-if="location === 'home'" class="total-note muted">
          (includes €{{ homeSurchargeLabel }} at-home surcharge; final price at confirm)
        </span>
      </div>

      <button type="submit" class="btn-primary" :disabled="!canContinue">Continue</button>
    </form>
  </main>
</template>

<style scoped>
.page {
  max-width: 48rem;
  margin: 0 auto;
  padding: 2rem 1.25rem;
}

.h2 {
  font-size: 1rem;
  margin: 0 0 0.35rem;
  color: #0f172a;
}

.card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1rem 1.1rem;
  margin-top: 1rem;
}

.recap-line {
  font-weight: 600;
  color: #0f172a;
  margin: 0.25rem 0;
}

.muted {
  color: #64748b;
  font-size: 0.875rem;
  margin: 0.25rem 0 0;
}

.error {
  color: #b91c1c;
  margin-top: 1rem;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.fieldset {
  border: none;
  margin: 0;
  padding: 0;
}

.legend {
  font-weight: 600;
  color: #334155;
  padding: 0;
  margin-bottom: 0.5rem;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.radio {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.95rem;
  color: #0f172a;
}

.warn {
  color: #b45309;
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 0.375rem;
  padding: 0.6rem 0.75rem;
  font-size: 0.875rem;
  margin: 0;
}

.total {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.5rem 1rem;
  padding-top: 0.25rem;
}

.total-label {
  font-weight: 600;
  color: #0f172a;
}

.total-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.total-note {
  flex-basis: 100%;
  font-size: 0.8rem;
}

.btn-primary {
  margin-top: 0.5rem;
  align-self: flex-start;
  border: none;
  background: #0f172a;
  color: #fff;
  padding: 0.55rem 1.1rem;
  border-radius: 0.375rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
