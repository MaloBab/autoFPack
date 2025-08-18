<!-- SelectableTable.vue -->
<script setup lang="ts">
import { ref, computed, defineProps, defineEmits, onMounted, watch, reactive, nextTick } from 'vue'
import axios from 'axios'
import Filters from '../Searching/Filters.vue'
import { showToast } from '../../composables/useToast'


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
const tableContainer = ref<HTMLElement | null>(null)
const headerTable = ref<HTMLElement | null>(null)
const bodyTable = ref<HTMLElement | null>(null)
const produitIncompatibilites = ref<{ produit_id_1: number, produit_id_2: number }[]>([])
const isLoading = ref(true)
const hoveredRow = ref<number | null>(null)

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
  await fetchData()

  const response = await axios.get(`http://localhost:8000/equipementproduit/${props.equipementId}`)
  const data = response.data

  data.forEach((item: { produit_id: number, quantite: number }) => {
    selected.value.add(item.produit_id)
    quantities.value[item.produit_id] = item.quantite
  })
  
  const res = await axios.get('http://localhost:8000/produit-incompatibilites')
  produitIncompatibilites.value = res.data
  
  
  await nextTick()
  setTimeout(() => {
    isLoading.value = false
    synchronizeColumnWidths()
  }, 500)
})

function toggleSelect(id: number) {
  if (selected.value.has(id)) {
    selected.value.delete(id)
    delete quantities.value[id]
  } else {
    const produitsExistants = Array.from(selected.value)
    if (!isProduitCompatibleAvecListe(id, produitsExistants)) {
      showToast("Ce produit est incompatible avec la sélection actuelle.", "#f67377")
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
  if (columns.value.some(col => col.toLowerCase() === 'reference')) {
    cols.unshift('reference')
  }
  return cols
})

function getColumnLabel(col: string): string {
  if (col === 'fournisseur_id') return 'Fournisseur'
  return col.charAt(0).toUpperCase() + col.slice(1)
}

function synchronizeColumnWidths() {
  if (!headerTable.value || !bodyTable.value) return
  
  const headerCells = headerTable.value.querySelectorAll('th')
  const bodyRows = bodyTable.value.querySelectorAll('tr')
  
  if (bodyRows.length === 0) return
  
  const dataColumns = headerCells.length
  const remainingWidth = `calc((100% / ${dataColumns})`
  
  headerCells.forEach((cell) => {
    cell.style.width = remainingWidth
    cell.style.minWidth = remainingWidth
    cell.style.maxWidth = remainingWidth
  })
  
  bodyRows.forEach(row => {
    const bodyCells = row.querySelectorAll('td')
    bodyCells.forEach((cell) => {
      cell.style.width = remainingWidth
      cell.style.minWidth = remainingWidth
      cell.style.maxWidth = remainingWidth
    })
  })
  
  if (headerTable.value && bodyTable.value) {
    const tableWidth = '100%'
    headerTable.value.style.width = tableWidth
    bodyTable.value.style.width = tableWidth
  }
}

watch([filteredAndSortedRows, orderedColumns], async () => {
  await nextTick()
  setTimeout(synchronizeColumnWidths, 100)
})

watch(scrollContainer, (newVal) => {
  if (newVal) {
    newVal.addEventListener('scroll', () => {
      requestAnimationFrame(synchronizeColumnWidths)
    })
  }
})

function handleRowHover(rowId: number | null) {
  hoveredRow.value = rowId
}

const selectedCount = computed(() => selected.value.size)
const compatibleCount = computed(() => 
  filteredAndSortedRows.value.filter(row => !isProduitIncompatibleAvecSelection(row.id)).length
)
</script>

<template>
  <div class="modern-selectable-table-wrapper" ref="tableContainer" :class="{ loading: isLoading }">
    <div class="table-stats">
      <div class="stats-card">
        <div class="stats-icon">📊</div>
        <div class="stats-content">
          <span class="stats-number">{{ filteredAndSortedRows.length }}</span>
          <span class="stats-label">Produits</span>
        </div>
      </div>
      <div class="stats-card">
        <div class="stats-icon">✅</div>
        <div class="stats-content">
          <span class="stats-number">{{ selectedCount }}</span>
          <span class="stats-label">Sélectionnés</span>
        </div>
      </div>
      <div class="stats-card">
        <div class="stats-icon">🔧</div>
        <div class="stats-content">
          <span class="stats-number">{{ compatibleCount }}</span>
          <span class="stats-label">Compatibles</span>
        </div>
      </div>
    </div>

    <div class="table-container">
      <div class="table-header-wrapper">
        <table class="table-header" ref="headerTable">
          <thead>
            <tr>
              <th v-for="col in orderedColumns" :key="col" class="header-cell">
                <div class="header-content">
                  <div class="header-title">
                    <span class="column-icon">🗃️</span>
                    <span class="column-name">{{ getColumnLabel(col) }}</span>
                  </div>
                  <div class="header-filters">
                    <Filters
                      :column="col"
                      :values="[...columnValues[col] || []]"
                      :selected="filters[col] || new Set([...columnValues[col] || []])"
                      :labels="valueLabels[col]"
                      :sort-order="sortOrders[col] || null"
                      @filter-change="updateFilter"
                      @sort-change="onSortChange"
                    />
                  </div>
                </div>
              </th>
              <th class="actions-header">
                <div class="header-content">
                  <span class="column-name">📦 Quantité</span>
                </div>
              </th>
            </tr>
          </thead>
        </table>
      </div>
      
      <div class="table-body-container" ref="scrollContainer">
        <table class="table-body" ref="bodyTable">
          <tbody>
            <tr 
              v-for="(row, index) in filteredAndSortedRows" 
              :key="row.id"
              class="data-row"
              :class="{ 
                'selected': selected.has(row.id) && !isProduitIncompatibleAvecSelection(row.id),
                'conflict': isProduitIncompatibleAvecSelection(row.id),
                'hovered': hoveredRow === row.id
              }"
              :style="{ '--row-index': index }"
              @click="toggleSelect(row.id)"
              @mouseenter="handleRowHover(row.id)"
              @mouseleave="handleRowHover(null)"
            >
              <td v-for="col in orderedColumns" :key="col" class="data-cell">
                <template v-if="col === 'fournisseur_id'">
                  {{ fournisseurs.find(f => f.id === row.fournisseur_id)?.nom || row.fournisseur_id }}
                </template>
                <template v-else>
                  {{ row[col] }}
                </template>
              </td>
              <td class="quantity-cell">
                <input
                  v-if="selected.has(row.id)"
                  type="number"
                  min="1"
                  v-model.number="quantities[row.id]"
                  @click.stop
                  class="quantity-input"
                />
                <div v-else class="quantity-placeholder">
                  <span class="quantity-icon">—</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner">
        <div class="spinner-ring"></div>
        <div class="spinner-ring"></div>
        <div class="spinner-ring"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modern-selectable-table-wrapper {
  position: relative;
  width: calc(69.56522vw + 0.543478vw * (100vw));
  height: 49vh;
  border-radius: var(--border-radius);
  padding: 1.5rem;
  box-shadow: var(--shadow-lg);
  transition: all var(--transition-slow);
  background: #f7f7f7;
}

.modern-selectable-table-wrapper.loading {
  pointer-events: none;
}

.table-stats {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  animation: slideInTop 0.6s ease-out;
  align-items: center;
  height: 8%;
}

.stats-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: var(--bg-primary);
  padding: 1rem 1.25rem;
  border-radius: 10px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
  transition: all var(--transition-normal);
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stats-icon {
  font-size: 1.5rem;
  filter: grayscale(0.3);
  transition: filter var(--transition-fast);
}

.stats-card:hover .stats-icon {
  filter: grayscale(0);
}

.stats-content {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.stats-number {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.stats-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.table-container {
  background: var(--bg-primary);
  border-radius: var(--border-radius);
  overflow: hidden;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-color);
  animation: slideInBottom 0.8s ease-out;
  max-height: 46vh;
}

.table-header-wrapper {
  position: sticky;
  top: 0;
  z-index: 10;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-bottom: 2px solid var(--primary-color);
}

.table-header,
.table-body {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
}

.table-header th,
.table-body td {
  box-sizing: border-box;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-cell,
.actions-header {
  padding: 0.5rem 1rem;
  text-align: left;
  position: relative;
  background: transparent;
  transition: all var(--transition-normal);
  box-sizing: border-box;
}

.header-cell::after {
  content: '';
  position: absolute;
  right: 0;
  top: 25%;
  height: 50%;
  width: 1px;
  background: rgba(255, 255, 255, 0.2);
}

.header-cell:last-child::after,
.actions-header::after {
  display: none;
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.column-icon {
  font-size: 1rem;
  opacity: 0.8;
}

.column-name {
  font-weight: 600;
  color: white;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.table-body-container {
  background: rgba(200, 220, 255, 0.2);
  max-height: 35vh;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: var(--primary-color) var(--bg-secondary);
}

.table-body-container::-webkit-scrollbar {
  width: 8px;
}

.table-body-container::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

.table-body-container::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
  border-radius: 4px;
  transition: background var(--transition-fast);
}


.data-row {
  position: relative;
  transition: all var(--transition-normal);
  cursor: pointer;
}

.data-row::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 4px;
  background: transparent;
  transition: all var(--transition-fast);
}

.data-row:hover::before {
  background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
}

.data-row.selected::before {
  background: #10b981
}

.data-row.conflict::before {
  background: #dc2626;
}

.data-row:hover {
  background: var(--bg-hover);
  transform: translateX(2px);
  box-shadow: var(--shadow-sm);
}

.data-row.selected {
  background: linear-gradient(135deg, rgba(16, 185, 95,0.25), rgba(5, 150, 105,0.25));
}

.data-row.conflict {
  background: linear-gradient(135deg, rgba(239, 68, 68,0.25), rgba(220, 38, 38,0.25));
}

.data-row td {
  padding: 0.5rem;
  border-bottom: 1px solid var(--border-color);
  vertical-align: middle;
  color: var(--text-primary);
  font-weight: 500;
  transition: all var(--transition-fast);
  box-sizing: border-box;
  overflow: hidden;
  text-overflow: ellipsis;
}

.data-row:last-child td {
  border-bottom: none;
}

.data-cell {
  font-size: 0.875rem;
}

.quantity-cell {
  text-align: center;
  width: 120px;
}

.quantity-input {
  width: 80px;
  padding: 0.4rem 0.6rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  text-align: center;
  transition: all var(--transition-fast);
  background: white;
}

.quantity-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.quantity-input:hover {
  border-color: var(--primary-color);
}

.quantity-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.3;
  transition: opacity var(--transition-fast);
}

.data-row:hover .quantity-placeholder {
  opacity: 0.6;
}

.quantity-icon {
  font-size: 1.2rem;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius);
  z-index: 100;
}

.loading-spinner {
  position: relative;
  width: 60px;
  height: 60px;
}

.spinner-ring {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 3px solid transparent;
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner-ring:nth-child(2) {
  animation-delay: -0.33s;
  border-top-color: var(--accent-color);
}

.spinner-ring:nth-child(3) {
  animation-delay: -0.67s;
  border-top-color: var(--warning-color);
}

@keyframes slideInTop {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInBottom {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>