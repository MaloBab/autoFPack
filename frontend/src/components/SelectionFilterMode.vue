<script setup lang="ts">
import { defineEmits, defineProps } from 'vue'

const props = defineProps<{
  modelValue: 'all' | 'selected' | 'unselected'
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: 'all' | 'selected' | 'unselected'): void
}>()

const modes: ('all' | 'selected' | 'unselected')[] = ['all', 'selected', 'unselected']

function toggleMode() {
  const currentIndex = modes.indexOf(props.modelValue)
  const nextIndex = (currentIndex + 1) % modes.length
  emit('update:modelValue', modes[nextIndex])
}

function setMode(mode: 'all' | 'selected' | 'unselected') {
  emit('update:modelValue', mode)
}


</script>

<template>
  <div class="filter-mode-buttons">
    <button @click="toggleMode()">{{props.modelValue}}</button>
  </div>
</template>

<style scoped>
.filter-mode-buttons {
  display: flex;
  gap: 0.5rem;
  margin:  1%;
  margin-bottom: 0.5rem;
}
button {
  background-color: #2563eb;
  color: white;
  margin-left: 2%;
  font-weight: 500;
  font-size: 1rem;
  padding: 0.6rem 1.2rem;
  border-radius: 0.375rem;
  cursor: pointer;
  border: none;
}
button:hover {
  background-color: #1040e8;
}
</style>
