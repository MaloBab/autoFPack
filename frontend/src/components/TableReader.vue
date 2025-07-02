<script setup lang="ts">
import { computed, defineEmits, defineProps } from 'vue'
import { useTableReader } from '../composables/useTableReader'
import Searcher from './Searcher.vue'
import { ref, watch } from 'vue'

const scrollContainer = ref<HTMLElement | null>(null)

const props = defineProps<{
  tableName: string
  apiUrl?: string
  ajouter?: boolean
}>()
const emit = defineEmits(['added', 'cancelled'])

const {
  columns, rows, newRow, editingId, editRow, fournisseurs,
  validateAdd, cancelAdd, startEdit, validateEdit, cancelEdit, deleteRow
} = useTableReader(props, emit)

const filters = ref<Record<string, Set<any>>>({})

// Valeurs distinctes pour chaque colonne
const columnValues = computed(() => {
  const map: Record<string, Set<any>> = {}
  for (const row of rows.value) {
    for (const col of columns.value) {
      map[col] ??= new Set()
      map[col].add(row[col])
    }
  }
  return map
})

// Filtrage
const filteredRows = computed(() =>
  rows.value.filter(row =>
    columns.value.every(col =>
      !filters.value[col] || filters.value[col].has(row[col])
    )
  )
)

function updateFilter(col: string, values: Set<any>) {
  filters.value[col] = values
}

watch(() => props.ajouter, (val) => {
  if (val && scrollContainer.value) {
    scrollContainer.value.scrollTop = 0
  }
})

const valueLabels = computed(() => {
  const map: Record<string, Record<any, string>> = {}

  if (props.tableName === 'produits') {
    map['fournisseur_id'] = Object.fromEntries(
      fournisseurs.value.map(f => [f.id, f.nom])
    )
  }

  return map
})

</script>


<template>
  <div class="table-container">
    <!-- Table pour l'en-tête, non scrollable -->
    <table class="table-head">
      <thead>
        <tr>
          <th v-for="col in columns" :key="col">
            <div style="display: flex; align-items: center; gap: 0.3rem;">
              <span>
                <template v-if="col === 'fournisseur_id' && props.tableName === 'produits'">fournisseur</template>
                <template v-else>{{ col }}</template>
              </span>
              <Searcher
                :column="col"
                :values="[...columnValues[col] || []]"
                :selected="filters[col] || new Set([...columnValues[col] || []])"
                :labels="valueLabels[col]"
                @filter-change="updateFilter"
              />
            </div>
          </th>
          <th>Actions</th>
        </tr>
      </thead>
    </table>
    <div class="table-body-scroll" ref="scrollContainer">
      <table>
        <tbody>
          <tr v-if="ajouter">
            <td v-for="col in columns" :key="col">
              <template v-if="col === 'fournisseur_id' && props.tableName === 'produits'">
                <select v-model="newRow.fournisseur_nom">
                  <option v-for="f in fournisseurs" :key="f.id" :value="f.nom">{{ f.nom }}</option>
                </select>
              </template>
              <template v-else-if="col !== 'id'">
                <input v-model="newRow[col]" @keyup.enter="validateAdd" />
              </template>
            </td>
            <td class="actions">
              <button @click="validateAdd">✅</button>
              <button @click="cancelAdd">❌</button>
            </td>
          </tr>
          <tr v-for="row in filteredRows" :key="row.id">
            <td v-for="col in columns" :key="col">
              <template v-if="editingId === row.id && col === 'fournisseur_id' && props.tableName === 'produits'">
                <select v-model="editRow.fournisseur_nom" @keyup.enter="validateEdit(row.id)">
                  <option v-for="f in fournisseurs" :key="f.id" :value="f.nom">{{ f.nom }}</option>
                </select>
              </template>
              <template v-else-if="editingId === row.id && col !== 'id'">
                <input v-model="editRow[col]" @keyup.enter="validateEdit(row.id)" />
              </template>
              <template v-else-if="col === 'fournisseur_id' && props.tableName === 'produits'">
                {{ fournisseurs.find(f => f.id === row.fournisseur_id)?.nom || row.fournisseur_id }}
              </template>
              <template v-else>
                {{ row[col] }}
              </template>
            </td>
            <td class="actions">
              <template v-if="editingId === row.id">
                <button @click="validateEdit(row.id)">✅</button>
                <button @click="cancelEdit">❌</button>
              </template>
              <template v-else>
                <button title="Éditer" @click="startEdit(row)">✏️</button>
                <button title="Supprimer" @click="deleteRow(row.id)">🗑️</button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.add-btn {
  margin-bottom: 1rem;
  background: #2563eb;
  color: #fff;
  border: none;
  padding: 0.5rem 1.2rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}
.add-btn:hover {
  background: #1d4ed8;
}

/* Conteneur principal du tableau */
.table-container {
  width: 100%;
  background: #f7f7f7;
}

/* Table d'en-tête (fixe) */
.table-head {
  width: 90%;
  margin-top: 3%;
  margin-left: 2%;
  min-width: 80%;
  border-collapse: separate;
  border-spacing: 0;
  background: white;
  font-family: inherit;
  border-radius: 1.5%;
  table-layout: fixed;
}

/* Corps scrollable */
.table-body-scroll {
  width: 90%;
  margin-left: 2%;
  max-height: 40vh;
  overflow-y: auto;
  background: white;
  scrollbar-width: thin;
  scrollbar-color: #b3b3b3 #f3f4f6;
}

.table-body-scroll::-webkit-scrollbar {
  width: 10px;
  height: 10px;
  background: #f3f4f6;
  border-radius: 8px;
}
.table-body-scroll::-webkit-scrollbar-thumb {
  background: #b3b3b3;
  border-radius: 8px;
}
.table-body-scroll::-webkit-scrollbar-thumb:hover {
  background: #4d4e4f;
}

/* Table du corps */
.table-body-scroll table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: white;
  font-family: inherit;
  table-layout: fixed;
}

th, td {
  padding: 0.75rem 1rem;
  text-align: left;
}

th {
  font-weight: 600;
  color: #222;
  background: #eaeaea;
  border-bottom: 1px solid #e5e7eb;
}

tbody tr {
  border-bottom: 1px solid #e5e7eb;
}

tbody tr:last-child {
  border-bottom: none;
}

td {
  vertical-align: middle;
  font-size: 1rem;
  color: #222;
}

.actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.actions button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-size: 1.5rem; 
  color: #222;
}

.actions button:hover {
  color: #2563eb;
}

input, select {
  border: 1px solid #bbb;
  border-radius: 4px;
  padding: 0.3rem 0.5rem;
  font-size: 1rem;
  font-family: inherit;
  background: #f9fafb;
  color: #222;
  outline: none;
  transition: border 0.2s;
  width: 100%;
  min-width: 60px;
  max-width: 200px;
}
input:focus, select:focus {
  border: 1.5px solid #2563eb;
  background: #fff;
}
</style>