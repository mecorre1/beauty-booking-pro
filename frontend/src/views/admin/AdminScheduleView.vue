<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchAdmin } from '../../api/admin'
import PageTitle from '../../components/shared/PageTitle.vue'
import { isoWeekLabel } from '../../utils/isoWeek'

type TemplateRow = { id: number; name: string; slots: { id: number; day_of_week: number; start_time: string; duration_minutes: number }[] }

const templates = ref<TemplateRow[]>([])
const name = ref('Standard week')
const week = ref(isoWeekLabel(new Date()))
const templateId = ref<number | null>(null)
const error = ref<string | null>(null)
const message = ref<string | null>(null)

async function load() {
  error.value = null
  try {
    const res = await fetchAdmin('/schedule/templates')
    if (!res.ok) throw new Error('Failed to load templates')
    templates.value = (await res.json()) as TemplateRow[]
    if (templates.value.length && templateId.value == null) {
      templateId.value = templates.value[0].id
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Error'
  }
}

async function createTemplate() {
  error.value = null
  message.value = null
  try {
    const res = await fetchAdmin('/schedule/templates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name.value,
        slots: [
          { day_of_week: 0, start_time: '09:00', duration_minutes: 60 },
          { day_of_week: 2, start_time: '10:00', duration_minutes: 60 },
        ],
      }),
    })
    if (!res.ok) throw new Error('Create failed')
    await load()
    message.value = 'Template created.'
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Error'
  }
}

async function apply() {
  error.value = null
  message.value = null
  if (templateId.value == null) return
  try {
    const res = await fetchAdmin('/schedule/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ template_id: templateId.value, week: week.value }),
    })
    if (!res.ok) throw new Error('Apply failed')
    const data = (await res.json()) as { slots_created: number }
    message.value = `Applied: ${data.slots_created} slot(s).`
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
    <PageTitle>Schedule templates</PageTitle>
    <p><router-link class="link" to="/admin">← Dashboard</router-link></p>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="message" class="ok">{{ message }}</p>
    <section class="card">
      <h2 class="h2">Templates</h2>
      <ul class="list">
        <li v-for="t in templates" :key="t.id">{{ t.name }} ({{ t.slots.length }} rules)</li>
        <li v-if="!templates.length" class="muted">No templates yet.</li>
      </ul>
      <button type="button" class="btn secondary" @click="createTemplate">Create demo template</button>
    </section>
    <section class="card">
      <h2 class="h2">Apply to week</h2>
      <label class="label">
        Template
        <select v-model="templateId" class="input">
          <option v-for="t in templates" :key="t.id" :value="t.id">{{ t.name }}</option>
        </select>
      </label>
      <label class="label">
        Week (YYYY-WW)
        <input v-model="week" class="input" />
      </label>
      <button type="button" class="btn" :disabled="templateId == null" @click="apply">Apply</button>
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
  background: #f8fafc;
  border-radius: 0.5rem;
  padding: 1rem 1.25rem;
  margin-bottom: 1rem;
}
.h2 {
  font-size: 1.05rem;
  margin: 0 0 0.5rem;
}
.list {
  margin: 0 0 0.75rem;
  padding-left: 1.2rem;
}
.muted {
  color: #64748b;
}
.label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
}
.input {
  padding: 0.5rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.35rem;
}
.btn {
  padding: 0.55rem 1rem;
  border-radius: 0.35rem;
  border: none;
  background: #0f172a;
  color: #fff;
  cursor: pointer;
}
.btn.secondary {
  background: #334155;
}
.error {
  color: #b91c1c;
}
.ok {
  color: #15803d;
}
.link {
  color: #2563eb;
}
</style>
