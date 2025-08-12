<!-- TableViewer.vue -->
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import Card from './Card.vue'
import axios from 'axios'
import { getTableConfig, type TableAction } from '../../composables/Cards/TableConfig'
import { showToast } from '../../composables/useToast'

const props = defineProps<{
  tableName: string
  title?: string
}>()

const emit = defineEmits(['add-item', 'import-success'])

const router = useRouter()

const loading = ref(false)
const rows = ref<Record<string, any>[]>([])
const columns = ref<{ name: string; label: string }[]>([])
const compact = ref(false)
const searchQuery = ref('')
const sortField = ref('')
const sortOrder = ref<'asc' | 'desc'>('asc')
const selectedFilter = ref('')
const showStats = ref(false)
const viewMode = ref<'grid' | 'list'>('grid')
const gridRef = ref<HTMLElement>()
const searchInputRef = ref<HTMLInputElement>()
const fileInputRef = ref<HTMLInputElement>()

// États d'animation et d'interaction
const isRefreshing = ref(false)
const showFilters = ref(false)
const animateCards = ref(false)
const scrollProgress = ref(0)
const isSearchFocused = ref(false)
const isImporting = ref(false)
const isExporting = ref(false)

// Configuration de la table
const tableConfig = computed(() => getTableConfig(props.tableName))

// Filtres dynamiques basés sur les données
const availableFilters = computed(() => {
  const filters: { label: string; field: string; values: string[] }[] = []
  
  if (rows.value.length === 0) return filters
  
  // Détecter les champs catégoriels (moins de 10 valeurs uniques)
  columns.value.forEach(col => {
    const uniqueValues = [...new Set(rows.value.map(row => row[col.name]))]
      .filter(val => val != null && val !== '')
      .slice(0, 10)
    
    if (uniqueValues.length > 1 && uniqueValues.length <= 8) {
      filters.push({
        label: col.label,
        field: col.name,
        values: uniqueValues.map(String).sort()
      })
    }
  })
  
  return filters
})

// Statistiques des données
const dataStats = computed(() => {
  const total = rows.value.length
  const filtered = filteredAndSortedRows.value.length
  
  const numericFields = columns.value.filter(col => {
    const sampleValue = rows.value[0]?.[col.name]
    return typeof sampleValue === 'number' || !isNaN(Number(sampleValue))
  })
  
  return {
    total,
    filtered,
    columns: columns.value.length,
    numericFields: numericFields.length
  }
})

// Actions spéciales avec icônes emoji
const specialActions = [
  { 
    label: 'Inspecter', 
    icon: '🔍',
    onClick: (row: any) => {
      console.log('Inspect:', row)
      alert(JSON.stringify(row, null, 2))
    }
  },
  {
    label: 'Partager',
    icon: '📤',
    onClick: (row: any) => {
      console.log('Share:', row)
    }
  }
]

// Filtrage et tri des données
const filteredAndSortedRows = computed(() => {
  let result = [...rows.value]
  
  // Filtrage textuel
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase().trim()
    result = result.filter(row =>
      Object.values(row).some(val =>
        String(val).toLowerCase().includes(query)
      )
    )
  }
  
  // Filtrage par catégorie
  if (selectedFilter.value) {
    const [field, value] = selectedFilter.value.split(':')
    result = result.filter(row => String(row[field]) === value)
  }
  
  // Tri
  if (sortField.value) {
    result.sort((a, b) => {
      const aVal = a[sortField.value]
      const bVal = b[sortField.value]
      
      if (aVal == null) return 1
      if (bVal == null) return -1
      
      let comparison = 0
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        comparison = aVal - bVal
      } else {
        comparison = String(aVal).localeCompare(String(bVal))
      }
      
      return sortOrder.value === 'desc' ? -comparison : comparison
    })
  }
  
  return result
})

// Gestion des actions de boutons
const handleAction = async (action: TableAction) => {
  switch (action.action) {
    case 'add':
      emit('add-item')
      break
    case 'export':
      await exportFile(action.url!)
      break
    case 'import':
      triggerImport(action.url!)
      break
    case 'custom':
      if (action.routeTo) {
        router.push(action.routeTo)
      } else if (action.customHandler) {
        action.customHandler()
      }
      break
  }
}

// Export
const exportFile = async (url: string) => {
  if (isExporting.value) return
  
  isExporting.value = true
  
  try {
    const response = await fetch(url)
    if (!response.ok) throw new Error('Erreur lors de l\'export')
    
    const blob = await response.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = `${props.tableName}.xlsx`
    a.click()
    window.URL.revokeObjectURL(downloadUrl)
    
    showToast('Export terminé avec succès', "#4ade80")
  } catch (err:any) {
    showToast(`Erreur: ${err.message}`, "#f87171")
  } finally {
    isExporting.value = false
  }
}

// Import
const triggerImport = (url: string) => {
  if (fileInputRef.value) {
    fileInputRef.value.setAttribute('data-url', url)
    fileInputRef.value.value = ''
    fileInputRef.value.click()
  }
}

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const url = target.getAttribute('data-url')
  
  if (target.files && target.files.length > 0 && url) {
    const file = target.files[0]
    isImporting.value = true
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      })
      
      if (response.ok) {
        await fetchData()
        emit('import-success')
        showToast('Import terminé avec succès', "#4ade80")
      } else {
        const err = await response.json()
        showToast(`Erreur : ${err.detail}`, "#f87171")
      }
    } catch (err: any) {
      showToast(`Erreur: ${err.message}`, "#f87171")
    } finally {
      isImporting.value = false
      target.removeAttribute('data-url')
    }
  }
}

// Gestion du tri
const handleSort = (field: string) => {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortOrder.value = 'asc'
  }
  
  animateCards.value = true
  setTimeout(() => {
    animateCards.value = false
  }, 600)
}

// Gestion du scroll pour la barre de progression
const handleScroll = () => {
  const element = document.documentElement
  const scrollTop = element.scrollTop
  const scrollHeight = element.scrollHeight - element.clientHeight
  scrollProgress.value = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0
}

// Actions principales
const toggleCompact = () => {
  compact.value = !compact.value
  if (gridRef.value) {
    gridRef.value.style.transform = 'scale(0.98)'
    setTimeout(() => {
      if (gridRef.value) {
        gridRef.value.style.transform = 'scale(1)'
      }
    }, 150)
  }
}

const toggleViewMode = () => {
  const modes: ('grid' | 'list')[] = ['grid', 'list']
  const currentIndex = modes.indexOf(viewMode.value)
  viewMode.value = modes[(currentIndex + 1) % modes.length]
}

const clearSearch = () => {
  searchQuery.value = ''
  nextTick(() => {
    searchInputRef.value?.focus()
  })
}

const clearFilters = () => {
  selectedFilter.value = ''
  sortField.value = ''
  searchQuery.value = ''
}

async function fetchData() {
  loading.value = true
  isRefreshing.value = true
  
  try {
    const [colsRes, dataRes] = await Promise.all([
      axios.get(`http://localhost:8000/table-columns/${props.tableName}`),
      axios.get(`http://localhost:8000/${props.tableName}`)
    ])
    
    columns.value = colsRes.data
    rows.value = dataRes.data
    
    await nextTick()
    animateCards.value = true
    setTimeout(() => {
      animateCards.value = false
    }, 800)
    
  } catch (err) {
    console.error('Erreur de récupération des données', err)
  } finally {
    loading.value = false
    isRefreshing.value = false
  }
}

const refresh = async () => {
  await fetchData()
}

// Handlers pour les actions des cartes
const editRow = (row: any) => {
  console.log('Edit:', row)
}

const deleteRow = (row: any) => {
  console.log('Delete:', row)
}

const duplicateRow = (row: any) => {
  console.log('Duplicate:', row)
}

const exportRow = (row: any) => {
  console.log('Export:', row)
}

// Raccourcis clavier
const handleKeydown = (e: KeyboardEvent) => {
  if (e.ctrlKey || e.metaKey) {
    switch (e.key) {
      case 'f':
        e.preventDefault()
        searchInputRef.value?.focus()
        break
      case 'r':
        e.preventDefault()
        refresh()
        break
    }
  }
  
  if (e.key === 'Escape') {
    if (isSearchFocused.value) {
      searchInputRef.value?.blur()
    } else if (showFilters.value) {
      showFilters.value = false
    }
  }
}

// Watchers
watch(searchQuery, () => {
  if (searchQuery.value) {
    animateCards.value = true
    setTimeout(() => {
      animateCards.value = false
    }, 300)
  }
})

onMounted(() => {
  fetchData()
  window.addEventListener('scroll', handleScroll)
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="table-viewer">
    <!-- Input caché pour l'import -->
    <input
      type="file"
      accept=".xlsx"
      ref="fileInputRef"
      style="display: none"
      @change="handleFileChange"
    />
    
    <!-- Barre de progression du scroll -->
    <div class="scroll-progress" :style="{ width: scrollProgress + '%' }"></div>
    
    <!-- En-tête avec titre et actions -->
    <header class="tv-header">
      <div class="header-left">
        <h1 class="tv-title">
          <span class="title-icon">📊</span>
          {{ title || tableConfig.displayName }}
          <span class="title-badge" v-if="dataStats.filtered !== dataStats.total">
            {{ dataStats.filtered }}/{{ dataStats.total }}
          </span>
          <span class="title-badge" v-else>
            {{ dataStats.total }}
          </span>
        </h1>
        
        <button 
          class="stats-toggle" 
          @click="showStats = !showStats"
          :class="{ active: showStats }"
          title="Afficher les statistiques"
        >
          <span class="stats-icon">📈</span>
        </button>
      </div>
      
      <div class="header-actions">        
        <!-- Boutons d'action configurables -->
        <div class="action-buttons">
          <button
            v-for="action in tableConfig.actions"
            :key="action.label"
            class="action-btn"
            :class="`action-btn--${action.variant}`"
            :disabled="(action.action === 'import' && isImporting) || (action.action === 'export' && isExporting)"
            @click="handleAction(action)"
            :title="action.label"
          >
            <span class="btn-icon">{{ action.icon }}</span>
            <span class="btn-label">{{ action.label }}</span>
            
            <!-- Loader pour import/export -->
            <span 
              v-if="(action.action === 'import' && isImporting) || (action.action === 'export' && isExporting)" 
              class="btn-loader"
            ></span>
          </button>
        </div>
      </div>
    </header>

    <!-- Panneau de statistiques -->
    <transition name="stats">
      <div v-if="showStats" class="stats-panel">
        <div class="stat-item">
          <div class="stat-icon">📋</div>
          <div class="stat-content">
            <div class="stat-value">{{ dataStats.total }}</div>
            <div class="stat-label">Enregistrements</div>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon">🔍</div>
          <div class="stat-content">
            <div class="stat-value">{{ dataStats.filtered }}</div>
            <div class="stat-label">Filtrés</div>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon">📊</div>
          <div class="stat-content">
            <div class="stat-value">{{ dataStats.columns }}</div>
            <div class="stat-label">Colonnes</div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Barre d'outils principale -->
    <div class="tv-toolbar">
      <!-- Recherche avancée -->
      <div class="search-container" :class="{ focused: isSearchFocused, active: searchQuery }">
        <div class="search-icon">🔍</div>
        <input
          ref="searchInputRef"
          type="text"
          v-model="searchQuery"
          placeholder="Rechercher dans tous les champs... (Ctrl+F)"
          class="search-input"
          @focus="isSearchFocused = true"
          @blur="isSearchFocused = false"
        />
        <button 
          v-if="searchQuery" 
          class="search-clear"
          @click="clearSearch"
          title="Effacer la recherche"
        >
          ✕
        </button>

              <!-- Contrôles de vue et tri -->
      <div class="toolbar-controls">
        <!-- Tri -->
        <div class="sort-controls" v-if="columns.length > 0">
          <select 
            v-model="sortField" 
            class="sort-select"
            title="Trier par"
          >
            <option value="">Sans tri</option>
            <option v-for="col in columns" :key="col.name" :value="col.name">
              {{ col.label }}
            </option>
          </select>
          
          <button 
            v-if="sortField"
            class="sort-order-btn"
            @click="handleSort(sortField)"
            :title="sortOrder === 'asc' ? 'Tri croissant' : 'Tri décroissant'"
          >
            <span v-if="sortOrder === 'asc'">↑</span>
            <span v-else>↓</span>
          </button>
        </div>

        <!-- Filtres -->
        <div class="filter-controls" v-if="availableFilters.length > 0">
          <button 
            class="filter-toggle"
            @click="showFilters = !showFilters"
            :class="{ active: showFilters || selectedFilter }"
            title="Filtres"
          >
            <span class="filter-icon">🔽</span>
            <span class="filter-count" v-if="selectedFilter">1</span>
          </button>
        </div>

        <!-- Modes d'affichage -->
        <div class="view-controls">
          <button 
            class="view-mode-btn"
            @click="toggleViewMode"
            :title="`Mode: ${viewMode}`"
          >
            <span v-if="viewMode === 'grid'">⊞</span>
            <span v-else>☰</span>
          </button>
          
          <button 
            class="compact-btn"
            @click="toggleCompact"
            :class="{ active: compact }"
            :title="compact ? 'Mode détaillé' : 'Mode compact'"
          >
            <span v-if="compact">📄</span>
            <span v-else>🗜️</span>
          </button>
        </div>

        <!-- Bouton de reset -->
        <button 
          v-if="searchQuery || selectedFilter || sortField"
          class="clear-all-btn"
          @click="clearFilters"
          title="Tout effacer"
        >
          🗑️
        </button>
      </div>

      </div>


    </div>

    <!-- Panneau de filtres -->
    <transition name="filters">
      <div v-if="showFilters && availableFilters.length > 0" class="filters-panel">
        <div class="filters-header">
          <h3>Filtres disponibles</h3>
          <button class="close-filters" @click="showFilters = false">✕</button>
        </div>
        <div class="filters-grid">
          <div v-for="filter in availableFilters" :key="filter.field" class="filter-group">
            <h4 class="filter-title">{{ filter.label }}</h4>
            <div class="filter-options">
              <label 
                v-for="value in filter.values" 
                :key="value" 
                class="filter-option"
              >
                <input 
                  type="radio"
                  :name="filter.field"
                  :value="filter.field + ':' + value"
                  v-model="selectedFilter"
                />
                <span class="filter-value">{{ value }}</span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Grille principale -->
    <main class="tv-main">
      <!-- Loader élégant -->
      <div v-if="loading" class="tv-loader">
        <div class="loader-spinner"></div>
        <p>Chargement des données...</p>
      </div>

      <!-- Message vide -->
      <div v-else-if="!loading && filteredAndSortedRows.length === 0" class="tv-empty">
        <div class="empty-icon">📭</div>
        <h3>Aucun enregistrement trouvé</h3>
        <p v-if="searchQuery || selectedFilter">
          Essayez de modifier vos critères de recherche
        </p>
        <p v-else>
          Cette table ne contient pas encore de données
        </p>
      </div>

      <!-- Grille de cartes -->
      <div 
        v-else
        ref="gridRef"
        class="tv-grid"
        :class="{
          [`tv-grid--${viewMode}`]: true,
          'tv-grid--compact': compact,
          'tv-grid--animate': animateCards
        }"
      >
        <Card
          v-for="(row, index) in filteredAndSortedRows"
          :key="`${row.id || index}-${searchQuery}-${selectedFilter}`"
          :row="row"
          :columns="columns.map(c => c.name)"
          :compact="compact"
          :card-index="index"
          :special-actions="specialActions"
          :style="{ '--card-delay': (index % 20) * 0.05 + 's' }"
          class="table-viewer-card"
          @edit="editRow"
          @delete="deleteRow"
          @duplicate="duplicateRow"
          @export="exportRow"
        />
      </div>
    </main>
  </div>
</template>

<style scoped>
.table-viewer {
  height: 90vh;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Barre de progression du scroll */
.scroll-progress {
  position: fixed;
  top: 0;
  left: 0;
  height: 3px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  transition: width 0.1s ease;
  z-index: 1000;
}

/* En-tête */
.tv-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2rem 2rem 1rem;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  gap: 2rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.tv-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: #1e293b;
}

.title-icon {
  font-size: 1.5rem;
}

.title-badge {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.875rem;
  font-weight: 600;
}

.stats-toggle {
  background: rgba(204, 204, 204, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 0.5rem;
  padding: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
}

.stats-toggle:hover,
.stats-toggle.active {
  background: #3b82f6;
  color: white;
  transform: translateY(-2px);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.control-buttons {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  padding-right: 1.5rem;
  border-right: 1px solid rgba(255, 255, 255, 0.3);
}

.action-buttons {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.action-btn {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  font-weight: 600;
  font-size: 0.875rem;
  border-radius: 0.75rem;
  border: none;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(20px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

/* Variants des boutons */
.action-btn--primary {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: white;
}

.action-btn--primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
}

.action-btn--success {
  background: linear-gradient(135deg, #10b981, #06d6a0);
  color: white;
}

.action-btn--success:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669, #05a087);
  box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
}

.action-btn--warning {
  background: linear-gradient(135deg, #f59e0b, #f97316);
  color: white;
}

.action-btn--warning:hover:not(:disabled) {
  background: linear-gradient(135deg, #d97706, #ea580c);
  box-shadow: 0 8px 25px rgba(245, 158, 11, 0.4);
}

.action-btn--danger {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
}

.action-btn--danger:hover:not(:disabled) {
  background: linear-gradient(135deg, #dc2626, #b91c1c);
  box-shadow: 0 8px 25px rgba(239, 68, 68, 0.4);
}

.action-btn--secondary {
  background: linear-gradient(135deg, #64748b, #475569);
  color: white;
}

.action-btn--secondary:hover:not(:disabled) {
  background: linear-gradient(135deg, #475569, #334155);
  box-shadow: 0 8px 25px rgba(100, 116, 139, 0.4);
}

.btn-icon {
  font-size: 1rem;
}

.btn-label {
  font-weight: 600;
  white-space: nowrap;
}

.btn-loader {
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  width: 14px;
  height: 14px;
  animation: spin 1s linear infinite;
  margin-left: 0.25rem;
}

.refresh-btn.refreshing .btn-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Panneau de statistiques */
.stats-panel {
  display: flex;
  gap: 1rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  min-width: 120px;
}

.stat-icon {
  font-size: 1.5rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 0.875rem;
  color: #64748b;
  font-weight: 500;
}

/* Barre d'outils */
.tv-toolbar {
  display: flex;
  gap: 0.5rem;
  padding: 1rem 2rem;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  align-items: center;
}

/* Recherche */
.search-container {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid transparent;
  border-radius: 1rem;
  padding: 0 1rem;
  transition: all 0.3s ease;
  backdrop-filter: blur(20px);
  max-width: 400px;
}

.search-container.focused {
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
}

.search-container.active {
  background: rgba(59, 130, 246, 0.1);
}

.search-icon {
  color: #64748b;
  margin-right: 0.5rem;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  padding: 0.875rem 0;
  background: transparent;
  font-size: 1rem;
  color: #1e293b;
}

.search-input::placeholder {
  color: #94a3b8;
}

.search-clear {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.25rem;
  transition: all 0.2s ease;
}

.search-clear:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

/* Contrôles */
.toolbar-controls {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.sort-controls,
.filter-controls,
.view-controls {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.sort-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  cursor: pointer;
  transition: all 0.2s ease;
}

.sort-select:hover,
.sort-select:focus {
  border-color: #3b82f6;
  outline: none;
}

.sort-order-btn,
.filter-toggle,
.view-mode-btn,
.compact-btn,
.clear-all-btn {
  position: relative;
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
  min-width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sort-order-btn:hover,
.filter-toggle:hover,
.view-mode-btn:hover,
.compact-btn:hover {
  background: #3b82f6;
  color: white;
  transform: translateY(-2px);
}

.filter-toggle.active,
.compact-btn.active {
  background: #3b82f6;
  color: white;
}

.filter-count {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #ef4444;
  color: white;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-all-btn {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.clear-all-btn:hover {
  background: #ef4444;
  color: white;
}

/* Panneau de filtres */
.filters-panel {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 1.5rem 2rem;
}

.filters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.filters-header h3 {
  margin: 0;
  color: #1e293b;
  font-size: 1.125rem;
  font-weight: 600;
}

.close-filters {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.25rem;
  transition: all 0.2s ease;
}

.close-filters:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.filter-group {
  background: rgba(255, 255, 255, 0.8);
  padding: 1rem;
  border-radius: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.filter-title {
  margin: 0 0 0.75rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.filter-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
}

.filter-option:hover {
  background: rgba(59, 130, 246, 0.1);
}

.filter-option input[type="radio"] {
  margin: 0;
}

.filter-value {
  font-size: 0.875rem;
  color: #1e293b;
}

/* Contenu principal */
.tv-main {
  padding: 2rem;
  flex: 1;
  overflow-y: auto;
}

/* Loader */
.tv-loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  color: #64748b;
  height: 300px;
}

.loader-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e2e8f0;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

/* Message vide */
.tv-empty {
  text-align: center;
  padding: 4rem;
  color: #64748b;
  height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.tv-empty h3 {
  margin: 0 0 0.5rem 0;
  color: #1e293b;
  font-size: 1.5rem;
}

.tv-empty p {
  margin: 0;
  font-size: 1rem;
}

/* Grille de cartes */
.tv-grid {
  display: grid;
  gap: 1.5rem;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  height: auto;
  padding-right: 8px;
}

.tv-main::-webkit-scrollbar {
  width: 8px;
}

.tv-main::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  margin: 8px 0;
}

.tv-main::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-radius: 4px;
  transition: all 0.2s ease;
}

.tv-main::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
}

.tv-grid--grid {
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
}

.tv-grid--grid.tv-grid--compact {
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}

.tv-grid--list {
  grid-template-columns: 1fr;
  max-width: 800px;
  margin: 0 auto;
}

.tv-grid--animate .card {
  animation: cardEnter 0.6s cubic-bezier(0.4, 0, 0.2, 1) var(--card-delay) both;
}

@keyframes cardEnter {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Transitions */
.stats-enter-active,
.stats-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.stats-enter-from {
  opacity: 0;
  transform: translateY(-20px);
  max-height: 0;
}

.stats-leave-to {
  opacity: 0;
  transform: translateY(-20px);
  max-height: 0;
}

.stats-enter-to,
.stats-leave-from {
  opacity: 1;
  transform: translateY(0);
  max-height: 200px;
}

.filters-enter-active,
.filters-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.filters-enter-from {
  opacity: 0;
  transform: translateY(-30px);
  max-height: 0;
}

.filters-leave-to {
  opacity: 0;
  transform: translateY(-30px);
  max-height: 0;
}

.filters-enter-to,
.filters-leave-from {
  opacity: 1;
  transform: translateY(0);
  max-height: 500px;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .tv-header {
    padding: 1.5rem 1rem 1rem;
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .header-left {
    justify-content: space-between;
    width: 100%;
  }
  
  .header-actions {
    justify-content: space-between;
    width: 100%;
  }
  
  .control-buttons {
    border-right: none;
    padding-right: 0;
  }
  
  .tv-toolbar {
    padding: 1rem;
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .toolbar-controls {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .search-container {
    max-width: none;
  }
  
  .tv-main {
    padding: 1rem;
  }
  
  .tv-grid {
    max-height: calc(100vh - 250px);
  }
  
  .tv-grid--grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
  
  .tv-grid--grid.tv-grid--compact {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  }
  
  .stats-panel {
    padding: 1rem;
    flex-wrap: wrap;
  }
  
  .filters-panel {
    padding: 1rem;
  }
  
  .filters-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .tv-title {
    font-size: 1.5rem;
  }
  
  .action-buttons,
  .control-buttons {
    flex-direction: column;
    width: 100%;
  }
  
  .action-btn {
    width: 100%;
    justify-content: center;
  }
  
  .toolbar-controls {
    gap: 0.25rem;
  }
  
  .tv-grid {
    max-height: calc(100vh - 350px);
  }
  
  .tv-grid--grid {
    grid-template-columns: 1fr;
  }
  
  .tv-grid--grid.tv-grid--compact {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  }
  
  .stats-panel {
    flex-direction: column;
  }
  
  .stat-item {
    min-width: auto;
  }
}

/* Styles pour les cartes dans TableViewer */
.table-viewer-card {
  height: fit-content;
}

.table-viewer-card :deep(.modern-card.expanded) {
  z-index: 10;
}

.table-viewer-card :deep(.floating-menu-overlay) {
  z-index: 9999;
}

/* Améliorations d'accessibilité */
.action-btn:focus-visible,
.sort-select:focus-visible,
.filter-option:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Animations d'entrée */
.tv-header,
.stats-panel,
.tv-toolbar,
.tv-main {
  animation: slideInDown 0.6s cubic-bezier(0.4, 0, 0.2, 1) both;
}

.tv-toolbar {
  animation-delay: 0.1s;
}

.tv-main {
  animation-delay: 0.2s;
}

@keyframes slideInDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Hover effects personnalisés */
.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.filter-group:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}
</style>