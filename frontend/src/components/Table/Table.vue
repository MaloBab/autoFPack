<script setup lang="ts">
import { computed, defineEmits, defineProps, ref, watch, onMounted, nextTick } from 'vue'
import { useTableReader } from '../../composables/Table/useTableReader'
import { useTableConfig } from '../../composables/Table/useTableConfig'
import { useTableFilters } from '../../composables/Table/useTableFilters'
import { useTableSorting } from '../../composables/Table/useTableSorting'
import { useTableNavigation } from '../../composables/Table/useTableNavigation'
import { useTableRowHandlers } from '../../composables/Table/useTableRowHandlers'
import Filters from '../Searching/Filters.vue'
import TableRowAddModal from './TableRowAddModal.vue'
import TableRowEdit from './TableRowEdit.vue'
import TableRowDisplay from './TableRowDisplay.vue'
import TableActions from './TableActions.vue'

const scrollContainer = ref<HTMLElement | null>(null)
const tableContainer = ref<HTMLElement | null>(null)
const headerTable = ref<HTMLElement | null>(null)
const bodyTable = ref<HTMLElement | null>(null)
const isLoading = ref(true)
const hoveredRow = ref<string | null>(null)
const showAddModal = ref(false)

const props = defineProps<{
  tableName: string
  apiUrl?: string
  ajouter?: boolean
  search?: string
}>()

const emit = defineEmits(['added', 'cancelled'])

// Fonction pour générer un ID unique pour les tables avec clé composée
function getRowId(row: any, tableName: string) {
  if (tableName === 'prix') {
    return `${row.produit_id}_${row.client_id}`
  }
  return row.id?.toString() || ''
}

// Composables
const filters = ref<Record<string, Set<any>>>({})
const tableData = useTableReader(props, emit, filters)
const { tableConfig } = useTableConfig(props.tableName)
const { columnValues, filteredRows, updateFilter } = useTableFilters(tableData, filters, props)

const { sortOrders, onSortChange, filteredAndSortedRows } = useTableSorting(filteredRows, tableData.valueLabels)
const { remplirEquipement, remplirFPack, remplirProjet } = useTableNavigation(props.tableName)
const { getEditingId, handleStartEdit, handleValidateEdit, handleDeleteRow } = useTableRowHandlers(tableData, props.tableName)

// Colonnes ordonnées
const orderedColumns = computed(() => {
  if (!tableData.columns.value) return []
  
  let cols = tableData.columns.value.filter((col:any) => {
    // Filtrage spécialisé selon la table
    if (props.tableName === 'prix') {
      // Pour la table prix, on garde tout sauf si c'est explicitement exclu
      return true
    } else if (props.tableName === 'prix_robot') {
      // Pour prix_robot, on garde l'ID
      return col.toLowerCase() !== 'reference'
    } else {
      // Pour les autres tables, on exclut l'ID sauf prix_robot
      return col.toLowerCase() !== 'id' && col.toLowerCase() !== 'reference'
    }
  })
  
  // Réorganiser les colonnes pour certaines tables
  if (props.tableName === 'prix') {
    // Pour la table prix, mettre les IDs au début
    const idColumns = cols.filter((col:any) => col.includes('_id'))
    const otherColumns = cols.filter((col:any) => !col.includes('_id'))
    cols = [...idColumns, ...otherColumns]
  } else if (tableData.columns.value.some((col:any) => col.toLowerCase() === 'reference')) {
    cols.unshift('reference')
  }
  
  return cols
})

// Fonction pour obtenir le label d'une colonne
function getColumnLabel(col: string): string {
  const mappings: Record<string, Record<string, string>> = {
    produits: { fournisseur_id: 'Fournisseur' },
    prix: { 
      client_id: 'Client', 
      produit_id: 'Produit',
      prix_produit: 'Prix Produit',
      prix_transport: 'Prix Transport',
      commentaire: 'Commentaire'
    },
    prix_robot: { id: 'Robot' },
    projets: { fpack_id: 'Fpack' }
  }
  return mappings[props.tableName]?.[col] || col.charAt(0).toUpperCase() + col.slice(1)
}

function openAddModal() {
  console.log('Opening modal...')
  showAddModal.value = true
}

function closeAddModal() {
  showAddModal.value = false
  tableData.cancelAdd()
  emit('cancelled')
}

function handleModalCreated(newItem: any) {
  console.log('Modal created:', newItem)
  showAddModal.value = false
  emit('added', newItem)
}

// Gestion du scroll et duplication
async function onDuplicate(row: any) {
  await tableData.duplicateRow(row)
  if (scrollContainer.value) {
    scrollContainer.value.scrollTo({
      top: scrollContainer.value.scrollHeight,
      behavior: 'smooth'
    })
  }
}

function synchronizeColumnWidths() {
  if (!headerTable.value || !bodyTable.value) return
  
  const headerCells = headerTable.value.querySelectorAll('th')
  const bodyRows = bodyTable.value.querySelectorAll('tr')
  
  if (bodyRows.length === 0) return
  
  // Calculer les largeurs avec une colonne d'actions plus large
  const dataColumns = headerCells.length
  const remainingWidth = `calc((100%  / ${dataColumns})`
  
  // Appliquer les largeurs au header
  headerCells.forEach((cell) => {
    // Colonnes de données
    cell.style.width = remainingWidth
    cell.style.minWidth = remainingWidth
    cell.style.maxWidth = remainingWidth
    
  })
  
  // Appliquer les largeurs à toutes les lignes du body
  bodyRows.forEach(row => {
    const bodyCells = row.querySelectorAll('td')
    bodyCells.forEach((cell) => {
      cell.style.width = remainingWidth
      cell.style.minWidth = remainingWidth
      cell.style.maxWidth = remainingWidth
   
    })
  })
  
  // Force les tables à avoir la même largeur
  if (headerTable.value && bodyTable.value) {
    const tableWidth = '100%'
    headerTable.value.style.width = tableWidth
    bodyTable.value.style.width = tableWidth
  }
}

// Animation d'entrée
onMounted(async () => {
  await nextTick()
  setTimeout(() => {
    isLoading.value = false
    synchronizeColumnWidths()
  }, 500)
})

// Resynchroniser quand les données changent
watch([filteredAndSortedRows, orderedColumns], async () => {
  await nextTick()
  setTimeout(synchronizeColumnWidths, 100)
})

// Resynchroniser également au scroll (au cas où)
watch(scrollContainer, (newVal) => {
  if (newVal) {
    newVal.addEventListener('scroll', () => {
      requestAnimationFrame(synchronizeColumnWidths)
    })
  }
})

// Watch pour l'ouverture automatique du modal
watch(() => props.ajouter, (val) => {
  if (val) {
    openAddModal()
  }
})

// Gestion du hover sur les lignes
function handleRowHover(rowId: string | null) {
  hoveredRow.value = rowId
}
</script>

<template>
  <div class="modern-table-wrapper" ref="tableContainer" :class="{ loading: isLoading }">
    <!-- Header avec statistiques et bouton d'ajout -->
    <div class="table-stats">
      <div class="stats-card">
        <div class="stats-icon">📊</div>
        <div class="stats-content">
          <span class="stats-number">{{ filteredAndSortedRows.length }}</span>
          <span class="stats-label">Entrées</span>
        </div>
      </div>
      <div class="stats-card">
        <div class="stats-icon">🔍</div>
        <div class="stats-content">
          <span class="stats-number">{{ orderedColumns.length }}</span>
          <span class="stats-label">Colonnes</span>
        </div>
      </div>
      
      <!-- Bouton d'ajout -->
      <button 
        @click="openAddModal"
        class="add-button"
        type="button"
      >
        <span class="add-icon">➕</span>
        <span>Ajouter</span>
      </button>
    </div>

    <div class="table-container">
      <!-- Header fixe -->
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
                      :labels="tableData.valueLabels.value[col]"
                      :sort-order="sortOrders[col] || null"
                      @filter-change="updateFilter"
                      @sort-change="onSortChange"
                    />
                  </div>
                </div>
              </th>
              <th class="actions-header">
                <div class="header-content">
                  <span class="column-name">⚡ Actions</span>
                </div>
              </th>
            </tr>
          </thead>
        </table>
      </div>
      
      <!-- Corps du tableau avec scroll -->
      <div class="table-body-container" ref="scrollContainer">
        <table class="table-body" ref="bodyTable">
          <tbody>
            <tr 
              v-for="(row, index) in filteredAndSortedRows" 
              :key="getRowId(row, props.tableName)"
              class="data-row"
              :class="{ 
                'editing': getEditingId(row),
                'hovered': hoveredRow === getRowId(row, props.tableName)
              }"
              :style="{ '--row-index': index }"
              @mouseenter="handleRowHover(getRowId(row, props.tableName))"
              @mouseleave="handleRowHover(null)"
            >
              <!-- Indicateur de statut -->
              <div class="row-status-indicator"></div>
              
              <!-- Cellules de données -->
              <template v-if="getEditingId(row)">
                <!-- Mode édition -->
                <TableRowEdit
                  :row="row"
                  :columns="orderedColumns"
                  :table-name="props.tableName"
                  :edit-row="tableData.editRow.value"
                  :table-data="tableData"
                  :column-values="columnValues"
                  @validate="handleValidateEdit(row)"
                  @cancel="tableData.cancelEdit"
                />
              </template>
              <template v-else>
                <!-- Mode lecture -->
                <TableRowDisplay
                  :row="row"
                  :columns="orderedColumns"
                  :table-name="props.tableName"
                  :table-data="tableData"
                />
              </template>

              <!-- Actions avec animations -->
              <td class="actions-cell">
                <TableActions
                  :row="row"
                  :is-editing="!!getEditingId(row)"
                  :table-config="tableConfig"
                  @edit="handleStartEdit(row)"
                  @delete="handleDeleteRow(row)"
                  @validate-edit="handleValidateEdit(row)"
                  @cancel-edit="tableData.cancelEdit"
                  @duplicate="onDuplicate(row)"
                  @export="tableData.ExportRow(row)"
                  @remplir-equipement="remplirEquipement(row)"
                  @remplir-fpack="remplirFPack(row)"
                  @remplir-projet="remplirProjet(row)"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <TableRowAddModal 
      :is-open="showAddModal"
      :table-name="props.tableName"
      @close="closeAddModal"
      @created="handleModalCreated"
    />
    
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

.modern-table-wrapper {
  position: relative;
  width: calc(69.56522vw + 0.543478vw * (100vw));;
  height: 49vh;
  border-radius: var(--border-radius);
  padding: 1.5rem;
  box-shadow: var(--shadow-lg);
  transition: all var(--transition-slow); 
}

.modern-table-wrapper.loading {
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

.add-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg,#b7eddf, #0f582b);
  color: white;
  border: none;
  padding: 0.875rem 1.25rem;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-normal);
  box-shadow: var(--shadow-sm);
  margin-left: auto;
}

.add-button:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  background: linear-gradient(135deg, #059669, #047857);
}

.add-button:active {
  transform: translateY(0);
}

.add-icon {
  font-size: 1rem;
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

.table-body-container::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #2563eb, #059669);
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

.data-row.editing::before {
  background: linear-gradient(135deg, var(--warning-color), var(--danger-color));
}

.data-row:hover {
  background: var(--bg-hover);
  transform: translateX(2px);
  box-shadow: var(--shadow-sm);
}

.data-row.editing {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.1), rgba(239, 68, 68, 0.1));
  border-left: 4px solid var(--warning-color);
}

.row-status-indicator {
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-color);
  opacity: 0;
  transition: all var(--transition-fast);
}

.data-row:hover .row-status-indicator {
  opacity: 1;
  transform: translateY(-50%) scale(1.2);
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

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
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