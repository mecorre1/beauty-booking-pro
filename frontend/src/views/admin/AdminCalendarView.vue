<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchAdmin } from '../../api/admin'
import PageTitle from '../../components/shared/PageTitle.vue'
import { isoWeekLabel, shiftIsoWeek } from '../../utils/isoWeek'

type SlotRow = {
  id: number
  date: string
  start_time: string
  end_time: string
  is_available: boolean
  booking_id: number | null
}

const weekLabel = ref(isoWeekLabel(new Date()))
const slots = ref<SlotRow[]>([])
const error = ref<string | null>(null)

const title = computed(() => `Week ${weekLabel.value}`)

async function load() {
  error.value = null
  try {
    const res = await fetchAdmin(`/bookings/calendar?week=${encodeURIComponent(weekLabel.value)}`)
    if (!res.ok) throw new Error('Failed to load calendar')
    const data = (await res.json()) as { slots: SlotRow[] }
    slots.value = data.slots
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Error'
  }
}

function prev() {
  weekLabel.value = shiftIsoWeek(weekLabel.value, -1)
  void load()
}

function next() {
  weekLabel.value = shiftIsoWeek(weekLabel.value, 1)
  void load()
}

onMounted(() => {
  void load()
})
</script>

<template>
  <main class="page">
    <PageTitle>Calendar</PageTitle>
    <div class="toolbar">
      <button type="button" class="btn" @click="prev">← Prev</button>
      <span class="week">{{ title }}</span>
      <button type="button" class="btn" @click="next">Next →</button>
      <router-link class="link" to="/admin">Dashboard</router-link>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <ul class="list">
      <li v-for="s in slots" :key="s.id" class="item" :class="{ booked: s.booking_id }">
        {{ s.date }} {{ s.start_time.slice(0, 5) }}–{{ s.end_time.slice(0, 5) }}
        <span v-if="s.booking_id" class="tag">Booking #{{ s.booking_id }}</span>
        <span v-else-if="!s.is_available" class="tag muted">Unavailable</span>
      </li>
      <li v-if="!slots.length" class="muted">No slots this week.</li>
    </ul>
  </main>
</template>

<style scoped>
.page {
  max-width: 48rem;
  margin: 0 auto;
  padding: 2rem 1.25rem;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}
.week {
  font-weight: 600;
}
.btn {
  padding: 0.35rem 0.65rem;
  border-radius: 0.35rem;
  border: 1px solid var(--border);
  background: var(--background);
  cursor: pointer;
}
.btn:hover {
  background: var(--surface-hover);
}
.link {
  margin-left: auto;
  color: var(--color-info);
}
.list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.item {
  padding: 0.4rem 0;
  border-bottom: 1px solid var(--border);
}
.item.booked {
  background: var(--color-info-bg);
}
.tag {
  margin-left: 0.5rem;
  font-size: 0.85rem;
}
.muted {
  color: var(--muted-foreground);
}
.error {
  color: var(--destructive);
}
</style>
