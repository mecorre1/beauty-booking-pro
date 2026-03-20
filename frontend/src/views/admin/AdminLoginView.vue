<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { loginAdmin, setAdminToken } from '../../api/admin'
import PageTitle from '../../components/shared/PageTitle.vue'

const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const error = ref<string | null>(null)
const busy = ref(false)

async function submit() {
  error.value = null
  busy.value = true
  try {
    const token = await loginAdmin(email.value.trim(), password.value)
    setAdminToken(token)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/admin'
    await router.push(redirect)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Login failed'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="page">
    <PageTitle>Admin sign in</PageTitle>
    <p v-if="error" class="error">{{ error }}</p>
    <form class="form card" @submit.prevent="submit">
      <label class="label">
        Email
        <input v-model="email" class="input" type="email" required autocomplete="username" />
      </label>
      <label class="label">
        Password
        <input v-model="password" class="input" type="password" required autocomplete="current-password" />
      </label>
      <button class="btn" type="submit" :disabled="busy">Sign in</button>
    </form>
  </main>
</template>

<style scoped>
.page {
  max-width: 28rem;
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
  font-size: 0.9rem;
}
.input {
  padding: 0.5rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.35rem;
}
.btn {
  margin-top: 0.25rem;
  padding: 0.55rem 1rem;
  border-radius: 0.35rem;
  border: none;
  background: #0f172a;
  color: #fff;
  cursor: pointer;
}
.error {
  color: #b91c1c;
  margin-bottom: 0.5rem;
}
</style>
