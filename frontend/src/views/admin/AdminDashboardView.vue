<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchAdmin } from '../../api/admin'
import PageTitle from '../../components/shared/PageTitle.vue'

type Row = {
  id: number
  slot_date: string
  slot_start_time: string
  client_name: string
  client_email: string
  status: string
  service_type: string
}

const upcoming = ref<Row[]>([])
const past = ref<Row[]>([])
const error = ref<string | null>(null)

async function load() {
  error.value = null
  try {
    const [u, p] = await Promise.all([
      fetchAdmin('/bookings?upcoming=true'),
      fetchAdmin('/bookings?upcoming=false'),
    ])
    if (!u.ok || !p.ok) throw new Error('Failed to load bookings')
    upcoming.value = (await u.json()) as Row[]
    past.value = (await p.json()) as Row[]
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
    <PageTitle>Back office</PageTitle>
    <nav class="nav">
      <router-link to="/admin/calendar">Calendar</router-link>
      <router-link to="/admin/salon">Salon</router-link>
      <router-link to="/admin/schedule">Schedule templates</router-link>
      <router-link to="/admin/pricing">Pricing</router-link>
    </nav>
    <p v-if="error" class="error">{{ error }}</p>
    <section>
      <h2 class="h2">Upcoming</h2>
      <ul class="list">
        <li v-for="b in upcoming" :key="b.id" class="item">
          {{ b.slot_date }} {{ b.slot_start_time.slice(0, 5) }} · {{ b.client_name }} · {{ b.service_type }} ·
          {{ b.status }}
        </li>
        <li v-if="!upcoming.length" class="muted">No upcoming bookings.</li>
      </ul>
    </section>
    <section>
      <h2 class="h2">Past</h2>
      <ul class="list">
        <li v-for="b in past" :key="b.id" class="item">
          {{ b.slot_date }} {{ b.slot_start_time.slice(0, 5) }} · {{ b.client_name }} · {{ b.service_type }}
        </li>
        <li v-if="!past.length" class="muted">No past bookings.</li>
      </ul>
    </section>
  </main>
</template>

<style scoped>
.page {
  max-width: 56rem;
  margin: 0 auto;
  padding: 2rem 1.25rem;
}
.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1rem;
  margin-bottom: 1.25rem;
}
.h2 {
  font-size: 1.1rem;
  margin: 1rem 0 0.5rem;
}
.list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.item {
  padding: 0.35rem 0;
  border-bottom: 1px solid #e2e8f0;
}
.muted {
  color: #64748b;
}
.error {
  color: #b91c1c;
}
</style>
