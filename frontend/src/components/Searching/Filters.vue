<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { onClickOutside } from '@vueuse/core'

const props = defineProps<{
  column: string
  values: any[]
  selected: Set<any>
  labels?: Record<any, string>
}>()

const emit = defineEmits<{
  (e: 'filter-change', column: string, newSet: Set<any>): void,
  (e: 'sort-change', column: string, order: 'asc' | 'desc' | null): void
}>()

const dropdownOpen = ref(false)
const localSelections = ref<Set<any>>(new Set(props.values))
const container = ref(null)
const sortOrder = ref<'asc' | 'desc' | null>(null)

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

const isFilterOrSortActive = computed(() => {
  return localSelections.value.size !== props.values.length || sortOrder.value !== null
})

function onSortClick(order: 'asc' | 'desc') {
  if (sortOrder.value === order) {
    sortOrder.value = null
  } else {
    sortOrder.value = order
  }
  emit('sort-change', props.column, sortOrder.value)
}
</script>

<template>
  <div class="searcher" ref="container">
    <button class="filter-icon" :class="{ 'active-filter': isFilterOrSortActive }" @click="dropdownOpen = !dropdownOpen" type="button">
      <img src="../../assets/filtre.png" alt="filtrer" class="filter-img" />
    </button>
    <div v-if="dropdownOpen" class="dropdown">
      <div class="dropdown-actions">
        <button @click="checkAll">Cocher tout</button>
        <button @click="uncheckAll">Décocher tout</button>
      </div>
      <div class="dropdown-actions">
        <button
          :class="{ active: sortOrder === 'asc' }"
          @click="onSortClick('asc')"
        > A-Z</button>
        <button
          :class="{ active: sortOrder === 'desc' }"
          @click="onSortClick('desc')"
        > Z-A</button>
      </div>
      <div class="dropdown-values">
        <label v-for="val in props.values" :key="val">
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

.filter-icon.active-filter .filter-img {
  filter: invert(35%) sepia(86%) saturate(2920%) hue-rotate(199deg) brightness(92%) contrast(89%);
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
  gap: 0.5rem; 
  margin: 0 0.25rem 0.5rem 0.25rem; 
}

.dropdown-actions button {
  flex: 1 1 0; 
  background-color: #464646;
  border: none;
  border-radius: 4px;
  padding: 0.4rem 0.6rem;
  font-size: 0.8rem;
  cursor: pointer;
  color: white;
  transition: background-color 0.2s, border-color 0.2s;
  text-align: center;
}

.dropdown-actions button.active {
  background-color: #0092ff;
}

.dropdown-actions button:hover {
  background-color: #313131;
}

.dropdown-actions button:focus {
  outline: none;
}

.dropdown-values {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
</style>
