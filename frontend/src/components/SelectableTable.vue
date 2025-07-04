<script setup lang="ts">
import { ref, computed, defineProps, defineEmits, onMounted, watch } from 'vue'
import axios from 'axios'
import Filters from '../components/Filters.vue'

// Props
const props = defineProps<{
  apiUrl?: string
  ajouter?: boolean
  search?: string
  selectedIds: Set<number>
  filterMode?: 'all' | 'selected' | 'unselected'
}>()

const emit = defineEmits<{
  (e: 'selection-changed', selected: Set<number>): void
}>()

// État
const columns = ref<string[]>([])
const rows = ref<any[]>([])
const fournisseurs = ref<{ id: number, nom: string }[]>([])
const filters = ref<Record<string, Set<any>>>({})
const selected = ref(new Set<number>(props.selectedIds))
const scrollContainer = ref<HTMLElement | null>(null)

// Fetch des données
async function fetchData() {
  const urlBase = props.apiUrl || 'http://localhost:8000'

  // Récupérer colonnes
  const colRes = await axios.get(`${urlBase}/table-columns/produits`)
  columns.value = colRes.data

  // Récupérer données produits
  const dataRes = await axios.get(`${urlBase}/produits`)
  rows.value = dataRes.data

  // Init filtres
  filters.value = {}
  columns.value.forEach(col => {
    filters.value[col] = new Set(rows.value.map(row => row[col]))
  })

  // Récupérer fournisseurs
  const fournisseursRes = await axios.get(`${urlBase}/fournisseurs`)
  fournisseurs.value = fournisseursRes.data
}

onMounted(fetchData)

// Toggle sélection
function toggleSelect(id: number) {
  if (selected.value.has(id)) {
    selected.value.delete(id)
  } else {
    selected.value.add(id)
  }
  emit('selection-changed', new Set(selected.value))
}

watch(() => props.selectedIds, (newVal) => {
  selected.value = new Set(newVal)
})

// Valeurs distinctes par colonne
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

// Labels pour les filtres
const valueLabels = computed(() => {
  const map: Record<string, Record<any, string>> = {}
  map['fournisseur_id'] = Object.fromEntries(
    fournisseurs.value.map(f => [f.id, f.nom])
  )
  return map
})

// Filtres et recherche
const filteredRows = computed(() => {
  let data = rows.value
    // appliquer les filtres colonnes
    .filter(row =>
      columns.value.every(col =>
        !filters.value[col] || filters.value[col].has(row[col])
      )
    )
    // appliquer la recherche
    .filter(row => {
      if (!props.search) return true
      const search = props.search.toLowerCase()
      return columns.value.some(col => {
        let cellValue = row[col]
        if (col === 'fournisseur_id') {
          const fournisseur = fournisseurs.value.find(f => f.id === cellValue)
          cellValue = fournisseur?.nom || ''
        }
        return String(cellValue).toLowerCase().includes(search)
      })
    })

  // appliquer filterMode
  if (props.filterMode === 'selected') {
    data = data.filter(row => selected.value.has(row.id))
  } else if (props.filterMode === 'unselected') {
    data = data.filter(row => !selected.value.has(row.id))
  }

  return data
})

function updateFilter(col: string, values: Set<any>) {
  filters.value[col] = values
}

</script>

<template>
  <div class="table-container">
    <table class="table-head">
      <thead>
        <tr>
          <th v-for="col in columns" :key="col">
            <div style="display: flex; align-items: center; gap: 0.3rem;">
              <span>
                <template v-if="col === 'fournisseur_id'">fournisseur</template>
                <template v-else>{{ col }}</template>
              </span>
              <Filters
                :column="col"
                :values="[...columnValues[col] || []]"
                :selected="filters[col] || new Set([...columnValues[col] || []])"
                :labels="valueLabels[col]"
                @filter-change="updateFilter"
              />
            </div>
          </th>
        </tr>
      </thead>
    </table>
    <div class="table-body-scroll" ref="scrollContainer">
      <table>
        <tbody>
            <tr v-for="row in filteredRows" :key="row.id" @click="toggleSelect(row.id)" :class="{ selected: selected.has(row.id) }">
                <td v-for="col in columns" :key="col">
                    <template v-if="col === 'fournisseur_id'">
                        {{ fournisseurs.find(f => f.id === row.fournisseur_id)?.nom || row.fournisseur_id }}
                    </template>
                    <template v-else>
                        {{ row[col] }}
                    </template>
                </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>



<style scoped>
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
tr:hover {
  background-color: #f0f0f0;
  cursor: pointer;
}
tr.selected {
  background-color: #bbf7d0;
}
</style>
