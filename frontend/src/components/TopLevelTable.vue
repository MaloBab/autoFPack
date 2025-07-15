<script setup lang="ts">
import { computed, defineEmits, defineProps, ref, watch } from 'vue'
import { useTableReader } from '../composables/useTableReader'
import Filters from './Filters.vue'
import { useRouter } from 'vue-router'

const scrollContainer = ref<HTMLElement | null>(null)

const props = defineProps<{
  tableName: string
  apiUrl?: string
  ajouter?: boolean
  search?: string
}>()
const emit = defineEmits(['added', 'cancelled'])
const router = useRouter()

const filters = ref<Record<string, Set<any>>>({})
const {
  columns, rows, newRow, editingId, editRow, fournisseurs, clients,
  validateAdd, cancelAdd, startEdit, validateEdit, cancelEdit, deleteRow, duplicateRow, ExportRow, ExportAll, isExporting
} = useTableReader(props, emit, filters)

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

const filteredRows = computed(() =>
  rows.value
    .filter(row =>
      columns.value.every(col =>
        !filters.value[col] || filters.value[col].has(row[col])
      )
    )
    .filter(row => {
      if (!props.search) return true
      const search = props.search.toLowerCase()
      return columns.value.some(col => {
        let cellValue = row[col]

        if (props.tableName === 'fpacks' && col === 'client') {
          const client = clients.value.find(c => c.id === cellValue)
          cellValue = client?.nom || ''
        }

        return String(cellValue).toLowerCase().includes(search)
      })
    })
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

  if (props.tableName === 'fpacks') {
    map['client'] = Object.fromEntries(
      clients.value.map(c => [c.id, c.nom])
    )
  }

  return map
})

function remplirEquipement(row: any) {
  router.push(`/remplir/${props.tableName}/${row.id}`)
}
function remplirFPack(row: any) {
  router.push(`/configure/${props.tableName}/${row.id}`)
}
</script>

<template>
  <button v-if="props.tableName === 'fpacks'" @click="ExportAll" :disabled="isExporting" class="ExportAll">
    Tout exporter
    <span v-if="isExporting" class="loader"></span>
  </button>
  <div class="table-container">
    <table class="table-head">
      <thead>
        <tr>
          <th v-for="col in columns" :key="col">
            <div style="display: flex; align-items: center; gap: 0.3rem;">
              <span>{{ col }}</span>
              <Filters
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
              <template v-if="col === 'client' && props.tableName === 'fpacks'">
                <select v-model="newRow.client_nom">
                  <option v-for="c in clients" :key="c.id" :value="c.nom">{{ c.nom }}</option>
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

              <template v-if="editingId === row.id && col === 'client' && props.tableName === 'fpacks'">
                <select v-model="editRow.client_nom" @keyup.enter="validateEdit(row.id)">
                  <option v-for="c in clients" :key="c.id" :value="c.nom">{{ c.nom }}</option>
                </select>
              </template>

              <template v-else-if="editingId === row.id && col !== 'id'">
                <input v-model="editRow[col]" @keyup.enter="validateEdit(row.id)" />
              </template>
              <template v-else-if="col === 'client' && props.tableName === 'fpacks'">
                {{ clients.find(c => c.id === row.client)?.nom || row.client }}
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
                <span v-if="props.tableName === 'equipements'">
                  <button title="Remplir" @click="remplirEquipement(row)">🗂️</button>
                </span>
                <span v-if="props.tableName === 'fpacks'">
                  <button title="Remplir" @click="remplirFPack(row)">🛠️</button>
                </span>
                <span v-if="props.tableName === 'fpacks'">
                  <button title="Dupliquer" @click="duplicateRow(row)">🔁</button>
                </span>
                <span v-if="props.tableName === 'fpacks'">
                  <button title="Dupliquer" @click="ExportRow(row)">📤</button>
                </span>
                
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

.table-container {
  width: 100%;
  background: #f7f7f7;
}

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
  gap: 0.6rem;
  align-items: center;
}

.actions button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-size: 1.2rem; 
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

.ExportAll {
  background-color: #4CAF50;
  color: white;
  margin-left: 2%;
  margin-top: 1%;
  padding: 10px 20px;
  font-size: 16px;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.ExportAll:hover {
  background-color: #45a049;
  transform: scale(1.03);
}

.ExportAll:active {
  background-color: #3e8e41;
  transform: scale(0.98);
}

.loader {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #09d871;
  border-radius: 50%;
  width: 14px;
  height: 14px;
  animation: spin 1s linear infinite;
  display: inline-block;
  margin-left: 8px;
  vertical-align: middle;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

</style>