<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchAdmin } from '../../api/admin'
import PageTitle from '../../components/shared/PageTitle.vue'

type Row = { id: number; service_id: number; valid_from: string; valid_to: string | null; price: string }

const rows = ref<Row[]>([])
const serviceId = ref(1)
const price = ref('40.00')
const validFrom = ref('2030-01-01T00:00:00')
const error = ref<string | null>(null)
const message = ref<string | null>(null)

async function load() {
  error.value = null
  try {
    const res = await fetchAdmin('/services/price-entries')
    if (!res.ok) throw new Error('Failed to load price entries')
    rows.value = (await res.json()) as Row[]
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Error'
  }
}

async function createEntry() {
  error.value = null
  message.value = null
  try {
    const res = await fetchAdmin('/services/price-entries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        service_id: serviceId.value,
        valid_from: validFrom.value,
        valid_to: null,
        price: price.value,
      }),
    })
    if (!res.ok) throw new Error('Create failed (overlapping range?)')
    message.value = 'Price entry created.'
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Error'
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <main class="page">
    <PageTitle>Pricing</PageTitle>
    <p><router-link class="link" to="/admin">← Dashboard</router-link></p>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="message" class="ok">{{ message }}</p>
    <section class="card">
      <h2 class="h2">Entries</h2>
      <ul class="list">
        <li v-for="r in rows" :key="r.id">
          service {{ r.service_id }} · {{ r.price }} · from {{ r.valid_from }}
        </li>
      </ul>
    </section>
    <section class="card">
      <h2 class="h2">Add entry</h2>
      <label class="label">Service id <input v-model.number="serviceId" class="input" type="number" min="1" /></label>
      <label class="label">Valid from <input v-model="validFrom" class="input" /></label>
      <label class="label">Price <input v-model="price" class="input" /></label>
      <button type="button" class="btn" @click="createEntry">Create</button>
    </section>
  </main>
</template>

<style scoped>
.page {
  max-width: 42rem;
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
.h2 {
  font-size: 1.05rem;
  margin: 0 0 0.5rem;
}
.list {
  margin: 0;
  padding-left: 1.2rem;
}
.label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
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
.error {
  color: var(--destructive);
}
.ok {
  color: var(--color-success);
}
.link {
  color: var(--color-info);
}
</style>
