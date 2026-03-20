<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { fetchPublicSlots } from '../../api/client'
import PageTitle from '../../components/shared/PageTitle.vue'
import { useBookingSelection } from '../../composables/useBookingSelection'
import type { PublicSlot } from '../../types'
import { formatLocalDate, isoWeekLabel, mondayOfIsoWeekLabel } from '../../utils/isoWeek'

const router = useRouter()
const { setSelectedSlot } = useBookingSelection()

const weekLabel = ref(isoWeekLabel(new Date()))
const slots = ref<PublicSlot[]>([])
const loading = ref(false)
const loadError = ref<string | null>(null)

const weekdayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

const weekDays = computed(() => {
  let mon: Date
  try {
    mon = mondayOfIsoWeekLabel(weekLabel.value)
  } catch {
    mon = mondayOfIsoWeekLabel(isoWeekLabel(new Date()))
  }
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(mon)
    d.setDate(mon.getDate() + i)
    return {
      dateKey: formatLocalDate(d),
      title: weekdayLabels[i],
      display: d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    }
  })
})

const slotsByDate = computed(() => {
  const map = new Map<string, PublicSlot[]>()
  for (const s of slots.value) {
    const list = map.get(s.date) ?? []
    list.push(s)
    map.set(s.date, list)
  }
  for (const list of map.values()) {
    list.sort((a, b) => a.start_time.localeCompare(b.start_time))
  }
  return map
})

async function loadSlots() {
  loading.value = true
  loadError.value = null
  try {
    slots.value = await fetchPublicSlots(weekLabel.value)
  } catch (e) {
    loadError.value = e instanceof Error ? e.message : 'Could not load slots'
    slots.value = []
  } finally {
    loading.value = false
  }
}

function shiftWeek(delta: number) {
  try {
    const mon = mondayOfIsoWeekLabel(weekLabel.value)
    mon.setDate(mon.getDate() + delta * 7)
    weekLabel.value = isoWeekLabel(mon)
  } catch {
    const today = new Date()
    today.setDate(today.getDate() + delta * 7)
    weekLabel.value = isoWeekLabel(today)
  }
}

function pickSlot(slot: PublicSlot) {
  if (!slot.is_available) return
  setSelectedSlot(slot)
  void router.push({ name: 'book-service' })
}

onMounted(() => {
  void loadSlots()
})

watch(weekLabel, () => {
  void loadSlots()
})
</script>

<template>
  <main class="page">
    <PageTitle>Book an appointment</PageTitle>

    <div class="toolbar">
      <button type="button" class="btn-ghost" @click="shiftWeek(-1)">Previous week</button>
      <span class="week-chip">Week {{ weekLabel }}</span>
      <button type="button" class="btn-ghost" @click="shiftWeek(1)">Next week</button>
    </div>

    <p v-if="loading" class="muted">Loading available times…</p>
    <p v-else-if="loadError" class="error">{{ loadError }}</p>

    <div class="calendar" role="list" aria-label="Weekly slots">
      <section
        v-for="day in weekDays"
        :key="day.dateKey"
        class="day-col"
        role="listitem"
      >
        <header class="day-head">
          <span class="dow">{{ day.title }}</span>
          <span class="dom">{{ day.display }}</span>
        </header>
        <ul class="slot-list">
          <li v-for="s in slotsByDate.get(day.dateKey) ?? []" :key="s.id">
            <button
              type="button"
              class="slot-card"
              :class="{ disabled: !s.is_available }"
              :disabled="!s.is_available"
              :aria-disabled="!s.is_available"
              @click="pickSlot(s)"
            >
              <span class="time">{{ s.start_time.slice(0, 5) }} – {{ s.end_time.slice(0, 5) }}</span>
              <span class="meta">{{ s.duration_minutes }} min · €{{ s.price.toFixed(2) }}</span>
            </button>
          </li>
          <li
            v-if="!(slotsByDate.get(day.dateKey)?.length)"
            class="empty-day muted"
          >
            No slots
          </li>
        </ul>
      </section>
    </div>
  </main>
</template>

<style scoped>
.page {
  max-width: 72rem;
  margin: 0 auto;
  padding: 2rem 1.25rem;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin: 1rem 0 1.25rem;
}

.week-chip {
  font-weight: 600;
  color: #0f172a;
}

.btn-ghost {
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #334155;
  padding: 0.35rem 0.65rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-ghost:hover {
  background: #f8fafc;
}

.muted {
  color: #64748b;
  margin: 0.25rem 0;
}

.error {
  color: #b91c1c;
}

.calendar {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0.75rem;
}

@media (max-width: 900px) {
  .calendar {
    grid-template-columns: 1fr;
  }
}

.day-col {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 0.5rem;
  min-height: 6rem;
}

.day-head {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  padding: 0.35rem 0.25rem 0.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.dow {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #64748b;
  font-weight: 600;
}

.dom {
  font-size: 0.95rem;
  font-weight: 600;
  color: #0f172a;
}

.slot-list {
  list-style: none;
  margin: 0.5rem 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.slot-card {
  width: 100%;
  text-align: left;
  border: 1px solid #cbd5e1;
  border-radius: 0.375rem;
  padding: 0.45rem 0.5rem;
  background: #fff;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.slot-card:hover:not(:disabled) {
  border-color: #94a3b8;
  background: #f1f5f9;
}

.slot-card.disabled {
  opacity: 0.55;
  cursor: not-allowed;
  background: #f1f5f9;
}

.time {
  font-weight: 600;
  color: #0f172a;
  font-size: 0.875rem;
}

.meta {
  font-size: 0.8rem;
  color: #64748b;
}

.empty-day {
  font-size: 0.8rem;
  padding: 0.25rem;
}
</style>
