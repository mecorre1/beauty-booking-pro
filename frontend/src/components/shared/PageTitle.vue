<script setup lang="ts">
defineProps<{ tag?: string }>()
</script>

<template>
  <component :is="tag ?? 'h1'" class="title">
    <slot />
  </component>
</template>

<style scoped>
.title {
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin: 0;
}
</style>
