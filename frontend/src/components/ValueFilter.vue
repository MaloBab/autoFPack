<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = defineProps<{
  columns: string[]
  rows: any[]
  filters: Record<string, string[]>
}>()
const emit = defineEmits(['update:filters'])

const showMenu = ref(false)
const openCol = ref<string | null>(null)

function getValues(col: string) {
  return [...new Set(props.rows.map(r => r[col]).filter(v => v !== undefined && v !== null && v !== ''))]
}

function toggle(col: string, val: string) {
  const arr = props.filters[col] ? [...props.filters[col]] : []
  const idx = arr.indexOf(val)
  if (idx === -1) arr.push(val)
  else arr.splice(idx, 1)
  emit('update:filters', { ...props.filters, [col]: arr })
}

function reset() {
  const reset: Record<string, string[]> = {}
  props.columns.forEach(c => { reset[c] = [] })
  emit('update:filters', reset)
}
</script>

<template>
  <div class="filter-container">
    <button class="filter-btn" @click="showMenu = !showMenu">🔍 Filtrer</button>
    <div v-if="showMenu" class="filter-menu" @mouseleave="showMenu = false">
      <ul>
        <li v-for="col in columns" :key="col" @mouseenter="openCol = col" @mouseleave="openCol = null">
          <span>{{ col }}</span>
          <div v-if="openCol === col" class="submenu">
            <div v-for="val in getValues(col)" :key="val" class="submenu-option">
              <label>
                <input type="checkbox"
                  :value="val"
                  :checked="filters[col]?.includes(val)"
                  @change="toggle(col, val)"
                />
                {{ val }}
              </label>
            </div>
          </div>
        </li>
      </ul>
      <button class="reset-btn" @click="reset">Réinitialiser</button>
    </div>
  </div>
</template>


<style scoped>
.filter-container {
  position: relative;
  display: inline-block;
  margin-top: 1em;
}
.filter-btn {
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 0.4em 1em;
  font-weight: 600;
  cursor: pointer;
}
.filter-menu {
  position: absolute;
  left: 0;
  top: 2.2em;
  background: #fff;
  border: 1px solid #bbb;
  border-radius: 6px;
  box-shadow: 0 2px 8px #0002;
  z-index: 20;
  min-width: 180px;
  padding: 0.5em 0.7em;
}
.filter-menu ul {
  list-style: none;
  margin: 0;
  padding: 0;
}
.filter-menu li {
  position: relative;
  padding: 0.2em 0.5em;
  cursor: pointer;
}
.submenu {
  position: absolute;
  left: 100%;
  top: 0;
  background: #fff;
  border: 1px solid #bbb;
  border-radius: 6px;
  box-shadow: 0 2px 8px #0002;
  min-width: 140px;
  z-index: 30;
  padding: 0.5em 0.7em;
}
.submenu-option {
  margin-bottom: 0.2em;
}
.reset-btn {
  margin-top: 0.5em;
  background: #bbb;
  color: #222;
  border: none;
  border-radius: 4px;
  padding: 0.2em 0.7em;
  cursor: pointer;
  font-size: 0.95em;
}
</style>