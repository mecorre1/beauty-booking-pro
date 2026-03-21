<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import { fetchAdmin } from '../../api/admin'
import PageTitle from '../../components/shared/PageTitle.vue'
import { isoWeekLabel, shiftIsoWeek } from '../../utils/isoWeek'

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as const

const VISIBLE_START_MIN = 6 * 60
const VISIBLE_END_MIN = 22 * 60
const RANGE_MIN = VISIBLE_END_MIN - VISIBLE_START_MIN
const SNAP_MIN = 15

type DaySchedule = {
  date: string
  day_of_week: number
  open_time: string | null
  close_time: string | null
}

type ExceptionRow = {
  id: number
  start: string
  end: string
  comment: string | null
}

type BookingRow = {
  id: number
  start: string
  end: string
  client_name: string
  client_email: string
  client_phone: string
  service_type: string
  location: string
  status: string
  slot_id: number
}

const weekLabel = ref(isoWeekLabel(new Date()))
const days = ref<DaySchedule[]>([])
const exceptions = ref<ExceptionRow[]>([])
const bookings = ref<BookingRow[]>([])
const error = ref<string | null>(null)
const selectedBooking = ref<BookingRow | null>(null)

const exceptionComment = ref('')
const exceptionDialog = ref<{ start: Date; end: Date; dateStr: string } | null>(null)

/** Live minutes while resizing working hours (null = use server day values). */
const hoursDraft = ref<Record<string, { open: number; close: number }>>({})

type ResizeState = {
  edge: 'open' | 'close'
  day: DaySchedule
  startY: number
  openMin: number
  closeMin: number
  trackHeight: number
  pointerId: number
  handleEl: HTMLElement
}

const resizeState = ref<ResizeState | null>(null)

type SelectState = {
  dateStr: string
  anchorMin: number
  currentMin: number
  trackEl: HTMLElement
  pointerId: number
}

const selectState = ref<SelectState | null>(null)

const title = computed(() => `Week ${weekLabel.value}`)

function minutesFromTimeStr(t: string): number {
  const parts = t.split(':').map((x) => parseInt(x, 10))
  const h = parts[0] ?? 0
  const m = parts[1] ?? 0
  const s = parts[2] ?? 0
  return h * 60 + m + Math.floor(s / 60)
}

function snap(m: number): number {
  return Math.round(m / SNAP_MIN) * SNAP_MIN
}

function timeStrFromMinutes(m: number): string {
  const h = Math.floor(m / 60)
  const min = m % 60
  return `${String(h).padStart(2, '0')}:${String(min).padStart(2, '0')}`
}

function dayDraft(day: DaySchedule): { open: number; close: number } | null {
  const d = hoursDraft.value[day.date]
  if (d) return d
  if (day.open_time && day.close_time) {
    return {
      open: minutesFromTimeStr(day.open_time),
      close: minutesFromTimeStr(day.close_time),
    }
  }
  return null
}

function workingBarStyle(day: DaySchedule): Record<string, string> | null {
  const draft = dayDraft(day)
  if (!draft || draft.close <= draft.open) return null
  const topMin = Math.max(draft.open, VISIBLE_START_MIN)
  const botMin = Math.min(draft.close, VISIBLE_END_MIN)
  if (botMin <= topMin) return null
  const topPct = ((topMin - VISIBLE_START_MIN) / RANGE_MIN) * 100
  const hPct = ((botMin - topMin) / RANGE_MIN) * 100
  return {
    top: `${topPct}%`,
    height: `${hPct}%`,
  }
}

function blockStyleOnDay(
  dayStr: string,
  startIso: string,
  endIso: string,
): Record<string, string> | null {
  const day0 = new Date(`${dayStr}T00:00:00`)
  const day1 = new Date(day0)
  day1.setDate(day1.getDate() + 1)
  const s = new Date(startIso)
  const e = new Date(endIso)
  const lo = Math.max(s.getTime(), day0.getTime())
  const hi = Math.min(e.getTime(), day1.getTime())
  if (hi <= lo) return null
  const startMin = (lo - day0.getTime()) / 60_000
  const endMin = (hi - day0.getTime()) / 60_000
  const topMin = Math.max(startMin, VISIBLE_START_MIN)
  const botMin = Math.min(endMin, VISIBLE_END_MIN)
  if (botMin <= topMin) return null
  return {
    top: `${((topMin - VISIBLE_START_MIN) / RANGE_MIN) * 100}%`,
    height: `${((botMin - topMin) / RANGE_MIN) * 100}%`,
  }
}

function exceptionsForDay(dateStr: string) {
  return exceptions.value
    .map((ex) => ({ ex, style: blockStyleOnDay(dateStr, ex.start, ex.end) }))
    .filter((x) => x.style !== null) as { ex: ExceptionRow; style: Record<string, string> }[]
}

function bookingsForDay(dateStr: string) {
  return bookings.value
    .map((b) => ({ b, style: blockStyleOnDay(dateStr, b.start, b.end) }))
    .filter((x) => x.style !== null) as { b: BookingRow; style: Record<string, string> }[]
}

function hourLabels() {
  const out: { label: string; pct: number }[] = []
  for (let h = 6; h <= 22; h++) {
    const m = h * 60
    out.push({
      label: `${String(h).padStart(2, '0')}:00`,
      pct: ((m - VISIBLE_START_MIN) / RANGE_MIN) * 100,
    })
  }
  return out
}

async function load() {
  error.value = null
  selectedBooking.value = null
  hoursDraft.value = {}
  try {
    const res = await fetchAdmin(`/schedule?week=${encodeURIComponent(weekLabel.value)}`)
    if (!res.ok) throw new Error('Failed to load schedule')
    const data = (await res.json()) as {
      days: DaySchedule[]
      exceptions: ExceptionRow[]
      bookings: BookingRow[]
    }
    days.value = data.days
    exceptions.value = data.exceptions
    bookings.value = data.bookings
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

async function putDayHours(day: DaySchedule, openMin: number, closeMin: number) {
  const o = snap(openMin)
  const c = snap(closeMin)
  if (c <= o || o < 0 || c > 24 * 60) return
  const res = await fetchAdmin('/schedule', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      day_of_week: day.day_of_week,
      open_time: timeStrFromMinutes(o),
      close_time: timeStrFromMinutes(c),
    }),
  })
  if (!res.ok) {
    error.value = 'Could not save hours'
    return
  }
  await load()
}

async function seedDefaultHours(day: DaySchedule) {
  await putDayHours(day, 9 * 60, 18 * 60)
}

function startResize(ev: PointerEvent, day: DaySchedule, edge: 'open' | 'close') {
  const draft = dayDraft(day)
  if (!draft) return
  const track = (ev.currentTarget as HTMLElement).closest('.day-track') as HTMLElement
  const handleEl = ev.currentTarget as HTMLElement
  if (!track) return
  ev.preventDefault()
  resizeState.value = {
    edge,
    day,
    startY: ev.clientY,
    openMin: draft.open,
    closeMin: draft.close,
    trackHeight: track.clientHeight,
    pointerId: ev.pointerId,
    handleEl,
  }
  handleEl.setPointerCapture(ev.pointerId)
}

function onResizePointerMove(ev: PointerEvent) {
  const st = resizeState.value
  if (!st || ev.pointerId !== st.pointerId) return
  const dy = ev.clientY - st.startY
  const pxPerMin = st.trackHeight / RANGE_MIN
  const dMin = Math.round(dy / pxPerMin)
  let open = st.openMin
  let close = st.closeMin
  if (st.edge === 'open') {
    open = snap(st.openMin + dMin)
    if (open >= close - SNAP_MIN) open = close - SNAP_MIN
  } else {
    close = snap(st.closeMin + dMin)
    if (close <= open + SNAP_MIN) close = open + SNAP_MIN
  }
  hoursDraft.value = { ...hoursDraft.value, [st.day.date]: { open, close } }
}

function yToMinuteInDay(ev: PointerEvent, track: HTMLElement): number {
  const r = track.getBoundingClientRect()
  const y = ev.clientY - r.top
  const ratio = Math.min(1, Math.max(0, y / r.height))
  return VISIBLE_START_MIN + ratio * RANGE_MIN
}

function onTrackPointerDown(ev: PointerEvent, day: DaySchedule) {
  if (resizeState.value) return
  if ((ev.target as HTMLElement).closest('.block-booking, .block-exception, .layer-working, .handle, .seed-btn')) return
  const track = ev.currentTarget as HTMLElement
  selectState.value = {
    dateStr: day.date,
    anchorMin: yToMinuteInDay(ev, track),
    currentMin: yToMinuteInDay(ev, track),
    trackEl: track,
    pointerId: ev.pointerId,
  }
  track.setPointerCapture(ev.pointerId)
}

function onSelectPointerMove(ev: PointerEvent) {
  const st = selectState.value
  if (!st || ev.pointerId !== st.pointerId) return
  st.currentMin = yToMinuteInDay(ev, st.trackEl)
}

function onGlobalPointerUp(ev: PointerEvent) {
  const rs = resizeState.value
  if (rs && ev.pointerId === rs.pointerId) {
    try {
      rs.handleEl.releasePointerCapture(ev.pointerId)
    } catch {
      /* ignore */
    }
    const draft = hoursDraft.value[rs.day.date]
    resizeState.value = null
    if (draft) void putDayHours(rs.day, draft.open, draft.close)
    return
  }

  const st = selectState.value
  if (st && ev.pointerId === st.pointerId) {
    try {
      st.trackEl.releasePointerCapture(ev.pointerId)
    } catch {
      /* ignore */
    }
    const a = snap(Math.min(st.anchorMin, st.currentMin))
    const b = snap(Math.max(st.anchorMin, st.currentMin))
    selectState.value = null
    if (b - a >= SNAP_MIN) {
      const day0 = new Date(`${st.dateStr}T00:00:00`)
      exceptionDialog.value = {
        start: new Date(day0.getTime() + a * 60_000),
        end: new Date(day0.getTime() + b * 60_000),
        dateStr: st.dateStr,
      }
      exceptionComment.value = ''
    }
  }
}

function bindGlobalPointer() {
  window.addEventListener('pointermove', onResizePointerMove)
  window.addEventListener('pointermove', onSelectPointerMove)
  window.addEventListener('pointerup', onGlobalPointerUp)
}

function unbindGlobalPointer() {
  window.removeEventListener('pointermove', onResizePointerMove)
  window.removeEventListener('pointermove', onSelectPointerMove)
  window.removeEventListener('pointerup', onGlobalPointerUp)
}

async function confirmException() {
  const d = exceptionDialog.value
  if (!d) return
  const res = await fetchAdmin('/exceptions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      start: formatLocalDateTime(d.start),
      end: formatLocalDateTime(d.end),
      comment: exceptionComment.value.trim() || null,
    }),
  })
  exceptionDialog.value = null
  if (!res.ok) {
    error.value = 'Could not add exception'
    return
  }
  await load()
}

function formatLocalDateTime(dt: Date): string {
  const y = dt.getFullYear()
  const mo = String(dt.getMonth() + 1).padStart(2, '0')
  const day = String(dt.getDate()).padStart(2, '0')
  const h = String(dt.getHours()).padStart(2, '0')
  const mi = String(dt.getMinutes()).padStart(2, '0')
  const s = String(dt.getSeconds()).padStart(2, '0')
  return `${y}-${mo}-${day}T${h}:${mi}:${s}`
}

async function removeException(id: number) {
  const res = await fetchAdmin(`/exceptions/${id}`, { method: 'DELETE' })
  if (!res.ok) {
    error.value = 'Could not remove exception'
    return
  }
  await load()
}

function selectionPreviewStyle(day: DaySchedule): Record<string, string> | null {
  const st = selectState.value
  if (!st || st.dateStr !== day.date) return null
  const a = Math.min(st.anchorMin, st.currentMin)
  const b = Math.max(st.anchorMin, st.currentMin)
  const topMin = Math.max(a, VISIBLE_START_MIN)
  const botMin = Math.min(b, VISIBLE_END_MIN)
  if (botMin <= topMin) return null
  return {
    top: `${((topMin - VISIBLE_START_MIN) / RANGE_MIN) * 100}%`,
    height: `${((botMin - topMin) / RANGE_MIN) * 100}%`,
  }
}

onMounted(() => {
  void load()
  bindGlobalPointer()
})

onBeforeUnmount(() => {
  unbindGlobalPointer()
})
</script>

<template>
  <main class="page">
    <PageTitle>Weekly calendar</PageTitle>
    <div class="toolbar">
      <button type="button" class="btn" @click="prev">← Prev</button>
      <span class="week">{{ title }}</span>
      <button type="button" class="btn" @click="next">Next →</button>
      <router-link class="link" to="/admin">Dashboard</router-link>
    </div>
    <p class="hint">
      <span class="legend legend-hours">Working hours</span>
      <span class="legend legend-exc">Closed (exception)</span>
      <span class="legend legend-book">Booking</span>
      — Drag top/bottom of green bar to change hours. Drag on empty grid to mark closed time.
    </p>
    <p v-if="error" class="error">{{ error }}</p>

    <div class="grid-wrap">
      <div class="time-gutter">
        <div class="corner" />
        <div class="gutter-inner">
          <span v-for="h in hourLabels()" :key="h.label" class="hour-tick" :style="{ top: h.pct + '%' }">{{
            h.label
          }}</span>
        </div>
      </div>
      <div class="days">
        <div v-for="day in days" :key="day.date" class="day-col">
          <div class="day-head">
            <span class="dow">{{ WEEKDAYS[day.day_of_week] }}</span>
            <span class="dnum">{{ day.date.slice(8) }}</span>
          </div>
          <div
            class="day-track"
            @pointerdown="onTrackPointerDown($event, day)"
          >
            <div class="grid-lines">
              <div v-for="h in hourLabels()" :key="'l' + day.date + h.label" class="grid-line" :style="{ top: h.pct + '%' }" />
            </div>
            <button
              v-if="!day.open_time && !day.close_time"
              type="button"
              class="seed-btn"
              @click.stop="seedDefaultHours(day)"
            >
              Set 9:00–18:00
            </button>
            <div
              v-else
              class="layer-working"
              :class="{ dragging: !!resizeState }"
              :style="workingBarStyle(day) || undefined"
            >
              <div
                class="handle top"
                title="Drag to change open time"
                @pointerdown.stop="startResize($event, day, 'open')"
              />
              <div
                class="handle bottom"
                title="Drag to change close time"
                @pointerdown.stop="startResize($event, day, 'close')"
              />
            </div>
            <div
              v-for="{ ex, style } in exceptionsForDay(day.date)"
              :key="'ex' + ex.id + day.date"
              class="block-exception"
              :style="style"
              :title="ex.comment || 'Closed'"
            />
            <div
              v-for="{ b, style } in bookingsForDay(day.date)"
              :key="'bk' + b.id + day.date"
              class="block-booking"
              :style="style"
              @click.stop="selectedBooking = b"
            >
              {{ b.client_name }}
            </div>
            <div
              v-if="selectionPreviewStyle(day)"
              class="selection-preview"
              :style="selectionPreviewStyle(day) ?? {}"
            />
          </div>
        </div>
      </div>
    </div>

    <section v-if="exceptions.length" class="exc-list card">
      <h2 class="h2">Exceptions this week</h2>
      <ul>
        <li v-for="ex in exceptions" :key="ex.id">
          {{ ex.start.replace('T', ' ').slice(0, 16) }} – {{ ex.end.replace('T', ' ').slice(0, 16) }}
          <span v-if="ex.comment" class="muted">({{ ex.comment }})</span>
          <button type="button" class="btn-mini" @click="removeException(ex.id)">Remove</button>
        </li>
      </ul>
    </section>

    <aside v-if="selectedBooking" class="detail card">
      <h2 class="h2">Booking #{{ selectedBooking.id }}</h2>
      <p><strong>{{ selectedBooking.client_name }}</strong></p>
      <p class="muted">{{ selectedBooking.client_email }}</p>
      <p class="muted">{{ selectedBooking.client_phone }}</p>
      <p>{{ selectedBooking.service_type }} · {{ selectedBooking.location }} · {{ selectedBooking.status }}</p>
      <p class="muted">
        {{ selectedBooking.start.replace('T', ' ').slice(0, 16) }} – {{ selectedBooking.end.replace('T', ' ').slice(0, 16) }}
      </p>
      <button type="button" class="btn secondary" @click="selectedBooking = null">Close</button>
    </aside>

    <div v-if="exceptionDialog" class="modal-backdrop" @click.self="exceptionDialog = null">
      <div class="modal card">
        <h2 class="h2">Mark time as closed</h2>
        <p class="muted">
          {{ formatLocalDateTime(exceptionDialog.start) }} → {{ formatLocalDateTime(exceptionDialog.end) }}
        </p>
        <label class="label">
          Comment (optional)
          <input v-model="exceptionComment" class="input" type="text" />
        </label>
        <div class="modal-actions">
          <button type="button" class="btn secondary" @click="exceptionDialog = null">Cancel</button>
          <button type="button" class="btn" @click="confirmException">Save</button>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.page {
  max-width: 72rem;
  margin: 0 auto;
  padding: 2rem 1.25rem 4rem;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.75rem;
}
.week {
  font-weight: 600;
}
.btn {
  padding: 0.35rem 0.65rem;
  border-radius: 0.35rem;
  border: 1px solid var(--border);
  background: var(--primary);
  color: var(--primary-foreground);
  cursor: pointer;
}
.btn.secondary {
  background: var(--secondary);
  color: var(--secondary-foreground);
}
.btn:hover {
  filter: brightness(1.05);
}
.link {
  margin-left: auto;
  color: var(--color-info);
}
.hint {
  font-size: 0.85rem;
  color: var(--muted-foreground);
  margin: 0 0 1rem;
}
.legend {
  display: inline-block;
  padding: 0.1rem 0.35rem;
  border-radius: 0.25rem;
  margin-right: 0.5rem;
  font-size: 0.8rem;
}
.legend-hours {
  background: color-mix(in srgb, var(--color-success) 35%, transparent);
  border: 1px solid var(--color-success);
}
.legend-exc {
  background: color-mix(in srgb, var(--destructive) 25%, transparent);
  border: 1px solid var(--destructive);
}
.legend-book {
  background: color-mix(in srgb, var(--color-info) 30%, transparent);
  border: 1px solid var(--color-info);
}
.error {
  color: var(--destructive);
}
.grid-wrap {
  display: flex;
  gap: 0.25rem;
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  overflow: hidden;
  background: var(--card);
}
.time-gutter {
  flex: 0 0 3rem;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border);
}
.corner {
  height: 2.5rem;
  border-bottom: 1px solid var(--border);
}
.gutter-inner {
  position: relative;
  flex: 1;
  min-height: 28rem;
}
.hour-tick {
  position: absolute;
  left: 0.15rem;
  transform: translateY(-50%);
  font-size: 0.65rem;
  color: var(--muted-foreground);
  pointer-events: none;
}
.days {
  display: flex;
  flex: 1;
  min-width: 0;
}
.day-col {
  flex: 1;
  min-width: 0;
  border-right: 1px solid var(--border);
}
.day-col:last-child {
  border-right: none;
}
.day-head {
  height: 2.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--border);
  font-size: 0.8rem;
}
.dow {
  font-weight: 600;
}
.dnum {
  color: var(--muted-foreground);
}
.day-track {
  position: relative;
  min-height: 28rem;
  cursor: crosshair;
  touch-action: none;
}
.grid-lines {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.grid-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 1px;
  background: color-mix(in srgb, var(--border) 70%, transparent);
}
.seed-btn {
  position: absolute;
  left: 50%;
  top: 45%;
  transform: translate(-50%, -50%);
  z-index: 2;
  font-size: 0.75rem;
  padding: 0.35rem 0.5rem;
  border-radius: 0.35rem;
  border: 1px dashed var(--border);
  background: var(--background);
  cursor: pointer;
}
.layer-working {
  position: absolute;
  left: 4px;
  right: 4px;
  border-radius: 0.25rem;
  background: color-mix(in srgb, var(--color-success) 40%, transparent);
  border: 2px solid var(--color-success);
  z-index: 1;
  box-sizing: border-box;
}
.layer-working.dragging {
  opacity: 0.95;
}
.handle {
  position: absolute;
  left: 0;
  right: 0;
  height: 10px;
  cursor: ns-resize;
  z-index: 3;
}
.handle.top {
  top: -2px;
}
.handle.bottom {
  bottom: -2px;
}
.block-exception {
  position: absolute;
  left: 6px;
  right: 6px;
  border-radius: 0.2rem;
  background: repeating-linear-gradient(
    -45deg,
    color-mix(in srgb, var(--destructive) 35%, transparent),
    color-mix(in srgb, var(--destructive) 35%, transparent) 6px,
    color-mix(in srgb, var(--destructive) 18%, transparent) 6px,
    color-mix(in srgb, var(--destructive) 18%, transparent) 12px
  );
  border: 1px solid var(--destructive);
  z-index: 2;
  pointer-events: none;
}
.block-booking {
  position: absolute;
  left: 8px;
  right: 8px;
  border-radius: 0.2rem;
  background: color-mix(in srgb, var(--color-info) 45%, transparent);
  border: 1px solid var(--color-info);
  z-index: 3;
  font-size: 0.65rem;
  padding: 2px 4px;
  overflow: hidden;
  cursor: pointer;
  pointer-events: auto;
}
.selection-preview {
  position: absolute;
  left: 10px;
  right: 10px;
  border-radius: 0.2rem;
  background: color-mix(in srgb, var(--primary) 20%, transparent);
  border: 1px dashed var(--primary);
  z-index: 4;
  pointer-events: none;
}
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1rem 1.25rem;
  margin-top: 1.25rem;
}
.h2 {
  font-size: 1.05rem;
  margin: 0 0 0.5rem;
}
.exc-list ul {
  margin: 0;
  padding-left: 1.1rem;
  font-size: 0.9rem;
}
.btn-mini {
  margin-left: 0.5rem;
  font-size: 0.75rem;
  padding: 0.15rem 0.4rem;
  border-radius: 0.25rem;
  border: 1px solid var(--border);
  background: var(--background);
  cursor: pointer;
}
.detail {
  max-width: 24rem;
}
.muted {
  color: var(--muted-foreground);
}
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgb(0 0 0 / 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 1rem;
}
.modal {
  max-width: 22rem;
  width: 100%;
}
.label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin: 0.75rem 0;
  font-size: 0.9rem;
}
.input {
  padding: 0.45rem 0.5rem;
  border: 1px solid var(--border);
  border-radius: 0.35rem;
  background: var(--background);
}
.modal-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 0.75rem;
}
</style>
