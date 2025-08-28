<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import TreeItem from './TreeItem.vue'

const props = defineProps({
  projets: {
    type: Array,
    default: () => []
  },
  clients: {
    type: Array,
    default: () => []
  },
  fpacks: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'create-project',
  'edit-project',
  'delete-project',
  'create-subproject',
  'edit-subproject',
  'delete-subproject',
  'associate-fpack',
  'remove-fpack',
  'complete-fpack'
])

const searchQuery = ref('')
const selectedClient = ref('')
const statusFilter = ref('')
const viewDensity = ref('compact')
const expandedItems = ref(new Set())
const allExpanded = ref(false)

const scrollContainer = ref(null)
const scrollTop = ref(0)
const containerHeight = ref(600)
const itemHeight = computed(() => {
  switch (viewDensity.value) {
    case 'compact': return 60
    default: return 80
  }
})
const visibleCount = computed(() => Math.ceil(containerHeight.value / itemHeight.value) + 2)

const treeItems = computed(() => {
  const items = []
  
  filteredProjects.value.forEach(project => {
    const projectItem = {
      id: project.id,
      uniqueId: `project-${project.id}`,
      type: 'project',
      level: 0,
      data: project,
      expanded: expandedItems.value.has(`project-${project.id}`),
      children: []
    }
    
    items.push(projectItem)

    if (projectItem.expanded) {
      project.sous_projets.forEach(subproject => {
        const subprojectItem = {
          id: subproject.id,
          uniqueId: `subproject-${subproject.id}`,
          type: 'subproject',
          level: 1,
          data: subproject,
          parent: project,
          expanded: expandedItems.value.has(`subproject-${subproject.id}`),
          children: []
        }
        
        items.push(subprojectItem)
        
        if (subprojectItem.expanded) {
          if (subproject.fpacks && Array.isArray(subproject.fpacks) && subproject.fpacks.length > 0) {
            subproject.fpacks.forEach((fpack) => {
              const fpackItem = {
                id: fpack.id, 
                uniqueId: `fpack-${fpack.id}`, 
                type: 'fpack',
                level: 2,
                data: {
                  ...fpack,
                  sous_projet_id: subproject.id,
                  sous_projet_nom: subproject.nom
                },
                parent: subproject,
                expanded: false
              }
              
              items.push(fpackItem)
            })
          }
        }
      })
    }
  })
  
  return items
})

const filteredProjects = computed(() => {
  let filtered = props.projets

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(project => 
      project.projet.toLowerCase().includes(query) ||
      project.client_nom.toLowerCase().includes(query) ||
      project.sous_projets.some(sp => {
        if (sp.nom.toLowerCase().includes(query)) return true
        if (sp.fpacks && sp.fpacks.length > 0) {
          return sp.fpacks.some(fpack => 
            (fpack.fpack_nom && fpack.fpack_nom.toLowerCase().includes(query)) ||
            (fpack.Robot_Location_Code && fpack.Robot_Location_Code.toLowerCase().includes(query)) ||
            (fpack.FPack_number && fpack.FPack_number.toString().toLowerCase().includes(query))
          )
        }
        return false
      })
    )
  }

  if (selectedClient.value) {
    filtered = filtered.filter(project => project.client_nom === selectedClient.value)
  }

  if (statusFilter.value) {
    filtered = filtered.filter(project => {
      const completedSubs = project.sous_projets.filter(sp => sp.complet).length
      const totalSubs = project.sous_projets.length
      
      switch (statusFilter.value) {
        case 'complete':
          return totalSubs > 0 && completedSubs === totalSubs
        case 'in-progress':
          return completedSubs > 0 && completedSubs < totalSubs
        case 'pending':
          return completedSubs === 0
        default:
          return true
      }
    })
  }

  return filtered
})

const virtualHeight = computed(() => treeItems.value.length * itemHeight.value)
const startIndex = computed(() => Math.floor(scrollTop.value / itemHeight.value))
const endIndex = computed(() => Math.min(startIndex.value + visibleCount.value, treeItems.value.length))
const visibleItems = computed(() => treeItems.value.slice(startIndex.value, endIndex.value))
const offsetY = computed(() => startIndex.value * itemHeight.value)

const totalSubprojects = computed(() => 
  filteredProjects.value.reduce((sum, p) => sum + p.sous_projets.length, 0)
)

const totalFpacks = computed(() =>
  filteredProjects.value.reduce((sum, p) => 
    sum + p.sous_projets.reduce((subSum, sp) => {
      if (sp.fpacks && Array.isArray(sp.fpacks)) {
        return subSum + sp.fpacks.length
      }
      return subSum
    }, 0), 0
  )
)

const overallProgress = computed(() => {
  const total = totalSubprojects.value
  if (total === 0) return 0
  
  const completed = filteredProjects.value.reduce((sum, p) => 
    sum + p.sous_projets.filter(sp => sp.complet).length, 0
  )
  
  return (completed / total) * 100
})

const handleScroll = (event) => {
  scrollTop.value = event.target.scrollTop
}

const handleToggleExpand = (uniqueId) => {
  if (expandedItems.value.has(uniqueId)) {
    expandedItems.value.delete(uniqueId)
  } else {
    expandedItems.value.add(uniqueId)
  }
}

const toggleExpandAll = () => {
  if (allExpanded.value) {
    expandedItems.value.clear()
  } else {
    treeItems.value.forEach(item => {
      if (item.type === 'project' || 
          (item.type === 'subproject' && 
           item.data.fpacks && item.data.fpacks.length > 0)) {
        expandedItems.value.add(item.uniqueId)
      }
    })
  }
  allExpanded.value = !allExpanded.value
}

const resetFilters = () => {
  searchQuery.value = ''
  selectedClient.value = ''
  statusFilter.value = ''
}

const updateContainerHeight = () => {
  if (scrollContainer.value) {
    containerHeight.value = scrollContainer.value.clientHeight
  }
}

const handleCompleteFpack = (sousProjetId, fpack_template_Id) => {
  emit('complete-fpack', sousProjetId, fpack_template_Id)
}

const handleRemoveFpack = (fpackAssociationId) => {
  emit('remove-fpack', fpackAssociationId)
}

watch(searchQuery, () => {
  scrollTop.value = 0
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = 0
  }
})

onMounted(() => {
  updateContainerHeight()
  window.addEventListener('resize', updateContainerHeight)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateContainerHeight)
})
</script>

<template>
  <div class="projects-tree-view">
    <div class="toolbar">
      <div class="search-section">
        <div class="search-input-wrapper">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.35-4.35"/>
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Rechercher projets, sous-projets, FPacks..."
            class="search-input"
          />
          <button v-if="searchQuery" @click="searchQuery = ''" class="clear-search">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </div>

      <div class="filters-section">
        <select v-model="selectedClient" class="filter-select">
          <option value="">Tous les clients</option>
          <option v-for="client in clients" :key="client.id" :value="client.nom">
            {{ client.nom }}
          </option>
        </select>

        <select v-model="statusFilter" class="filter-select">
          <option value="">Tous les états</option>
          <option value="complete">Terminés</option>
          <option value="in-progress">En cours</option>
          <option value="pending">En attente</option>
        </select>

        <button @click="resetFilters" class="reset-filters-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <polyline points="1 4 1 10 7 10"/>
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
          </svg>
          Reset
        </button>
      </div>

      <div class="view-controls">
        <button 
          @click="toggleExpandAll"
          class="control-btn"
          :title="allExpanded ? 'Réduire tout' : 'Étendre tout'"
        >
          <span v-if="allExpanded"> ⏫</span>
          <span v-else >⏬</span>
        </button>

        <div class="density-control">
          <button 
            v-for="density in ['compact', 'normal']"
            :key="density"
            @click="viewDensity = density"
            :class="['density-btn', { active: viewDensity === density }]"
            :title="density.charAt(0).toUpperCase() + density.slice(1)"
          >
            {{ density === 'compact' ? 'C' : 'N' }}
          </button>
        </div>
      </div>
    </div>

    <div class="quick-stats">
      <div class="stat-item">
        <span class="stat-value">{{ filteredProjects.length }}</span>
        <span class="stat-label">Projets</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ totalSubprojects }}</span>
        <span class="stat-label">Sous-projets</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ totalFpacks }}</span>
        <span class="stat-label">FPacks</span>
      </div>
      <div class="stat-item progress">
        <span class="stat-value">{{ Math.round(overallProgress) }}%</span>
        <span class="stat-label">Progression</span>
        <div class="mini-progress">
          <div class="mini-progress-fill" :style="`width: ${overallProgress}%`"></div>
        </div>
      </div>
    </div>

    <div 
      ref="scrollContainer" 
      class="scroll-container"
      :class="`density-${viewDensity}`"
      @scroll="handleScroll"
    >
      <div 
        class="virtual-list" 
        :style="`height: ${virtualHeight}px`"
      >
        <div 
          class="visible-items"
          :style="`transform: translateY(${offsetY}px)`"
        >
          <TreeItem
            v-for="item in visibleItems"
            :key="item.uniqueId"
            :item="item"
            :density="viewDensity"
            @toggle-expand="handleToggleExpand"
            @edit="$emit('edit-project', $event)"
            @delete="$emit('delete-project', $event)"
            @create-subproject="$emit('create-subproject', $event)"
            @edit-subproject="$emit('edit-subproject', $event)"
            @delete-subproject="$emit('delete-subproject', $event)"
            @associate-fpack="$emit('associate-fpack', $event)"
            @remove-fpack="handleRemoveFpack"
            @complete-fpack="handleCompleteFpack"
          />
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner">
        <svg class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <line x1="12" y1="2" x2="12" y2="6"/>
          <line x1="12" y1="18" x2="12" y2="22"/>
          <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>
          <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
          <line x1="2" y1="12" x2="6" y2="12"/>
          <line x1="18" y1="12" x2="22" y2="12"/>
          <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/>
          <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>
        </svg>
      </div>
    </div>
  </div>
</template>

<style scoped>
.projects-tree-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 10px 13px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-bottom: 1px solid #e2e8f0;
  flex-wrap: wrap;
}

.search-section {
  flex: 1;
  min-width: 300px;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  width: 18px;
  height: 18px;
  color: #64748b;
  pointer-events: none;
  z-index: 2;
}

.search-input {
  width: 100%;
  color: #000;
  padding: 12px 40px 12px 44px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 14px;
  background: white;
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.clear-search {
  position: absolute;
  right: 8px;
  width: 28px;
  height: 28px;
  border: none;
  background: #f1f5f9;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  transition: all 0.2s ease;
}

.clear-search:hover {
  background: #e2e8f0;
  color: #374151;
}

.clear-search svg {
  width: 14px;
  height: 14px;
}

.filters-section {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  font-size: 14px;
  color: #374151;
  cursor: pointer;
  transition: border-color 0.2s ease;
}

.filter-select:focus {
  outline: none;
  border-color: #66b7ea;
}

.reset-filters-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  color: #64748b;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.reset-filters-btn:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.reset-filters-btn svg {
  width: 14px;
  height: 14px;
}

.view-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.control-btn {
  width: 36px;
  height: 36px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  transition: all 0.2s ease;
}

.control-btn:hover {
  background: #66a8ea;
  color: white;
  border-color: #6689ea;
}

.control-btn svg {
  width: 16px;
  height: 16px;
}

.density-control {
  display: flex;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  overflow: hidden;
  background: white;
}

.density-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: white;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  transition: all 0.2s ease;
}

.density-btn:hover {
  background: #f9fafb;
}

.density-btn.active {
  background: #66a8ea;
  color: white;
}

.quick-stats {
  display: flex;
  gap: 12px;
  padding: 8px 12px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 80px;
}

.stat-item.progress {
  position: relative;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 0.7rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.mini-progress {
  width: 60px;
  height: 4px;
  background: #e2e8f0;
  border-radius: 2px;
  overflow: hidden;
}

.mini-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #7c66ea, #d72fe0);
  transition: width 0.3s ease;
}

.scroll-container {
  flex: 1;
  overflow-y: auto;
  position: relative;
}

.scroll-container::-webkit-scrollbar {
  width: 6px;
}

.scroll-container::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.scroll-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.scroll-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.virtual-list {
  position: relative;
  width: 100%;
}

.visible-items {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
}

.density-compact {
  font-size: 14px;
}

.density-normal {
  font-size: 15px;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  color: #66a8ea;
}

.loading-spinner svg {
  width: 100%;
  height: 100%;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

</style>