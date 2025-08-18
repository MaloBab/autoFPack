<script setup lang="ts">
import { ref, watch, computed, nextTick } from 'vue'
import { onClickOutside } from '@vueuse/core'

const props = defineProps<{
  column: string
  values: any[]
  selected: Set<any>
  labels?: Record<any, string>
  maxDropdownHeight?: number // Nouvelle prop pour personnaliser la hauteur max
}>()

const emit = defineEmits<{
  (e: 'filter-change', column: string, newSet: Set<any>): void,
  (e: 'sort-change', column: string, order: 'asc' | 'desc' | null): void
}>()

const dropdownOpen = ref(false)
const localSelections = ref<Set<any>>(new Set(props.values))
const container = ref<any>(null)
const dropdown = ref<any>(null)
const sortOrder = ref<'asc' | 'desc' | null>(null)
const dropdownPosition = ref({ top: '0px', left: '0px', maxValuesHeight: '200px' })

// CORRIGÉ: Inclure le dropdown téléporté dans la détection du clic extérieur
onClickOutside(container, (event) => {
  // Vérifier si le clic est dans le dropdown téléporté
  if (dropdown.value && dropdown.value.contains(event.target)) {
    return
  }
  dropdownOpen.value = false
}, { ignore: [dropdown] })

watch(() => props.selected, (newSelected) => {
  localSelections.value = new Set([...newSelected])
}, { immediate: true })

// CORRIGÉ: Fonction toggleValue avec event handler
function toggleValue(val: any) {
  const newSet = new Set(localSelections.value)
  if (newSet.has(val)) {
    newSet.delete(val)
  } else {
    newSet.add(val)
  }
  localSelections.value = newSet
  emit('filter-change', props.column, newSet)
}

function checkAll() {
  const newSet = new Set(props.values)
  localSelections.value = newSet
  emit('filter-change', props.column, newSet)
}

function uncheckAll() {
  const newSet = new Set()
  localSelections.value = newSet
  emit('filter-change', props.column, newSet)
}

const isFilterOrSortActive = computed(() => {
  return localSelections.value.size !== props.values.length || sortOrder.value !== null
})

function onSortClick(order: 'asc' | 'desc') {
  if (sortOrder.value === order) {
    sortOrder.value = null
  } else {
    sortOrder.value = order
  }
  emit('sort-change', props.column, sortOrder.value)
}

function calculateDropdownPosition() {
  if (container.value) {
    const rect = container.value.getBoundingClientRect()
    const dropdownWidth = 280 // Légèrement plus large
    
    // Calculer la hauteur des sections fixes avec plus de précision
    const headerHeight = isFilterOrSortActive.value ? 45 : 0
    const actionsHeight = 94 // Actions rapides
    const sortHeight = 94 // Section tri
    const titleHeight = 40 // Titre "Valeurs"
    const padding = 32 // Padding général
    const bottomPadding = 16 // Padding du bas
    
    const fixedHeight = headerHeight + actionsHeight + sortHeight + titleHeight + padding + bottomPadding
    
    // Hauteur max personnalisable avec des limites plus intelligentes
    const customMaxHeight = props.maxDropdownHeight || 400
    const viewportMaxHeight = window.innerHeight * 0.7 // Max 70% de la hauteur viewport
    const maxDropdownHeight = Math.min(customMaxHeight, viewportMaxHeight, 500)
    
    // Calculer la hauteur disponible pour les valeurs
    const availableHeight = maxDropdownHeight - fixedHeight
    const minValuesHeight = 150 // Hauteur minimum pour voir au moins quelques éléments
    const maxValuesHeight = Math.max(minValuesHeight, availableHeight)
    
    // Estimer la hauteur finale du dropdown
    const estimatedValuesHeight = Math.min(maxValuesHeight, props.values.length * 42)
    const finalDropdownHeight = fixedHeight + estimatedValuesHeight
    
    // Position horizontale - éviter de dépasser à droite avec marge de sécurité
    let left = rect.right + window.scrollX - dropdownWidth
    if (left < 20) { // Marge de 20px du bord gauche
      left = Math.max(20, rect.left + window.scrollX)
    }
    if (left + dropdownWidth > window.innerWidth - 20) {
      left = window.innerWidth - dropdownWidth - 20
    }
    
    // Position verticale - CENTRER sur le bouton de filtre
    const buttonCenterY = rect.top + window.scrollY + rect.height / 2
    let top = buttonCenterY - finalDropdownHeight / 2
    
    // Vérifier les débordements et ajuster si nécessaire
    const viewportTop = window.scrollY + 20
    const viewportBottom = window.scrollY + window.innerHeight - 20
    
    // Si le dropdown dépasse en haut
    if (top < viewportTop) {
      top = viewportTop
    }
    
    // Si le dropdown dépasse en bas
    if (top + finalDropdownHeight > viewportBottom) {
      top = viewportBottom - finalDropdownHeight
      
      // Si même comme ça ça ne rentre pas, le repositionner au centre du viewport
      if (top < viewportTop) {
        top = viewportTop + (window.innerHeight - finalDropdownHeight) / 2
      }
    }
    
    dropdownPosition.value = {
      top: top + 'px',
      left: left + 'px',
      maxValuesHeight: maxValuesHeight + 'px'
    }
  }
}

async function toggleDropdown() {
  if (!dropdownOpen.value) {
    calculateDropdownPosition()
    dropdownOpen.value = true
    await nextTick()
    
    // Auto-scroll vers le premier élément sélectionné si il y en a
    if (dropdown.value) {
      const firstChecked = dropdown.value.querySelector('input[type="checkbox"]:checked')
      if (firstChecked) {
        const label = firstChecked.closest('.checkbox-label')
        if (label) {
          label.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      }
    }
  } else {
    dropdownOpen.value = false
  }
}

// Fonction pour recalculer la position lors du redimensionnement
function handleResize() {
  if (dropdownOpen.value) {
    calculateDropdownPosition()
  }
}

// Écouter les changements de taille de fenêtre
if (typeof window !== 'undefined') {
  window.addEventListener('resize', handleResize)
  window.addEventListener('scroll', handleResize)
}
</script>

<template>
  <div class="searcher" ref="container">
    <button class="filter-icon" :class="{ 'active-filter': isFilterOrSortActive }" @click="toggleDropdown" type="button">
      <img src="../../assets/filtre.png" alt="filtrer" class="filter-img" />
    </button>
    
    <Teleport to="body">
      <div 
        v-if="dropdownOpen" 
        ref="dropdown"
        class="dropdown dropdown-teleported"
        :style="{
          position: 'fixed',
          top: dropdownPosition.top,
          left: dropdownPosition.left,
          zIndex: 9999
        }"
        @click.stop
      >
        <!-- Indicateur de filtre actif -->
        <div v-if="isFilterOrSortActive" class="filter-status">
          <span class="active-count">{{ localSelections.size }}/{{ props.values.length }} sélectionnés</span>
        </div>
        
        <!-- Actions de filtre -->
        <div class="dropdown-section">
          <div class="section-title">Actions rapides</div>
          <div class="dropdown-actions">
            <button @click="checkAll" class="action-btn select-all">
              <span class="btn-icon">✓</span>
              Tout sélectionner
            </button>
            <button @click="uncheckAll" class="action-btn deselect-all">
              <span class="btn-icon">✗</span>
              Tout désélectionner
            </button>
          </div>
        </div>
        
        <!-- Actions de tri -->
        <div class="dropdown-section">
          <div class="section-title">Trier</div>
          <div class="dropdown-actions sort-actions">
            <button
              :class="{ active: sortOrder === 'asc' }"
              @click="onSortClick('asc')"
              class="sort-btn"
            >
              <span class="sort-icon">↑</span>
              A-Z
            </button>
            <button
              :class="{ active: sortOrder === 'desc' }"
              @click="onSortClick('desc')"
              class="sort-btn"
            >
              <span class="sort-icon">↓</span>
              Z-A
            </button>
          </div>
        </div>
        
        <!-- Valeurs avec scrollbar optimisée -->
        <div class="dropdown-section values-section">
          <div class="section-title">
            <span>Valeurs ({{ props.values.length }})</span>
          </div>
          <div 
            class="dropdown-values"
            :style="{ maxHeight: dropdownPosition.maxValuesHeight }"
          >
            <label v-for="(val, index) in props.values" :key="val" class="checkbox-label" :style="{ animationDelay: Math.min(index * 0.02, 0.3) + 's' }">
              <div class="custom-checkbox">
                <input
                  type="checkbox"
                  :checked="localSelections.has(val)"
                  @change="toggleValue(val)"
                />
                <span class="checkmark"></span>
              </div>
              <span class="checkbox-text" :title="props.labels?.[val] ?? val">{{ props.labels?.[val] ?? val }}</span>
            </label>
            
            <!-- Indicateur de fin de liste -->
            <div v-if="props.values.length > 0" class="end-indicator">
              <span class="end-text">{{ props.values.length }} élément{{ props.values.length > 1 ? 's' : '' }} au total</span>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.searcher {
  position: relative;
  display: inline-block;
}

.filter-icon {
  background: none;
  border: none;
  cursor: pointer;
  margin-top: 20%;
  padding: 3%;
  border-radius: 3%;
  transition: all 0.3s ease;
}

.filter-img {
  width: 1.6vw;
  height: 1.6vw;
  background-color: transparent;
  transition: all 0.3s ease;
}

.filter-icon:hover .filter-img {
  filter: invert(34%) sepia(87%) saturate(1535%) hue-rotate(203deg) brightness(95%) contrast(90%);
  transform: scale(1.1);
}

.filter-icon.active-filter .filter-img {
  filter: invert(35%) sepia(86%) saturate(2920%) hue-rotate(199deg) brightness(92%) contrast(89%);
}

.filter-icon:focus {
  outline: none;
}

/* Dropdown principal - optimisé */
.dropdown {
  background: white;
  border: 1px solid #e1e5e9;
  border-radius: 16px;
  box-shadow: 
    0 20px 50px rgba(0, 0, 0, 0.15), 
    0 8px 25px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset;
  padding: 0;
  width: 280px;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  animation: slideDown 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.98);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-12px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.dropdown-teleported {
  position: fixed !important;
  z-index: 9999 !important;
}

/* En-tête - Indicateur de filtre */
.filter-status {
  padding: 14px 18px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-align: center;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

/* Sections */
.dropdown-section {
  padding: 18px;
  border-bottom: 1px solid #f0f2f5;
}

.dropdown-section:last-child {
  border-bottom: none;
  padding-bottom: 12px;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  color: #6b7280;
  margin-bottom: 14px;
  letter-spacing: 0.6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}


/* Actions */
.dropdown-actions {
  display: flex;
  gap: 10px;
}

.action-btn, .sort-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px 14px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  color: #475569;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.action-btn:hover, .sort-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.action-btn:active, .sort-btn:active {
  transform: translateY(0);
}

.btn-icon, .sort-icon {
  font-size: 14px;
  font-weight: bold;
}

.select-all .btn-icon {
  color: #10b981;
}

.deselect-all .btn-icon {
  color: #ef4444;
}

.sort-btn.active {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: white;
  border-color: #1d4ed8;
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
}

.sort-btn.active .sort-icon {
  color: white;
}

.values-section {
  padding-bottom: 12px;
}

.dropdown-values {
  display: flex;
  flex-direction: column;
  gap: 1px;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 6px;
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
}

.dropdown-values::-webkit-scrollbar {
  width: 10px;
}

.dropdown-values::-webkit-scrollbar-track {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  margin: 6px 0;
  border: 1px solid rgba(226, 232, 240, 0.5);
}

.dropdown-values::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #cbd5e1 0%, #94a3b8 50%, #64748b 100%);
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
  background-clip: padding-box;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.dropdown-values::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 50%, #475569 100%);
  transform: scale(1.1);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.dropdown-values::-webkit-scrollbar-thumb:active {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  transform: scale(1.05);
}

/* Support amélioré pour Firefox */
.dropdown-values {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 #f8fafc;
}

/* Checkbox personnalisé amélioré */
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 14px;
  cursor: pointer;
  user-select: none;
  border-radius: 8px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  margin-right: 6px;
  border: 1px solid transparent;
}

.checkbox-label:hover {
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  transform: translateX(3px);
  border-color: rgba(59, 130, 246, 0.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.custom-checkbox {
  position: relative;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.custom-checkbox input[type="checkbox"] {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  width: 20px;
  height: 20px;
  margin: 0;
}

.checkmark {
  position: relative;
  width: 20px;
  height: 20px;
  border: 2px solid #d1d5db;
  border-radius: 6px;
  background: white;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.custom-checkbox input[type="checkbox"]:checked + .checkmark {
  background: linear-gradient(135deg, #109db9 0%, #055c96 100%);
  border-color: #1081b9;
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.custom-checkbox input[type="checkbox"]:checked + .checkmark::after {
  content: '✓';
  color: white;
  font-size: 13px;
  font-weight: bold;
  animation: checkScale 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes checkScale {
  0% {
    transform: scale(0) rotate(-45deg);
  }
  50% {
    transform: scale(1.3) rotate(0deg);
  }
  100% {
    transform: scale(1) rotate(0deg);
  }
}

.checkbox-text {
  font-size: 14px;
  color: #374151;
  font-weight: 400;
  flex: 1;
  word-break: break-word;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}


/* Indicateur de fin de liste */
.end-indicator {
  padding: 16px 14px 8px;
  text-align: center;
  border-top: 1px solid #f0f2f5;
  margin-top: 8px;
}

.end-text {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 500;
  opacity: 0.8;
}

.action-btn:focus, .sort-btn:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
}

.custom-checkbox input[type="checkbox"]:focus + .checkmark {
  box-shadow: 0 0 0 3px rgba(16, 103, 185, 0.3);
}

/* Animation d'entrée optimisée pour les éléments de la liste */
.checkbox-label {
  animation: fadeInUp 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  opacity: 0;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(15px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

</style>