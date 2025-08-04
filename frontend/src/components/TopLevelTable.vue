<script setup lang="ts">
import { computed, defineEmits, defineProps, reactive, ref, watch } from 'vue'
import { useTableReader } from '../composables/useTableReader'
import Filters from './Filters.vue'
import { useRouter } from 'vue-router'
import AutoComplete from '../components/AutoCompleteInput.vue'
import SearchSelect from '../components/SearchSelect.vue'

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
  columns, rows, newRow, editingId, editRow, fournisseurs, clients,fpacks,
  validateAdd, cancelAdd, startEdit, validateEdit, cancelEdit, deleteRow, duplicateRow, ExportRow
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

        if ((props.tableName === 'projets' ||props.tableName === 'fpacks') && col === 'client') {
          const client = clients.value.find(c => c.id === cellValue)
          cellValue = client?.nom || ''
        }

        if (props.tableName === 'projets' && col === 'fpack_id') {
          const fpack = fpacks.value.find(f => f.id === cellValue)
          cellValue = fpack?.nom || ''
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

  if (props.tableName === 'fpacks' || props.tableName === 'projets') {
    map['client'] = Object.fromEntries(
      clients.value.map(c => [c.id, c.nom])
    )
  }

  if (props.tableName === 'projets') {
    map['fpack'] = Object.fromEntries(
      fpacks.value.map(f => [f.id, f.nom])
    )
  }
  return map
})

const orderedColumns = computed(() => {
  if (!columns.value) return []
  const cols = columns.value.filter(col => col.toLowerCase() !== 'id' && col.toLowerCase() !== 'reference')
  if (columns.value.some(col => col.toLowerCase() === 'reference')) {cols.unshift('reference')}
  return cols
})


const sortOrders = reactive<Record<string, 'asc' | 'desc' | null>>({})

function onSortChange(column: string, order: 'asc' | 'desc' | null) {
  sortOrders[column] = order
}

const filteredAndSortedRows = computed(() => {
  let result = filteredRows.value.slice()

  for (const [col, order] of Object.entries(sortOrders)) {
    if (order) {
      result.sort((a, b) => {
        const valA = a[col]
        const valB = b[col]
        if (typeof valA === 'string' && typeof valB === 'string') {
          return order === 'asc'
            ? valA.localeCompare(valB)
            : valB.localeCompare(valA)
        }
        if (typeof valA === 'number' && typeof valB === 'number') {
          return order === 'asc' ? valA - valB : valB - valA
        }
        return 0
      })
    }
  }

  return result
})

function remplirEquipement(row: any) {
  router.push(`/remplir/${props.tableName}/${row.id}`)
}
function remplirFPack(row: any) {
  router.push(`/configure/${props.tableName}/${row.id}`)
}
function remplirProjet(row: any) {
  router.push(`/complete/${props.tableName}/${row.id}`)
}


const filteredFpacks = computed(() => {
  if (newRow.value.client_nom) {
    const client = clients.value.find(c => c.nom === newRow.value.client_nom)
    if (client) {
      return fpacks.value.filter(f => f.client === client.id)
    }
  }
  return fpacks.value
})

watch(() => newRow.value.client_nom, (clientNom) => {
  if (!clientNom) {
    newRow.value.fpack_nom = ''
  } else {
    const client = clients.value.find(c => c.nom === clientNom)
    const fpack = fpacks.value.find(f => f.nom === newRow.value.fpack_nom)
    if (fpack && client && fpack.client !== client.id) {
      newRow.value.fpack_nom = ''
    }
  }
})

watch(() => newRow.value.fpack_nom, (fpackNom) => {
  if (!fpackNom) {
    return
  }
  const fpack = fpacks.value.find(f => f.nom === fpackNom)
  if (fpack) {
    const client = clients.value.find(c => c.id === fpack.client)
    if (client && newRow.value.client_nom !== client.nom) {
      newRow.value.client_nom = client.nom
    }
  }
})


watch(() => props.ajouter, (val) => {
  if (val) {
    if (!newRow.value.client_nom || !clients.value.some(c => c.nom === newRow.value.client_nom)) {
      if (clients.value.length > 0) {
        newRow.value.client_nom = clients.value[0].nom
      }
    }

    const fpacksForClient = fpacks.value.filter(f => {
      const client = clients.value.find(c => c.id === f.client)
      return client && client.nom === newRow.value.client_nom
    })
    if (!newRow.value.fpack_nom || !fpacksForClient.some(f => f.nom === newRow.value.fpack_nom)) {
      if (fpacksForClient.length > 0) {
        newRow.value.fpack_nom = fpacksForClient[0].nom
      } else {
        newRow.value.fpack_nom = ''
      }
    }
  }
})


const filteredFpacksEdit = computed(() => {
  if (editRow.value.client_nom) {
    const client = clients.value.find(c => c.nom === editRow.value.client_nom)
    if (client) {
      return fpacks.value.filter(f => f.client === client.id)
    }
  }
  return fpacks.value
})

watch(() => editRow.value.client_nom, (clientNom) => {
  if (!clientNom) {
    editRow.value.fpack_nom = ''
  } else {
    const client = clients.value.find(c => c.nom === clientNom)
    const fpack = fpacks.value.find(f => f.nom === editRow.value.fpack_nom)
    if (fpack && client && fpack.client !== client.id) {
      editRow.value.fpack_nom = ''
    }
  }
})

watch(() => editRow.value.fpack_nom, (fpackNom) => {
  if (!fpackNom) return
  const fpack = fpacks.value.find(f => f.nom === fpackNom)
  if (fpack) {
    const client = clients.value.find(c => c.id === fpack.client)
    if (client && editRow.value.client_nom !== client.nom) {
      editRow.value.client_nom = client.nom
    }
  }
})

</script>

<template>
  <div class="table-container">
    <table class="table-head">
      <thead>
        <tr>
          <th v-for="col in orderedColumns" :key="col">
            <div style="display: flex; align-items: center; gap: 0.3rem;">
              <span>
                <template v-if="props.tableName === 'projets' && col === 'fpack_id'">fpack</template>
                <template v-else>{{ col }}</template> 
              </span>
              <Filters
                :column="col"
                :values="[...columnValues[col] || []]"
                :selected="filters[col] || new Set([...columnValues[col] || []])"
                :labels="valueLabels[col]"
                @filter-change="updateFilter"
                @sort-change="onSortChange"
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
            <td v-for="col in orderedColumns" :key="col">
              <template v-if="col === 'client' && (props.tableName === 'fpacks' || props.tableName === 'projets')">
              <SearchSelect v-model="newRow.client_nom" :disabled="!!newRow.fpack_nom">
                <option v-for="c in clients" :key="c.id" :value="c.nom">{{ c.nom }}</option>
              </SearchSelect>

              </template>

              <template v-else-if="col === 'fpack_id' && props.tableName === 'projets'">
                <SearchSelect v-model="newRow.fpack_nom" :disabled="!!newRow.client_nom && !newRow.fpack_nom" :key="newRow.client_nom">
                  <option v-for="f in filteredFpacks" :key="f.id" :value="f.nom">{{ f.nom }}</option>
                </SearchSelect>
              </template>

                <template v-else-if="col !== 'id'">
                <AutoComplete v-model="newRow[col]" @keyup.enter="validateAdd" :suggestions="[...columnValues[col] || []]" />
              </template>

            </td>
            <td class="actions">
              <button @click="validateAdd">✅</button>
              <button @click="cancelAdd">❌</button>
            </td>
          </tr>
          <tr v-for="row in filteredAndSortedRows" :key="row.id">
            <td v-for="col in orderedColumns" :key="col">

              <template v-if="editingId === row.id && col === 'client' && (props.tableName === 'fpacks' || props.tableName === 'projets')">
                <SearchSelect v-model="editRow.client_nom" @keyup.enter="validateEdit(row.id)">
                  <option v-for="c in clients" :key="c.id" :value="c.nom">{{ c.nom }}</option>
                </SearchSelect>
              </template>

              <template v-else-if="editingId === row.id && col === 'fpack_id' && props.tableName === 'projets'">
                <SearchSelect v-model="editRow.fpack_nom" @keyup.enter="validateEdit(row.id)">
                  <option v-for="f in filteredFpacksEdit" :key="f.id" :value="f.nom">{{ f.nom }}</option>
                </SearchSelect>
              </template>

              <template v-else-if="editingId === row.id && col !== 'id'">
                <AutoComplete v-model="editRow[col]" @keyup.enter="validateEdit(row.id)" :suggestions="[...columnValues[col] || []]" />
              </template>
              <template v-else-if="col === 'client' && (props.tableName === 'fpacks' || props.tableName === 'projets')">
                {{ clients.find(c => c.id === row.client)?.nom || row.client }}
              </template>

              <template v-else-if="col === 'fpack_id' && props.tableName === 'projets'">
                {{ fpacks.find(f => f.id === row.fpack_id)?.nom || row.fpack_id }}
              </template>

              <template v-else-if="col === 'nom' && props.tableName === 'projets'">
                <span>{{ row.complet ? '✔️' : '⏳' }}</span> | {{ row.nom }}
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
                <button title="Éditer" @click="startEdit(row.id)">✏️</button>
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
                  <button title="Exporter" @click="ExportRow(row)">📤</button>
                </span>
                <span v-if="props.tableName === 'projets'">
                  <button title="Completer" @click="remplirProjet(row)">📝</button>
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

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

</style>