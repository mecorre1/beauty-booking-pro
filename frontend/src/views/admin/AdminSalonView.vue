<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchAdmin } from '../../api/admin'
import PageTitle from '../../components/shared/PageTitle.vue'

const name = ref('')
const address = ref('')
const phone = ref('')
const email = ref('')
const error = ref<string | null>(null)
const saved = ref(false)

async function load() {
  error.value = null
  try {
    const res = await fetchAdmin('/salon')
    if (!res.ok) throw new Error('Failed to load salon')
    const s = (await res.json()) as { name: string; address: string; phone: string; email: string }
    name.value = s.name
    address.value = s.address
    phone.value = s.phone
    email.value = s.email
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Error'
  }
}

async function save() {
  error.value = null
  saved.value = false
  try {
    const res = await fetchAdmin('/salon', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name.value,
        address: address.value,
        phone: phone.value,
        email: email.value,
      }),
    })
    if (!res.ok) throw new Error('Save failed')
    saved.value = true
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
    <PageTitle>Salon</PageTitle>
    <p><router-link class="link" to="/admin">← Dashboard</router-link></p>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="saved" class="ok">Saved.</p>
    <form class="form card" @submit.prevent="save">
      <label class="label">Name <input v-model="name" class="input" required /></label>
      <label class="label">Address <input v-model="address" class="input" required /></label>
      <label class="label">Phone <input v-model="phone" class="input" required /></label>
      <label class="label">Email <input v-model="email" class="input" type="email" required /></label>
      <button class="btn" type="submit">Save</button>
    </form>
  </main>
</template>

<style scoped>
.page {
  max-width: 40rem;
  margin: 0 auto;
  padding: 2rem 1.25rem;
}
.card {
  background: #f8fafc;
  border-radius: 0.5rem;
  padding: 1rem 1.25rem;
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
