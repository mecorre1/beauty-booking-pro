<script setup lang="ts">
import { computed, onBeforeMount, ref } from 'vue'
import { useRouter } from 'vue-router'

import { createBooking } from '../../api/client'
import PageTitle from '../../components/shared/PageTitle.vue'
import { useBookingSelection } from '../../composables/useBookingSelection'

const router = useRouter()
const { selectedSlot, selectedService, location, displayTotalEur, canContinue, resetBookingSelection } =
  useBookingSelection()

const name = ref('')
const email = ref('')
const phone = ref('')
const homeAddress = ref('')
const submitting = ref(false)
const error = ref<string | null>(null)
const success = ref<{ editUrl: string } | null>(null)

onBeforeMount(() => {
  if (!canContinue.value) {
    void router.replace({ name: 'client-home' })
  }
})

const needsHomeAddress = computed(() => location.value === 'home')

async function submit() {
  if (!selectedSlot.value || !selectedService.value || !location.value) return
  if (needsHomeAddress.value && !homeAddress.value.trim()) {
    error.value = 'Please enter your home address.'
    return
  }
  submitting.value = true
  error.value = null
  try {
    const created = await createBooking({
      slot_id: selectedSlot.value.id,
      service_id: selectedService.value.id,
      location: location.value,
      home_address: needsHomeAddress.value ? homeAddress.value.trim() : null,
      client_name: name.value.trim(),
      client_email: email.value.trim(),
      client_phone: phone.value.trim(),
    })
    const base = window.location.origin
    success.value = { editUrl: `${base}/book/edit/${created.edit_token}` }
    resetBookingSelection()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Booking failed'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main v-if="!success" class="page">
    <PageTitle>Confirm booking</PageTitle>

    <section v-if="selectedSlot && selectedService" class="card recap">
      <p>
        {{ selectedSlot.date }} · {{ selectedSlot.start_time.slice(0, 5) }} – {{ selectedSlot.end_time.slice(0, 5) }}
      </p>
      <p class="muted">Total (estimate): €{{ displayTotalEur?.toFixed(2) ?? '—' }}</p>
    </section>

    <p v-if="error" class="error">{{ error }}</p>

    <form class="form card" @submit.prevent="submit">
      <label class="label">
        Name
        <input v-model="name" class="input" required autocomplete="name" />
      </label>
      <label class="label">
        Email
        <input v-model="email" class="input" type="email" required autocomplete="email" />
      </label>
      <label class="label">
        Phone
        <input v-model="phone" class="input" required autocomplete="tel" />
      </label>
      <label v-if="needsHomeAddress" class="label">
        Home address
        <input v-model="homeAddress" class="input" required autocomplete="street-address" />
      </label>
      <button class="btn" type="submit" :disabled="submitting || !canContinue">Confirm</button>
    </form>
  </main>

  <main v-else class="page">
    <PageTitle>Booking confirmed</PageTitle>
    <p class="card">You’re booked. Manage your appointment any time:</p>
    <p>
      <a class="link" :href="success!.editUrl">{{ success!.editUrl }}</a>
    </p>
  </main>
</template>

<style scoped>
.page {
  max-width: 40rem;
  margin: 0 auto;
  padding: 2rem 1.25rem;
}
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1rem 1.25rem;
  margin-bottom: 1rem;
}
.recap {
  margin-bottom: 1rem;
}
.muted {
  color: var(--muted-foreground);
  margin-top: 0.35rem;
}
.form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.9rem;
}
.input {
  padding: 0.5rem 0.6rem;
  border: 1px solid var(--border);
  border-radius: 0.35rem;
  background: var(--background);
}
.btn {
  margin-top: 0.5rem;
  padding: 0.55rem 1rem;
  border-radius: 0.35rem;
  border: none;
  background: var(--primary);
  color: var(--primary-foreground);
  cursor: pointer;
}
.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.error {
  color: var(--destructive);
}
.link {
  word-break: break-all;
  color: var(--color-info);
}
</style>
