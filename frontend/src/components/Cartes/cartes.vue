<!--- cartes.vue --->
<script setup lang="ts">
import { ref, computed, defineProps, defineEmits, onMounted } from 'vue'
import axios from 'axios'

const props = defineProps<{
  tableName: string
  search?: string
}>()

const emit = defineEmits(['item-selected', 'item-edited', 'item-deleted'])

// État réactif
const columns = ref<string[]>([])
const rows = ref<any[]>([])
const fournisseurs = ref<{ id: number, nom: string }[]>([])
const clients = ref<{ id: number, nom: string }[]>([])
const fpacks = ref<{ id: number, nom: string }[]>([])
const produits = ref<{ id: number, nom: string }[]>([])
const robots = ref<{ id: number, nom: string }[]>([])

const searchQuery = ref('')
const viewMode = ref<'grid' | 'list' | 'masonry'>('grid')
const showAdvancedFilters = ref(false)
const filters = ref<Record<string, any[]>>({})
const selectedItems = ref(new Set<number>())
const selectedItem = ref<any>(null)
const editingId = ref<number | null>(null)

// Pagination
const currentPage = ref(1)
const itemsPerPage = ref(10)

// Données computées
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

const filterableColumns = computed(() => {
  return columns.value.filter(col => 
    col !== 'id' && 
    columnValues.value[col]?.size > 1 && 
    columnValues.value[col]?.size < 50
  )
})

const filteredAndSortedRows = computed(() => {
  let data = rows.value

  // Filtre de recherche global
  if (searchQuery.value || props.search) {
    const search = (searchQuery.value || props.search || '').toLowerCase()
    data = data.filter(row =>
      columns.value.some(col => {
        let cellValue = getDisplayValue(row[col], col)
        return String(cellValue).toLowerCase().includes(search)
      })
    )
  }

  // Filtres avancés
  data = data.filter(row =>
    Object.entries(filters.value).every(([col, values]) =>
      !values.length || values.includes(row[col])
    )
  )

  return data
})

const totalPages = computed(() => 
  Math.ceil(filteredAndSortedRows.value.length / itemsPerPage.value)
)

const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return filteredAndSortedRows.value.slice(start, end)
})

// Méthodes utilitaires
function getTableDisplayName(tableName: string): string {
  const names: Record<string, string> = {
    produits: 'Produits',
    fournisseurs: 'Fournisseurs',
    clients: 'Clients',
    fpacks: 'FPacks',
    projets: 'Projets',
    robots: 'Robots',
    prix: 'Prix',
    prix_robot: 'Prix Robot'
  }
  return names[tableName] || tableName.charAt(0).toUpperCase() + tableName.slice(1)
}

function getColumnLabel(col: string): string {
  const mappings: Record<string, Record<string, string>> = {
    produits: { fournisseur_id: 'Fournisseur' },
    prix: { client_id: 'Client', produit_id: 'Produit' },
    prix_robot: { id: 'Robot' },
    projets: { fpack_id: 'Fpack' }
  }
  return mappings[props.tableName]?.[col] || col.charAt(0).toUpperCase() + col.slice(1)
}

function getDisplayValue(value: any, col: string): any {
  switch (col) {
    case 'fournisseur_id':
      return fournisseurs.value.find(f => f.id === value)?.nom || value
    case 'client_id':
    case 'client':
      return clients.value.find(c => c.id === value)?.nom || value
    case 'fpack_id':
      return fpacks.value.find(f => f.id === value)?.nom || value
    case 'produit_id':
      return produits.value.find(p => p.id === value)?.nom || value
    default:
      return value
  }
}

function getPrimaryValue(item: any): string {
  if (item.nom) return item.nom
  if (item.reference) return item.reference
  if (item.name) return item.name
  return `${props.tableName.charAt(0).toUpperCase() + props.tableName.slice(1)} #${item.id}`
}

function getSecondaryValue(item: any): string {
  if (props.tableName === 'produits') return getDisplayValue(item.fournisseur_id, 'fournisseur_id')
  if (props.tableName === 'projets') return item.complet ? '✔️ Complet' : '⏳ En cours'
  if (item.reference && item.nom) return item.reference
  return `ID: ${item.id}`
}

function getVisibleFields(item: any): Array<{ key: string, label: string, value: any, type: string }> {
  return columns.value
    .filter(col => col !== 'id' && col !== 'nom' && col !== 'reference')
    .slice(0, 4)
    .map(col => ({
      key: col,
      label: getColumnLabel(col),
      value: getDisplayValue(item[col], col),
      type: typeof item[col] === 'number' ? 'number' : 'text'
    }))
}

function getCompactFields(item: any): Array<{ key: string, label: string, value: any, type: string }> {
  return columns.value
    .filter(col => col !== 'id' && col !== 'nom' && col !== 'reference')
    .slice(0, 3)
    .map(col => ({
      key: col,
      label: getColumnLabel(col),
      value: getDisplayValue(item[col], col),
      type: typeof item[col] === 'number' ? 'number' : 'text'
    }))
}

function getAllFields(item: any): Array<{ key: string, label: string, value: any, type: string }> {
  return columns.value
    .filter(col => col !== 'id')
    .map(col => ({
      key: col,
      label: getColumnLabel(col),
      value: getDisplayValue(item[col], col),
      type: typeof item[col] === 'number' ? 'number' : 'text'
    }))
}

function getItemTags(item: any): string[] {
  const tags:any = []
  if (props.tableName === 'projets' && item.complet) tags.push('Complet')
  if (item.prix && item.prix > 1000) tags.push('Premium')
  return tags
}

// Actions
function selectItem(item: any) {
  if (selectedItems.value.has(item.id)) {
    selectedItems.value.delete(item.id)
    selectedItem.value = null
  } else {
    selectedItems.value.clear()
    selectedItems.value.add(item.id)
    selectedItem.value = item
  }
  emit('item-selected', item)
}

function closeModal() {
  selectedItem.value = null
}

function toggleEdit(item: any) {
  editingId.value = editingId.value === item.id ? null : item.id
  emit('item-edited', item)
}

function deleteItem(item: any) {
  if (confirm(`Êtes-vous sûr de vouloir supprimer cet élément ?`)) {
    emit('item-deleted', item)
  }
}

// Chargement des données
async function fetchData() {
  const urlBase = 'http://localhost:8000'

  try {
    const colRes = await axios.get(`${urlBase}/table-columns/${props.tableName}`)
    columns.value = colRes.data

    const dataRes = await axios.get(`${urlBase}/${props.tableName}`)
    rows.value = dataRes.data

    // Charger les données de référence si nécessaire
    if (columns.value.includes('fournisseur_id')) {
      const fournRes = await axios.get(`${urlBase}/fournisseurs`)
      fournisseurs.value = fournRes.data
    }

    if (columns.value.includes('client_id') || columns.value.includes('client')) {
      const clientRes = await axios.get(`${urlBase}/clients`)
      clients.value = clientRes.data
    }

    if (columns.value.includes('fpack_id')) {
      const fpackRes = await axios.get(`${urlBase}/fpacks`)
      fpacks.value = fpackRes.data
    }

    if (columns.value.includes('produit_id')) {
      const prodRes = await axios.get(`${urlBase}/produits`)
      produits.value = prodRes.data
    }

    filterableColumns.value.forEach(col => {
      filters.value[col] = []
    })

  } catch (error) {
    console.error('Erreur lors du chargement des données:', error)
  }
}

onMounted(fetchData)
</script>


<template>
  <div class="data-card-view">
    <!-- Header avec contrôles -->
    <div class="header-controls">
      <div class="view-info">
        <h2 class="table-title">{{ getTableDisplayName(tableName) }}</h2>
        <div class="item-count">{{ filteredAndSortedRows.length }} éléments</div>
      </div>
      
      <!-- Contrôles de vue -->
      <div class="controls-section">
        <!-- Barre de recherche -->
        <div class="search-container">
          <div class="search-input-wrapper">
            <svg class="search-icon" viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z" />
            </svg>
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Rechercher..." 
              class="search-input"
            />
          </div>
        </div>

        <!-- Layout toggles -->
        <div class="layout-controls">
          <button 
            @click="viewMode = 'grid'" 
            :class="['layout-btn', { active: viewMode === 'grid' }]"
            title="Vue grille"
          >
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M3,11H11V3H3M3,21H11V13H3M13,21H21V13H13M13,3V11H21V3" />
            </svg>
          </button>
          <button 
            @click="viewMode = 'list'" 
            :class="['layout-btn', { active: viewMode === 'list' }]"
            title="Vue liste"
          >
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M3,5H21V3H3M3,13H21V11H3M3,21H21V19H3" />
            </svg>
          </button>
          <button 
            @click="viewMode = 'masonry'" 
            :class="['layout-btn', { active: viewMode === 'masonry' }]"
            title="Vue mosaïque"
          >
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M3,3V11H11V3H3M13,3V9H21V3H13M3,13V21H11V13H3M13,11V21H21V11H13Z" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Filtres avancés (collapsible) -->
    <div v-if="showAdvancedFilters" class="advanced-filters">
      <div class="filters-grid">
        <div v-for="col in filterableColumns" :key="col" class="filter-group">
          <label class="filter-label">{{ getColumnLabel(col) }}</label>
          <select v-model="filters[col]" class="filter-select" multiple>
            <option v-for="value in [...columnValues[col] || []]" :key="value" :value="value">
              {{ getDisplayValue(value, col) }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Bouton pour afficher/masquer les filtres -->
    <button @click="showAdvancedFilters = !showAdvancedFilters" class="toggle-filters-btn">
      <svg viewBox="0 0 24 24" width="16" height="16">
        <path fill="currentColor" d="M14,12V19.88C14.04,20.18 13.94,20.5 13.71,20.71C13.32,21.1 12.69,21.1 12.3,20.71L10.29,18.7C10.06,18.47 9.96,18.16 10,17.87V12H9.97L4.21,4.62C3.87,4.19 3.95,3.56 4.38,3.22C4.57,3.08 4.78,3 5,3V3H19V3C19.22,3 19.43,3.08 19.62,3.22C20.05,3.56 20.13,4.19 19.79,4.62L14.03,12H14Z" />
      </svg>
      {{ showAdvancedFilters ? 'Masquer' : 'Filtres avancés' }}
    </button>

    <!-- Zone de contenu principal -->
    <div class="content-area" :class="[`view-${viewMode}`]">
      <!-- Mode grille -->
      <div v-if="viewMode === 'grid'" class="grid-container">
        <div 
          v-for="item in paginatedItems" 
          :key="item.id"
          class="data-card"
          @click="selectItem(item)"
          :class="{ 
            selected: selectedItems.has(item.id),
            editing: editingId === item.id 
          }"
        >
          <div class="card-header">
            <div class="card-title">
              {{ getPrimaryValue(item) }}
            </div>
            <div class="card-actions">
              <button @click.stop="toggleEdit(item)" class="action-btn edit-btn">
                <svg viewBox="0 0 24 24" width="16" height="16">
                  <path fill="currentColor" d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z" />
                </svg>
              </button>
              <button @click.stop="deleteItem(item)" class="action-btn delete-btn">
                <svg viewBox="0 0 24 24" width="16" height="16">
                  <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z" />
                </svg>
              </button>
            </div>
          </div>
          
          <div class="card-content">
            <div v-for="field in getVisibleFields(item)" :key="field.key" class="field-row">
              <span class="field-label">{{ field.label }}</span>
              <span class="field-value" :class="field.type">{{ field.value }}</span>
            </div>
          </div>
          
          <div class="card-footer">
            <div class="card-meta">
              <span class="item-id">#{{ item.id }}</span>
              <div class="card-tags">
                <span v-for="tag in getItemTags(item)" :key="tag" class="tag">{{ tag }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Mode liste -->
      <div v-else-if="viewMode === 'list'" class="list-container">
        <div 
          v-for="item in paginatedItems" 
          :key="item.id"
          class="list-item"
          @click="selectItem(item)"
          :class="{ 
            selected: selectedItems.has(item.id),
            editing: editingId === item.id 
          }"
        >
          <div class="list-item-main">
            <div class="list-item-primary">
              <h3 class="list-title">{{ getPrimaryValue(item) }}</h3>
              <span class="list-subtitle">{{ getSecondaryValue(item) }}</span>
            </div>
            
            <div class="list-item-fields">
              <div v-for="field in getCompactFields(item)" :key="field.key" class="compact-field">
                <span class="compact-label">{{ field.label }}:</span>
                <span class="compact-value">{{ field.value }}</span>
              </div>
            </div>
          </div>
          
          <div class="list-item-actions">
            <button @click.stop="toggleEdit(item)" class="action-btn">
              <svg viewBox="0 0 24 24" width="16" height="16">
                <path fill="currentColor" d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z" />
              </svg>
            </button>
            <button @click.stop="deleteItem(item)" class="action-btn delete-btn">
              <svg viewBox="0 0 24 24" width="16" height="16">
                <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Mode mosaïque -->
      <div v-else-if="viewMode === 'masonry'" class="masonry-container">
        <div 
          v-for="item in paginatedItems" 
          :key="item.id"
          class="masonry-item"
          @click="selectItem(item)"
          :class="{ 
            selected: selectedItems.has(item.id),
            editing: editingId === item.id 
          }"
        >
          <div class="masonry-header">
            <h3>{{ getPrimaryValue(item) }}</h3>
          </div>
          
          <div class="masonry-content">
            <div v-for="field in getAllFields(item)" :key="field.key" class="masonry-field">
              <div class="masonry-field-label">{{ field.label }}</div>
              <div class="masonry-field-value" :class="field.type">{{ field.value }}</div>
            </div>
          </div>
          
          <div class="masonry-actions">
            <button @click.stop="toggleEdit(item)" class="masonry-btn">
              Éditer
            </button>
            <button @click.stop="deleteItem(item)" class="masonry-btn delete">
              Supprimer
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="pagination">
      <button 
        @click="currentPage = Math.max(1, currentPage - 1)"
        :disabled="currentPage === 1"
        class="pagination-btn"
      >
        ←
      </button>
      
      <span class="pagination-info">
        Page {{ currentPage }} sur {{ totalPages }}
      </span>
      
      <button 
        @click="currentPage = Math.min(totalPages, currentPage + 1)"
        :disabled="currentPage === totalPages"
        class="pagination-btn"
      >
        →
      </button>
    </div>

    <!-- Modal de détails -->
    <div v-if="selectedItem" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>{{ getPrimaryValue(selectedItem) }}</h2>
          <button @click="closeModal" class="modal-close">×</button>
        </div>
        
        <div class="modal-body">
          <div class="modal-fields">
            <div v-for="field in getAllFields(selectedItem)" :key="field.key" class="modal-field">
              <label class="modal-field-label">{{ field.label }}</label>
              <div class="modal-field-value" :class="field.type">{{ field.value }}</div>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="toggleEdit(selectedItem)" class="modal-btn primary">
            Éditer
          </button>
          <button @click="deleteItem(selectedItem)" class="modal-btn danger">
            Supprimer
          </button>
          <button @click="closeModal" class="modal-btn">
            Fermer
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.data-card-view {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding: 2rem;
}

.header-controls {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 1rem;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
}

.view-info .table-title {
  font-size: 2rem;
  font-weight: 700;
  color: #2d3748;
  margin: 0;
}

.item-count {
  color: #718096;
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.controls-section {
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.search-container {
  position: relative;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 1rem;
  color: #a0aec0;
  z-index: 1;
}

.search-input {
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  border: 2px solid #e2e8f0;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  min-width: 300px;
  transition: all 0.2s ease;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.layout-controls {
  display: flex;
  gap: 0.5rem;
  background: #f7fafc;
  padding: 0.25rem;
  border-radius: 0.5rem;
}

.layout-btn {
  padding: 0.5rem;
  border: none;
  background: transparent;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #718096;
}

.layout-btn:hover {
  background: #e2e8f0;
  color: #2d3748;
}

.layout-btn.active {
  background: #667eea;
  color: white;
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
}

.toggle-filters-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
  margin-bottom: 1rem;
}

.toggle-filters-btn:hover {
  background: #5a67d8;
  transform: translateY(-1px);
}

.advanced-filters {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 1rem;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-label {
  font-weight: 500;
  color: #2d3748;
  font-size: 0.9rem;
}

.filter-select {
  padding: 0.5rem;
  border: 2px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.9rem;
}

.content-area {
  margin-bottom: 2rem;
}

/* Mode grille */
.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

.data-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.data-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.data-card.selected {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.card-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #2d3748;
  line-height: 1.2;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.data-card:hover .card-actions {
  opacity: 1;
}

.action-btn {
  padding: 0.375rem;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #f7fafc;
  color: #718096;
}

.action-btn:hover {
  transform: scale(1.05);
}

.edit-btn:hover {
  background: #667eea;
  color: white;
}

.delete-btn:hover {
  background: #f56565;
  color: white;
}

.card-content {
  margin-bottom: 1rem;
}

.field-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f1f5f9;
}

.field-row:last-child {
  border-bottom: none;
}

.field-label {
  font-size: 0.875rem;
  color: #718096;
  font-weight: 500;
}

.field-value {
  font-size: 0.875rem;
  color: #2d3748;
  font-weight: 500;
  text-align: right;
}

.field-value.number {
  background: #e6fffa;
  color: #065f46;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-family: 'JetBrains Mono', monospace;
}

.card-footer {
  border-top: 1px solid #f1f5f9;
  padding-top: 1rem;
}

.card-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.item-id {
  font-size: 0.75rem;
  color: #a0aec0;
  font-weight: 500;
}

.card-tags {
  display: flex;
  gap: 0.5rem;
}

.tag {
  background: #667eea;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 500;
}

/* Mode liste */
.list-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 1rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
  transition: all 0.2s ease;
}

.list-item:last-child {
  border-bottom: none;
}

.list-item:hover {
  background: rgba(102, 126, 234, 0.05);
  transform: translateX(4px);
}

.list-item.selected {
  background: rgba(102, 126, 234, 0.1);
  border-left: 4px solid #667eea;
}

.list-item-main {
  display: flex;
  align-items: center;
  gap: 2rem;
  flex: 1;
}

.list-item-primary {
  min-width: 200px;
}

.list-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #2d3748;
  margin: 0 0 0.25rem 0;
}

.list-subtitle {
  font-size: 0.875rem;
  color: #718096;
}

.list-item-fields {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}

.compact-field {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.compact-label {
  font-size: 0.875rem;
  color: #718096;
  font-weight: 500;
}

.compact-value {
  font-size: 0.875rem;
  color: #2d3748;
  font-weight: 600;
}

.list-item-actions {
  display: flex;
  gap: 0.5rem;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.list-item:hover .list-item-actions {
  opacity: 1;
}

/* Mode mosaïque */
.masonry-container {
  columns: 3;
  column-gap: 1.5rem;
}

@media (max-width: 1200px) {
  .masonry-container {
    columns: 2;
  }
}

@media (max-width: 768px) {
  .masonry-container {
    columns: 1;
  }
}

.masonry-item {
  display: inline-block;
  width: 100%;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 1rem;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  break-inside: avoid;
}

.masonry-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.masonry-item.selected {
  border-color: #667eea;
}

.masonry-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #2d3748;
  margin: 0 0 1rem 0;
}

.masonry-content {
  margin-bottom: 1rem;
}

.masonry-field {
  margin-bottom: 0.75rem;
}

.masonry-field-label {
  font-size: 0.875rem;
  color: #718096;
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.masonry-field-value {
  font-size: 0.875rem;
  color: #2d3748;
  font-weight: 500;
}

.masonry-field-value.number {
  background: #e6fffa;
  color: #065f46;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-family: 'JetBrains Mono', monospace;
  display: inline-block;
}

.masonry-actions {
  display: flex;
  gap: 0.5rem;
  border-top: 1px solid #f1f5f9;
  padding-top: 1rem;
}

.masonry-btn {
  flex: 1;
  padding: 0.5rem;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #f7fafc;
  color: #718096;
}

.masonry-btn:hover {
  background: #667eea;
  color: white;
  transform: translateY(-1px);
}

.masonry-btn.delete:hover {
  background: #f56565;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 0.5rem;
  padding: 1rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.pagination-btn {
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #f7fafc;
  color: #718096;
  font-weight: 500;
}

.pagination-btn:hover:not(:disabled) {
  background: #667eea;
  color: white;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-info {
  font-size: 0.875rem;
  color: #718096;
  font-weight: 500;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 2rem;
}

.modal-content {
  background: white;
  border-radius: 1rem;
  max-width: 600px;
  max-height: 80vh;
  width: 100%;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-50px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2rem;
  border-bottom: 1px solid #f1f5f9;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
}

.modal-close {
  background: none;
  border: none;
  font-size: 2rem;
  color: white;
  cursor: pointer;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.2s ease;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.2);
}

.modal-body {
  padding: 2rem;
  max-height: 60vh;
  overflow-y: auto;
}

.modal-fields {
  display: grid;
  gap: 1.5rem;
}

.modal-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.modal-field-label {
  font-size: 0.875rem;
  color: #718096;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.modal-field-value {
  font-size: 1rem;
  color: #2d3748;
  font-weight: 500;
  padding: 0.75rem;
  background: #f7fafc;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
}

.modal-field-value.number {
  background: #e6fffa;
  color: #065f46;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 2rem;
  border-top: 1px solid #f1f5f9;
  background: #fafafa;
}

.modal-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
  background: #f7fafc;
  color: #718096;
}

.modal-btn.primary {
  background: #667eea;
  color: white;
}

.modal-btn.primary:hover {
  background: #5a67d8;
  transform: translateY(-1px);
}

.modal-btn.danger {
  background: #f56565;
  color: white;
}

.modal-btn.danger:hover {
  background: #e53e3e;
  transform: translateY(-1px);
}

.modal-btn:hover {
  background: #e2e8f0;
}

/* Responsive */
@media (max-width: 768px) {
  .data-card-view {
    padding: 1rem;
  }

  .header-controls {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .controls-section {
    flex-direction: column;
    gap: 1rem;
  }

  .search-input {
    min-width: auto;
    width: 100%;
  }

  .grid-container {
    grid-template-columns: 1fr;
  }

  .list-item-main {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .list-item-fields {
    gap: 1rem;
  }

  .modal-content {
    margin: 1rem;
    max-height: 90vh;
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 1rem;
  }

  .modal-footer {
    flex-direction: column;
  }
}

/* Animations et micro-interactions */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.data-card,
.list-item,
.masonry-item {
  animation: fadeInUp 0.3s ease-out;
}

/* États de chargement */
.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  color: #718096;
}

/* Scrollbar personnalisée */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}
</style>