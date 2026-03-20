<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  cancelBookingByToken,
  fetchPublicServices,
  getBookingByToken,
  updateBookingByToken,
} from '../../api/client'
import PageTitle from '../../components/shared/PageTitle.vue'
import type { PublicService, ServiceGender, ServiceType } from '../../types'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref<string | null>(null)
const services = ref<PublicService[]>([])
const booking = ref<Awaited<ReturnType<typeof getBookingByToken>> | null>(null)

const serviceType = ref<ServiceType | null>(null)
const gender = ref<ServiceGender | null>(null)
const selectedService = computed(() => {
  if (!serviceType.value || !gender.value) return null
  return services.value.find((s) => s.type === serviceType.value && s.gender === gender.value) ?? null
})

const location = ref<'salon' | 'home' | null>(null)
const homeAddress = ref('')
const name = ref('')
const email = ref('')
const phone = ref('')
const slotId = ref<number | null>(null)

onMounted(async () => {
  const token = route.params.token as string
  try {
    services.value = await fetchPublicServices()
    booking.value = await getBookingByToken(token)
    const b = booking.value
    name.value = b.client_name
    email.value = b.client_email
    phone.value = b.client_phone
    location.value = b.location
    homeAddress.value = b.home_address ?? ''
    slotId.value = b.slot_id
    const svc = services.value.find((s) => s.id === b.service_id)
    if (svc) {
      serviceType.value = svc.type
      gender.value = svc.gender
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Could not load booking'
  } finally {
    loading.value = false
  }
})

async function save() {
  const token = route.params.token as string
  if (!selectedService.value || !location.value || slotId.value == null) return
  if (location.value === 'home' && !homeAddress.value.trim()) {
    error.value = 'Home address required.'
    return
  }
  error.value = null
  try {
    await updateBookingByToken(token, {
      slot_id: slotId.value,
      service_id: selectedService.value.id,
      location: location.value,
      home_address: location.value === 'home' ? homeAddress.value.trim() : null,
      client_name: name.value.trim(),
      client_email: email.value.trim(),
      client_phone: phone.value.trim(),
    })
    await router.push({ name: 'client-home' })
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Update failed'
  }
}

async function cancel() {
  const token = route.params.token as string
  if (!window.confirm('Cancel this booking?')) return
  try {
    await cancelBookingByToken(token)
    await router.push({ name: 'client-home' })
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Cancel failed'
  }
}
</script>

<template>
  <main class="page">
    <PageTitle>Edit booking</PageTitle>
    <p v-if="loading" class="muted">Loading…</p>
    <p v-else-if="error" class="error">{{ error }}</p>
    <form v-else class="form card" @submit.prevent="save">
      <p class="muted">Slot #{{ slotId }} — change slot in a future iteration or re-book from home.</p>
      <label class="label">
        Service type
        <select v-model="serviceType" class="input" required>
          <option disabled value="">Select</option>
          <option value="haircut">Regular haircut</option>
          <option value="haircut_hairdressing">Haircut + hairdressing</option>
          <option value="color">Color</option>
        </select>
      </label>
      <label class="label">
        Gender
        <select v-model="gender" class="input" required>
          <option disabled value="">Select</option>
          <option value="male">Male</option>
          <option value="female">Female</option>
        </select>
      </label>
      <label class="label">
        Location
        <select v-model="location" class="input" required>
          <option disabled value="">Select</option>
          <option value="salon">At salon</option>
          <option value="home">At home</option>
        </select>
      </label>
      <label v-if="location === 'home'" class="label">
        Home address
        <input v-model="homeAddress" class="input" required />
      </label>
      <label class="label">
        Name
        <input v-model="name" class="input" required />
      </label>
      <label class="label">
        Email
        <input v-model="email" class="input" type="email" required />
      </label>
      <label class="label">
        Phone
        <input v-model="phone" class="input" required />
      </label>
      <button class="btn" type="submit">Save changes</button>
      <button class="btn danger" type="button" @click="cancel">Cancel booking</button>
    </form>
  </main>
</template>

<style scoped>
.page {
  max-width: 40rem;
  margin: 0 auto;
  padding: 2rem 1.25rem;
}
.muted {
  color: var(--muted-foreground);
}
.error {
  color: var(--destructive);
}
.form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1rem 1.25rem;
}
.label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.input {
  padding: 0.5rem 0.6rem;
  border: 1px solid var(--border);
  border-radius: 0.35rem;
  background: var(--background);
}
.btn {
  padding: 0.55rem 1rem;
  border-radius: 0.35rem;
  border: none;
  background: var(--primary);
  color: var(--primary-foreground);
  cursor: pointer;
}
.btn.danger {
  background: var(--destructive);
  color: var(--primary-foreground);
}
</style>
