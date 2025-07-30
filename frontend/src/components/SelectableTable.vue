<script setup lang="ts">
import { ref, computed, defineProps, defineEmits, onMounted, watch, reactive } from 'vue'
import axios from 'axios'
import Filters from '../components/Filters.vue'
import { showToast } from '../composables/useToast'
import { useLoading } from '../composables/useLoading'

const { startLoading, stopLoading } = useLoading()

const props = defineProps<{
  equipementId: number
  apiUrl?: string
  ajouter?: boolean
  search?: string
  selectedIds: Set<number>
  filterMode?: 'all' | 'selected' | 'unselected'
}>()

const emit = defineEmits<{
  (e: 'selection-changed', selected: Set<number>, quantities: Record<number, number>): void
}>()

const columns = ref<string[]>([])
const rows = ref<any[]>([])
const fournisseurs = ref<{ id: number, nom: string }[]>([])
const filters = ref<Record<string, Set<any>>>({})
const selected = ref(new Set<number>(props.selectedIds))
const quantities = ref<Record<number, number>>({})
const scrollContainer = ref<HTMLElement | null>(null)
const produitIncompatibilites = ref<{ produit_id_1: number, produit_id_2: number }[]>([])

async function fetchData() {
  const urlBase = props.apiUrl || 'http://localhost:8000'

  const colRes = await axios.get(`${urlBase}/table-columns/produits`)
  columns.value = colRes.data

  const dataRes = await axios.get(`${urlBase}/produits`)
  rows.value = dataRes.data

  filters.value = {}
  columns.value.forEach(col => {
    filters.value[col] = new Set(rows.value.map(row => row[col]))
  })

  const fournisseursRes = await axios.get(`${urlBase}/fournisseurs`)
  fournisseurs.value = fournisseursRes.data
}


onMounted(async () => {
  startLoading()
  await fetchData()

  const response = await axios.get(`http://localhost:8000/equipementproduit/${props.equipementId}`)
  const data = response.data

  data.forEach((item: { produit_id: number, quantite: number }) => {
    selected.value.add(item.produit_id)
    quantities.value[item.produit_id] = item.quantite
  })
  const res = await axios.get('http://localhost:8000/produit-incompatibilites')
  produitIncompatibilites.value = res.data
  stopLoading()
})

function toggleSelect(id: number) {
  if (selected.value.has(id)) {
    selected.value.delete(id)
    delete quantities.value[id]
  } else {
    const produitsExistants = Array.from(selected.value)
    if (!isProduitCompatibleAvecListe(id, produitsExistants)) {
      showToast("Ce produit est incompatible avec la sélection actuelle.","#f67377")
      return
    }
    selected.value.add(id)
    quantities.value[id] = 1
  }

  emit('selection-changed', new Set(selected.value), { ...quantities.value })
}

watch(() => props.selectedIds, (newVal) => {
  selected.value = new Set(newVal)
})
watch(
  () => quantities.value,
  (newQty) => {
    emit('selection-changed', new Set(selected.value), { ...newQty })
  },
  { deep: true }
)

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

const valueLabels = computed(() => {
  const map: Record<string, Record<any, string>> = {}
  map['fournisseur_id'] = Object.fromEntries(
    fournisseurs.value.map(f => [f.id, f.nom])
  )
  return map
})

const filteredRows = computed(() => {
  let data = rows.value
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
        if (col === 'fournisseur_id') {
          const fournisseur = fournisseurs.value.find(f => f.id === cellValue)
          cellValue = fournisseur?.nom || ''
        }
        return String(cellValue).toLowerCase().includes(search)
      })
    })

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


function isProduitCompatibleAvecListe(nouveauProduitId: number, produitsExistants: number[]): boolean {
  return !produitsExistants.some(existant =>
    produitIncompatibilites.value.some(inc =>
      (inc.produit_id_1 === nouveauProduitId && inc.produit_id_2 === existant) ||
      (inc.produit_id_2 === nouveauProduitId && inc.produit_id_1 === existant)
    )
  )
}

function isProduitIncompatibleAvecSelection(id: number): boolean {
  const produitsExistants = Array.from(selected.value)
  return !isProduitCompatibleAvecListe(id, produitsExistants)
}

const orderedColumns = computed(() => {
  if (!columns.value) return []
  const cols = columns.value.filter(col => col.toLowerCase() !== 'id' && col.toLowerCase() !== 'reference')
  if (columns.value.some(col => col.toLowerCase() === 'reference')) {cols.unshift('reference')}
  return cols
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
                <template v-if="col === 'fournisseur_id'">fournisseur</template>
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
          <th>Quantité</th>
        </tr>
      </thead>
    </table>
    <div class="table-body-scroll" ref="scrollContainer">
      <table>
        <tbody>
            <tr v-for="row in filteredAndSortedRows" :key="row.id" @click="toggleSelect(row.id)"
              :class="{ conflict: isProduitIncompatibleAvecSelection(row.id),
                selected: selected.has(row.id) && !isProduitIncompatibleAvecSelection(row.id)}">
                <td v-for="col in orderedColumns" :key="col">
                    <template v-if="col === 'fournisseur_id'">
                        {{ fournisseurs.find(f => f.id === row.fournisseur_id)?.nom || row.fournisseur_id }}
                    </template>
                    <template v-else>
                        {{ row[col] }}
                    </template>
                </td>
                <td>
                <input
                  v-if="selected.has(row.id)"
                  type="number"
                  min="1"
                  v-model.number="quantities[row.id]"
                  @click.stop
                  class="quantite-input"
                />
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

.quantite-input {
  width: 60px;
  padding: 0.2rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

tr:hover {
  background-color: #f0f0f0;
  cursor: pointer;
}
tr.selected {
  background-color: #bbf7d0;
}

tr.conflict {
  background-color: #f6b3b7;
}

</style>
