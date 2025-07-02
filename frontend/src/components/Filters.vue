<script setup lang="ts">
import { ref, watch } from 'vue'
import { onClickOutside } from '@vueuse/core'

const props = defineProps<{
  column: string
  values: any[]
  selected: Set<any>
  labels?: Record<any, string>
}>()

const emit = defineEmits<{
  (e: 'filter-change', column: string, newSet: Set<any>): void
}>()

const dropdownOpen = ref(false)
const localSelections = ref<Set<any>>(new Set(props.values))
const container = ref(null)

onClickOutside(container, () => {
  dropdownOpen.value = false
})

watch(() => props.selected, (newSelected) => {
  localSelections.value = new Set([...newSelected])
}, { immediate: true })



function toggleValue(val: any) {
  if (localSelections.value.has(val)) {
    localSelections.value.delete(val)
  } else {
    localSelections.value.add(val)
  }
  emit('filter-change', props.column, new Set(localSelections.value))
}

function checkAll() {
  localSelections.value = new Set(props.values)
  emit('filter-change', props.column, new Set(localSelections.value))
}

function uncheckAll() {
  localSelections.value = new Set()
  emit('filter-change', props.column, new Set())
}
</script>

<template>
  <div class="searcher" ref="container">
    <button class="filter-icon" @click="dropdownOpen = !dropdownOpen">
      <img src="../assets/filtre.png" alt="filtrer" class="filter-img" />
    </button>
    <div v-if="dropdownOpen" class="dropdown">
      <div class="dropdown-actions">
        <button @click="checkAll">Cocher tout</button>
        <button @click="uncheckAll">Décocher tout</button>
      </div>
      <div class="dropdown-values">
        <label v-for="val in values" :key="val">
        <input
            type="checkbox"
            :checked="localSelections.has(val)"
            @change="() => toggleValue(val)"
        />
        {{ props.labels?.[val] ?? val }}
        </label>
      </div>
    </div>
  </div>
</template>

<style scoped>
.searcher {
  position: relative;
  display: inline-block;
}

.filter-icon {
  background: none;
  border: none;
  cursor: pointer;
  margin-top: 20%;
  padding: 3%;
  border-radius: 3%;
  transition: background-color 0.2s;
}

.filter-img {
  width: 1.6vw;
  height: 1.6vw;
  background-color: transparent;
}
.filter-icon:hover .filter-img {
  filter: invert(34%) sepia(87%) saturate(1535%) hue-rotate(203deg) brightness(95%) contrast(90%);
}
.filter-icon:focus {
  outline: none;
}

.dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  background: white;
  border: 1px solid #ccc;
  border-radius: 6px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  padding: 0.5rem;
  z-index: 1000;
  min-width: 180px;
  max-height: 300px;
  overflow-y: auto;
}
.dropdown-actions {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}
.dropdown-values {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}


.dropdown-actions button {
  background-color: #464646;
  margin-left: 0.2rem;
  border: none;
  border-radius: 4px;
  padding: 0.2rem 0.2rem;
  font-size: 0.80rem;
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s;
}

.dropdown-actions button:hover {
    background-color: #313131;
}


.dropdown-actions button:focus {
  outline: none;
}

</style>