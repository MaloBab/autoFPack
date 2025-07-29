<script setup lang="ts">
import { computed, defineEmits, defineProps, reactive } from 'vue'
import { useTableReader } from '../composables/useTableReader'
import Filters from './Filters.vue'
import { ref, watch } from 'vue'
import AutoComplete from '../components/AutoCompleteInput.vue'

const scrollContainer = ref<HTMLElement | null>(null)

const props = defineProps<{
  tableName: string
  apiUrl?: string
  ajouter?: boolean
  search?: string
}>()
const emit = defineEmits(['added', 'cancelled'])

const filters = ref<Record<string, Set<any>>>({})
const {
  columns, rows, newRow, editingId, editRow,
  fournisseurs, clients, produits, robots,
  validateAdd, cancelAdd, startEdit, duplicateRow,
  validateEdit, cancelEdit, deleteRow, startEditPrix
} = useTableReader(props, emit, filters)

const orderedColumns = computed(() => {
  if (!columns.value) return []
  const cols = columns.value.filter(col => (col.toLowerCase() !== 'id' || props.tableName==='prix_robot') && col.toLowerCase() !== 'reference')
  if (columns.value.some(col => col.toLowerCase() === 'reference')) {cols.unshift('reference')}
  return cols
})

const nameMapping = computed(() => {
  const map: Record<string, Record<number, string>> = {}

  if (props.tableName === 'produits') {
    map['fournisseur_id'] = Object.fromEntries(fournisseurs.value.map(f => [f.id, f.nom]))
  }
  if (props.tableName === 'robots') {
    map['client'] = Object.fromEntries(clients.value.map(c => [c.id, c.nom]))
  }
  if (props.tableName === 'prix') {
    map['produit_id'] = Object.fromEntries(produits.value.map(p => [p.id, p.nom]))
    map['client_id'] = Object.fromEntries(clients.value.map(c => [c.id, c.nom]))
  }
    if (props.tableName === 'prix_robot') {
    map['id'] = Object.fromEntries(robots.value.map(r => [r.id, r.nom]))
  }

  return map
})


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
        const label = nameMapping.value[col]?.[cellValue]
        return (label || String(cellValue)).toLowerCase().includes(search)
      })
    }))

const valueLabels = computed(() => nameMapping.value)

function updateFilter(col: string, values: Set<any>) {
  filters.value[col] = values
}

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
        const labelA = valueLabels.value[col]?.[valA] ?? valA
        const labelB = valueLabels.value[col]?.[valB] ?? valB

        if (typeof labelA === 'string' && typeof labelB === 'string') {
          const aLower = labelA.toLowerCase()
          const bLower = labelB.toLowerCase()
          return order === 'asc' ? aLower.localeCompare(bLower) : bLower.localeCompare(aLower)
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



async function onDuplicate(row: any) {
  await duplicateRow(row)
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
  }
}


watch(() => props.ajouter, (val) => {
  if (val && scrollContainer.value) {
    scrollContainer.value.scrollTop = 0
  }})

  watch(() => newRow.value.robot_nom, (nom) => {
  const r = robots.value.find(r => r.nom === nom)
  if (r) newRow.value.robot_reference = r.reference
  })

watch(() => newRow.value.robot_reference, (ref) => {
  const r = robots.value.find(r => r.reference === ref)
  if (r) newRow.value.robot_nom = r.nom
  })

watch(() => editRow.value.robot_nom, (nom) => {
  const r = robots.value.find(r => r.nom === nom)
  if (r) editRow.value.robot_reference = r.reference
  })

watch(() => editRow.value.robot_reference, (ref) => {
  const r = robots.value.find(r => r.reference === ref)
  if (r) editRow.value.robot_nom = r.nom
  })

</script>


<template>
  <div class="table-container">
    <table class="table-head">
      <thead>
        <tr>
          <th v-for="col in orderedColumns " :key="col">
            <div style="display: flex; align-items: center; gap: 0.3rem;">
              <span>
                <template v-if="col === 'fournisseur_id' && props.tableName === 'produits'">fournisseur</template>
                <template v-else-if="col === 'client_id' && props.tableName === 'prix'">client</template>
                <template v-else-if="col === 'produit_id' && props.tableName === 'prix'">produit</template>
                <template v-else-if="col === 'id' && props.tableName === 'prix_robot'">robot</template>
                <template v-else>{{ col }}</template>
              </span>
              <Filters
                :column="col"
                :values="[...columnValues[col] || []]"
                :selected="filters[col] || new Set([...columnValues[col] || []])"
                :labels="valueLabels[col] || {}"
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
            <td v-for="col in orderedColumns " :key="col">

              <template v-if="col === 'fournisseur_id' && props.tableName === 'produits'">
                <select v-model="newRow.fournisseur_nom">
                  <option v-for="f in fournisseurs" :key="f.id" :value="f.nom">{{ f.nom }}</option>
                </select>
              </template>

              <template v-else-if="col === 'client' && props.tableName === 'robots'">
                <select v-model="newRow.client_nom">
                  <option v-for="c in clients" :key="c.id" :value="c.nom">{{ c.nom }}</option>
                </select>
              </template>

              <template v-else-if="col === 'produit_id' && props.tableName === 'prix'">
                <select v-model="newRow.produit_nom">
                  <option v-for="p in produits" :key="p.id" :value="p.nom">{{ p.nom }}</option>
                </select>
              </template>

              <template v-else-if="col === 'client_id' && props.tableName === 'prix'">
                <select v-model="newRow.client_nom">
                  <option v-for="c in clients" :key="c.id" :value="c.nom">{{ c.nom }}</option>
                </select>
              </template>

              <template v-else-if="col === 'reference' && props.tableName === 'prix_robot'">
                <select v-model="newRow.robot_reference">
                  <option v-for="r in robots" :key="r.id" :value="r.reference">{{ r.reference }}</option>
                </select>
              </template>

              <template v-else-if="col === 'id' && props.tableName === 'prix_robot'">
                <select v-model="newRow.robot_nom">
                  <option v-for="r in robots" :key="r.id" :value="r.nom">{{r.nom}}</option>
                </select>
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
            <td v-for="col in orderedColumns " :key="col">
              <template v-if="editingId === row.id && col === 'fournisseur_id' && props.tableName === 'produits'">
                <select v-model="editRow.fournisseur_nom" @keyup.enter="validateEdit(row.id)">
                  <option v-for="f in fournisseurs" :key="f.id" :value="f.nom">{{ f.nom }}</option>
                </select>
              </template>
              <template v-else-if="editingId === row.id && col === 'client' && props.tableName === 'robots'">
                <select v-model="editRow.client_nom" @keyup.enter="validateEdit(row.id)">
                  <option v-for="c in clients" :key="c.id" :value="c.nom">{{ c.nom }}</option>
                </select>
              </template>
              
              <template v-else-if="editingId === row.id && col === 'reference' && props.tableName === 'prix_robot'">
                <select v-model="editRow.robot_reference">
                  <option v-for="r in robots" :key="r.id" :value="r.reference">{{ r.reference }}</option>
                </select>
              </template>

              <template v-else-if="editingId === row.id && col === 'id' && props.tableName === 'prix_robot'">
                <select v-model="editRow.robot_nom" @keyup.enter="validateEdit(row.id)">
                  <option v-for="r in robots" :key="r.id" :value="r.nom">{{ r.nom }}</option>
                </select>
              </template>

              <template v-else-if="editingId === Number(`${row.produit_id}${row.client_id}`) && col === 'client_id' && props.tableName === 'prix'">
                <select v-model="editRow.client_nom" @keyup.enter="validateEdit({ produit_id: row.produit_id, client_id: row.client_id })">
                  <option v-for="c in clients" :key="c.id" :value="c.nom">{{ c.nom }}</option>
                </select>
              </template>

              <template v-else-if="editingId === Number(`${row.produit_id}${row.client_id}`) && col === 'produit_id' && props.tableName === 'prix'">
                <select v-model="editRow.produit_nom" @keyup.enter="validateEdit({ produit_id: row.produit_id, client_id: row.client_id })">
                  <option v-for="p in produits" :key="p.id" :value="p.nom">{{ p.nom }}</option>
                </select>
              </template>


              <template v-else-if="editingId === Number(`${row.produit_id}${row.client_id}`) && props.tableName === 'prix' && col !== 'produit_id' && col !== 'client_id'">
                <AutoComplete v-model="editRow[col]" @keyup.enter="validateEdit({ produit_id: row.produit_id, client_id: row.client_id })" :suggestions="[...columnValues[col] || []]" />
              </template>

              <template v-else-if="editingId === row.id && col !== 'id'">
                <AutoComplete v-model="editRow[col]" @keyup.enter="validateEdit(row.id)" :suggestions="[...columnValues[col] || []]" />
              </template>
              <template v-else-if="col === 'fournisseur_id' && props.tableName === 'produits'">
                {{ fournisseurs.find(f => f.id === row.fournisseur_id)?.nom || row.fournisseur_id }}
              </template>
              <template v-else-if="col === 'client' && props.tableName === 'robots'">
                {{ clients.find(c => c.id === row.client)?.nom || row.client }}
              </template>
              <template v-else-if="col === 'produit_id' && props.tableName === 'prix'">
                {{ produits.find(p => p.id === row.produit_id)?.nom || row.produit_id }}
              </template>
              <template v-else-if="col === 'client_id' && props.tableName === 'prix'">
                {{ clients.find(c => c.id === row.client_id)?.nom || row.client_id }}
              </template>

              <template v-else-if="col === 'id' && props.tableName === 'prix_robot'">
                {{ robots.find(r => r.id === row.id)?.nom || row.id }}
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
              <template v-else-if="editingId === Number(`${row.produit_id}${row.client_id}`) && props.tableName === 'prix'">
                <button @click="validateEdit({ produit_id: row.produit_id, client_id: row.client_id })">✅</button>
                <button @click="cancelEdit">❌</button>
              </template>
              <template v-else>
                <button v-if="props.tableName === 'prix'" title="Editer" @click="startEditPrix({ produit_id: row.produit_id, client_id: row.client_id })">✏️</button>
                <button v-else title="Éditer" @click="startEdit(row.id)">✏️</button>

                <button v-if="props.tableName === 'produits'" title="Dupliquer" @click="onDuplicate(row)">🔁</button>
                <button v-if="props.tableName === 'prix'" @click="deleteRow({ produit_id: row.produit_id, client_id: row.client_id })">🗑️</button>
                <button v-else title="Supprimer" @click="deleteRow(row.id)">🗑️</button>
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