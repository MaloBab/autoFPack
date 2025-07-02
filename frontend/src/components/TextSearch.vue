<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: string): void
}>()

const searchInput = ref(props.modelValue)

watch(searchInput, (val) => {
  emit('update:modelValue', val)
})
watch(() => props.modelValue, (val) => {
  if (val !== searchInput.value) searchInput.value = val
})
</script>

<template>
  <div class="search-bar">
    <input
      type="text"
      v-model="searchInput"
      placeholder="🔍 Recherche"
    />
  </div>
</template>

<style scoped>
.search-bar {
  margin: 1rem 2%;
  width: 20%;
}

input {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 1rem;
  background-color: #bbbbbb;
}
</style>
