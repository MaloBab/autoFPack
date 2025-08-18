<script setup lang="ts">
import { defineProps, defineEmits, computed, ref, watch, nextTick, onMounted } from 'vue'

interface ProjetItem {
  id: number
  nom: string
  fpack_nom: string
  complet: boolean
  nb_selections: number
  nb_groupes_attendus: number
  progression_percent?: number
}

interface SousProjet {
  id: number
  nom: string
  fpacks: ProjetItem[]
}

interface ProjetGlobalData {
  id: number
  projet: string
  sous_projet?: string
  client: number
  client_nom: string
  projets: ProjetItem[]
  stats?: {
    nb_projets: number
    nb_projets_complets: number
    nb_projets_en_cours: number
    progression_globale: number
    total_groupes: number
    total_selections: number
  }
}

const props = defineProps<{
  projetGlobal: ProjetGlobalData
  forceExpanded: boolean
}>()

const emit = defineEmits<{
  (e: 'add-projet', globalId: number, sousProjetId?: number): void
  (e: 'add-sous-projet', globalId: number): void
  (e: 'edit-global', globalId: number): void
  (e: 'edit-sous-projet', sousProjetId: number): void
  (e: 'delete-global', globalId: number, nom: string): void
  (e: 'delete-sous-projet', sousProjetId: number, nom: string): void
  (e: 'delete-projet', projetId: number, nom: string): void
  (e: 'complete-projet', projetId: number): void
  (e: 'view-facture', projetId: number): void
  (e: 'view-details', projetId: number): void
}>()

const showActions = ref(false)
const showProjetActions = ref<Record<number, boolean>>({})
const isExpanded = ref(props.forceExpanded)
const selectedSousProjet = ref<SousProjet | null>(null)

const stats = ref({
  nb_projets: 0,
  nb_projets_complets: 0,
  nb_projets_en_cours: 0,
  progression_globale: 0,
  total_groupes: 0,
  total_selections: 0
})

const sousProjets = computed((): SousProjet[] => {
  if (!props.projetGlobal?.projets || !Array.isArray(props.projetGlobal.projets)) {
    return []
  }

  // Grouper les projets par sous-projet (ici on utilise le fpack_nom comme proxy)
  const grouped: Record<string, ProjetItem[]> = {}
  
  props.projetGlobal.projets.forEach(projet => {
    if (!projet) return
    
    const key = projet.fpack_nom || 'Groupe par défaut'
    if (!grouped[key]) {
      grouped[key] = []
    }
    grouped[key].push(projet)
  })

  return Object.entries(grouped).map(([nom, fpacks], index) => ({
    id: index + 1,
    nom,
    fpacks: fpacks || []
  }))
})

// Gestion des actions contextuelles
function handleHeaderClick() {
  if (!selectedSousProjet.value) {
    isExpanded.value = !isExpanded.value
  }
}

function handleAddClick() {
  if (!props.projetGlobal?.id) return

  if (selectedSousProjet.value) {
    // Mode FPack : ajouter un FPack au sous-projet
    emit('add-projet', props.projetGlobal.id, selectedSousProjet.value.id)
  } else {
    // Mode sous-projets : ajouter un sous-projet
    emit('add-sous-projet', props.projetGlobal.id)
  }
}

function selectSousProjet(sousProjet: SousProjet) {
  selectedSousProjet.value = sousProjet
}

function exitSousProjetMode() {
  selectedSousProjet.value = null
}

function handleEditSousProjet(sousProjet?: SousProjet) {
  const target = sousProjet || selectedSousProjet.value
  if (target?.id) {
    emit('edit-sous-projet', target.id)
  }
}

function handleDeleteSousProjet(sousProjet: SousProjet) {
  if (sousProjet?.id && sousProjet.nom) {
    emit('delete-sous-projet', sousProjet.id, sousProjet.nom)
  }
}

// Fonctions utilitaires pour les sous-projets avec protection null
function getSousProjetProgress(sousProjet: SousProjet): number {
  if (!sousProjet?.fpacks || !Array.isArray(sousProjet.fpacks)) return 0

  const totalSelections = sousProjet.fpacks.reduce((sum, f) => {
    return sum + (Number(f?.nb_selections) || 0)
  }, 0)
  
  const totalAttendus = sousProjet.fpacks.reduce((sum, f) => {
    return sum + (Number(f?.nb_groupes_attendus) || 0)
  }, 0)
  
  if (totalAttendus === 0) return 0
  return Math.min(100, Math.max(0, Math.round((totalSelections / totalAttendus) * 100)))
}

function getSousProjetStatusIcon(sousProjet: SousProjet): string {
  if (!sousProjet?.fpacks || !Array.isArray(sousProjet.fpacks)) return '📂'

  const complets = sousProjet.fpacks.filter(f => Boolean(f?.complet)).length
  if (complets === sousProjet.fpacks.length && sousProjet.fpacks.length > 0) return '✅'
  if (complets > 0) return '⚡'
  return '📂'
}

function getSousProjetStatusColor(sousProjet: SousProjet): string {
  if (!sousProjet?.fpacks || !Array.isArray(sousProjet.fpacks)) return '#6b7280'

  const complets = sousProjet.fpacks.filter(f => Boolean(f?.complet)).length
  if (complets === sousProjet.fpacks.length && sousProjet.fpacks.length > 0) return '#10b981'
  if (complets > 0) return '#f59e0b'
  return '#6b7280'
}

// Fonctions existantes avec protection null
function updateStats() {
  try {
    const projets = selectedSousProjet.value?.fpacks || props.projetGlobal?.projets || []
    
    if (!Array.isArray(projets)) {
      Object.assign(stats.value, {
        nb_projets: 0,
        nb_projets_complets: 0,
        nb_projets_en_cours: 0,
        progression_globale: 0,
        total_groupes: 0,
        total_selections: 0
      })
      return
    }

    const totalGroupes = projets.reduce((sum, p) => {
      if (!p) return sum
      const groupes = Number(p.nb_groupes_attendus) || 0
      return sum + groupes
    }, 0)
    
    const totalSelections = projets.reduce((sum, p) => {
      if (!p) return sum
      const selections = Number(p.nb_selections) || 0
      return sum + selections
    }, 0)
    
    const complets = projets.filter(p => Boolean(p?.complet))
    const enCours = projets.filter(p => !Boolean(p?.complet) && (Number(p?.nb_selections) || 0) > 0)

    const progression = totalGroupes > 0 ? Math.round((totalSelections / totalGroupes) * 100) : 0

    const newStats = {
      nb_projets: projets.length,
      nb_projets_complets: complets.length,
      nb_projets_en_cours: enCours.length,
      progression_globale: Math.min(100, Math.max(0, progression)),
      total_groupes: totalGroupes,
      total_selections: totalSelections
    }
    
    stats.value = { ...newStats }
  } catch (error) {
    console.error('Error updating stats:', error)
    // Set default values on error
    Object.assign(stats.value, {
      nb_projets: 0,
      nb_projets_complets: 0,
      nb_projets_en_cours: 0,
      progression_globale: 0,
      total_groupes: 0,
      total_selections: 0
    })
  }
}

const progressionColor = computed(() => {
  const progress = stats.value.progression_globale || 0
  if (progress >= 100) return '#10b981' 
  if (progress >= 75) return '#3b82f6'  
  if (progress >= 50) return '#f59e0b'  
  if (progress >= 25) return '#ef4444'  
  return '#6b7280' 
})

function getProjetProgress(projet: ProjetItem): number {
  if (!projet) return 0
  
  const selections = Number(projet.nb_selections) || 0
  const attendus = Number(projet.nb_groupes_attendus) || 0
  
  if (attendus === 0) return 0
  
  const percent = Math.round((selections / attendus) * 100)
  return Math.min(100, Math.max(0, percent))
}

const statusText = computed(() => {
  const { nb_projets_complets, nb_projets } = stats.value
  if (nb_projets_complets === nb_projets && nb_projets > 0) return 'Terminé'
  if (nb_projets_complets > 0) return 'En cours'
  return 'À démarrer'
})

const statusIcon = computed(() => {
  const { nb_projets_complets, nb_projets } = stats.value
  if (nb_projets_complets === nb_projets && nb_projets > 0) return '✅'
  if (nb_projets_complets > 0) return '⚡'
  return '📋'
})

function toggleProjetActions(projetId: number) {
  if (projetId) {
    showProjetActions.value[projetId] = !showProjetActions.value[projetId]
  }
}

function getProjetStatusIcon(projet: ProjetItem) {
  if (!projet) return '📝'
  if (projet.complet) return '✅'
  if ((projet.nb_selections || 0) > 0) return '⚡'
  return '📝'
}

function getProjetStatusColor(projet: ProjetItem) {
  if (!projet) return '#6b7280'
  if (projet.complet) return '#10b981'
  if ((projet.nb_selections || 0) > 0) return '#f59e0b'
  return '#6b7280'
}

function formatProgress(current: number, total: number) {
  const currentSafe = Number(current) || 0
  const totalSafe = Number(total) || 0
  return `${currentSafe}/${totalSafe}`
}

function startTransition(el: Element, done: () => void) {
  const element = el as HTMLElement
  if (!element) {
    done()
    return
  }
  
  const height = element.scrollHeight
  element.style.height = '0'
  element.offsetHeight
  element.style.height = height + 'px'
  
  element.addEventListener('transitionend', () => {
    done()
  }, { once: true })
}

function endTransition(el: Element, done: () => void) {
  const element = el as HTMLElement
  if (!element) {
    done()
    return
  }
  
  const height = element.scrollHeight
  element.style.height = height + 'px'
  element.offsetHeight
  element.style.height = '0'
  
  element.addEventListener('transitionend', () => {
    done()
  }, { once: true })
}

// Watchers avec protection d'erreur
onMounted(() => {
  updateStats()
})

watch(
  () => [
    selectedSousProjet.value,
    props.projetGlobal,
    props.projetGlobal?.projets,
    ...(props.projetGlobal?.projets?.map(p => p?.nb_selections) || []),
    ...(props.projetGlobal?.projets?.map(p => p?.nb_groupes_attendus) || []),
    ...(props.projetGlobal?.projets?.map(p => p?.complet) || [])
  ],
  () => {
    nextTick(() => {
      updateStats()
    })
  },
  { 
    deep: true, 
    immediate: true,
    flush: 'post'
  }
)

watch(
  () => props.forceExpanded,
  (newValue) => {
    isExpanded.value = newValue
  },
  { immediate: true }
)
</script>

<template>
  <div class="projet-global-card" :class="{ expanded: isExpanded }">
    <div class="card-header" @click="handleHeaderClick">
      <div class="header-left">
        <div class="project-title-section">
          <h3 class="project-title">
            {{ projetGlobal?.projet || 'Projet sans nom' }}
            <span v-if="selectedSousProjet" class="sous-projet-indicator">
              → {{ selectedSousProjet.nom }}
            </span>
          </h3>
          <p v-if="projetGlobal?.sous_projet && !selectedSousProjet" class="sub-project">
            {{ sousProjets.length }} sous-projet(s)
          </p>
          <p v-else-if="selectedSousProjet" class="sub-project">
            Mode FPacks - {{ selectedSousProjet.nom }}
          </p>
        </div>
        
        <div class="client-info">
          <span class="client-icon">👤</span>
          <span class="client-name">{{ projetGlobal?.client_nom || 'Client inconnu' }}</span>
        </div>
      </div>

      <div class="header-center">
        <div class="status-badge" :style="{ backgroundColor: progressionColor }">
          <span class="status-icon">{{ statusIcon }}</span>
          <span class="status-text">{{ statusText }}</span>
        </div>
        
        <div class="progress-circle-container">
          <svg class="progress-circle" width="60" height="60" viewBox="0 0 60 60">
            <circle
              cx="30"
              cy="30"
              r="25"
              fill="none"
              stroke="#e5e7eb"
              stroke-width="4"
            />
            <circle
              cx="30"
              cy="30"
              r="25"
              fill="none"
              :stroke="progressionColor"
              stroke-width="4"
              stroke-linecap="round"
              :stroke-dasharray="157"
              :stroke-dashoffset="157 - (157 * stats.progression_globale) / 100"
              transform="rotate(-90 30 30)"
              class="progress-bar-circle"
            />
          </svg>
          <div class="progress-text">{{ stats.progression_globale }}%</div>
        </div>
      </div>

      <div class="header-right">
        <div class="quick-stats">
          <div class="stat-item">
            <span class="stat-number">{{ selectedSousProjet ? (selectedSousProjet.fpacks?.length || 0) : sousProjets.length }}</span>
            <span class="stat-label">{{ selectedSousProjet ? 'FPacks' : 'Sous-projets' }}</span>
          </div>
          <div class="stat-item success">
            <span class="stat-number">{{ stats.nb_projets_complets }}</span>
            <span class="stat-label">Complets</span>
          </div>
        </div>
        
        <div class="header-actions">
          <button 
            v-if="selectedSousProjet"
            @click.stop="exitSousProjetMode" 
            class="action-btn back-btn"
            title="Retour aux sous-projets"
          >
            <span class="btn-icon">←</span>
          </button>
          
          <button 
            @click.stop="handleAddClick" 
            class="action-btn add-btn"
            :title="selectedSousProjet ? 'Ajouter un FPack' : 'Ajouter un sous-projet'"
          >
            <span class="btn-icon">➕</span>
          </button>
          
          <div class="dropdown" @click.stop>
            <button 
              @click="showActions = !showActions"
              class="action-btn dropdown-btn"
              title="Plus d'options"
            >
              <span class="btn-icon">⋮</span>
            </button>
            
            <Transition name="dropdown">
              <div v-if="showActions" class="dropdown-menu" @click.stop>
                <button 
                  @click="emit('edit-global', projetGlobal?.id || 0); showActions = false"
                  class="dropdown-item"
                >
                  <span class="item-icon">✏️</span>
                  Éditer le projet
                </button>
                <button 
                  v-if="selectedSousProjet"
                  @click="handleEditSousProjet(); showActions = false"
                  class="dropdown-item"
                >
                  <span class="item-icon">✏️</span>
                  Éditer le sous-projet
                </button>
                <button 
                  @click="emit('delete-global', projetGlobal?.id || 0, projetGlobal?.projet || ''); showActions = false"
                  class="dropdown-item danger"
                >
                  <span class="item-icon">🗑️</span>
                  Supprimer
                </button>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </div>

    <Transition name="expand" @enter="startTransition" @leave="endTransition">
      <div v-if="isExpanded" class="card-content-wrapper" ref="contentWrapper">
        <div class="card-content">
          <div v-if="!selectedSousProjet" class="sous-projets-mode">
            <div v-if="sousProjets.length === 0" class="empty-sous-projets">
              <div class="empty-icon">📁</div>
              <p class="empty-text">Aucun sous-projet créé</p>
              <button 
                @click="handleAddClick"
                class="create-first-btn"
              >
                ➕ Créer le premier sous-projet
              </button>
            </div>
            
            <div v-else class="sous-projets-grid">
              <TransitionGroup name="sous-projet-list" tag="div" class="sous-projets-container">
                <div 
                  v-for="sousProjet in sousProjets" 
                  :key="sousProjet.id"
                  class="sous-projet-card"
                  @click="selectSousProjet(sousProjet)"
                >
                  <div class="sous-projet-header">
                    <div class="sous-projet-icon">📂</div>
                    <div class="sous-projet-info">
                      <h4 class="sous-projet-name">{{ sousProjet.nom }}</h4>
                      <p class="fpacks-count">{{ sousProjet.fpacks?.length || 0 }} FPack(s)</p>
                    </div>
                    <div class="sous-projet-status">
                      <span class="status-indicator" :style="{ color: getSousProjetStatusColor(sousProjet) }">
                        {{ getSousProjetStatusIcon(sousProjet) }}
                      </span>
                    </div>
                  </div>
                  
                  <div class="sous-projet-progress">
                    <div class="mini-progress-bar">
                      <div 
                        class="mini-progress-fill"
                        :style="{ 
                          width: `${getSousProjetProgress(sousProjet)}%`,
                          backgroundColor: getSousProjetStatusColor(sousProjet)
                        }"
                      ></div>
                    </div>
                    <span class="mini-progress-text">{{ getSousProjetProgress(sousProjet) }}%</span>
                  </div>

                  <div class="sous-projet-actions" @click.stop>
                    <button 
                      @click="handleEditSousProjet(sousProjet)"
                      class="mini-action-btn"
                      title="Éditer"
                    >
                      ✏️
                    </button>
                    <button 
                      @click="handleDeleteSousProjet(sousProjet)"
                      class="mini-action-btn danger"
                      title="Supprimer"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </TransitionGroup>
            </div>
          </div>
          
          <div v-else class="fpacks-mode">
            <div v-if="!selectedSousProjet.fpacks || selectedSousProjet.fpacks.length === 0" class="empty-projects">
              <div class="empty-icon">📋</div>
              <p class="empty-text">Aucun F-Pack créé pour ce sous-projet</p>
              <button 
                @click="handleAddClick"
                class="create-first-project-btn"
              >
                ➕ Créer le premier F-Pack
              </button>
            </div>
            
            <div v-else class="projects-grid">
              <TransitionGroup name="project-list" tag="div" class="projects-container">
                <div 
                  v-for="projet in selectedSousProjet.fpacks" 
                  :key="projet.id" 
                  class="projet-card"
                  :class="{ 
                    complete: projet.complet,
                    'in-progress': (projet.nb_selections || 0) > 0 && !projet.complet,
                    'not-started': (projet.nb_selections || 0) === 0
                  }"
                >
                  <div class="projet-header">
                    <div class="projet-status">
                      <span 
                        class="status-indicator"
                        :style="{ color: getProjetStatusColor(projet) }"
                      >
                        {{ getProjetStatusIcon(projet) }}
                      </span>
                    </div>
                    
                    <div class="projet-info">
                      <h4 class="projet-name">{{ projet.nom || 'Projet sans nom' }}</h4>
                      <p class="fpack-info">📦 {{ projet.fpack_nom || 'FPack inconnu' }}</p>
                    </div>

                    <div class="projet-actions-container">
                      <button 
                        @click="toggleProjetActions(projet.id)"
                        class="projet-menu-btn"
                        :class="{ active: showProjetActions[projet.id] }"
                      >
                        ⋮
                      </button>
                      
                      <Transition name="fade-slide">
                        <div 
                          v-if="showProjetActions[projet.id]" 
                          class="projet-actions-menu"
                        >
                          <button 
                            @click="emit('view-details', projet.id)"
                            class="action-menu-item"
                          >
                            <span class="action-icon">👁️</span>
                            Détails
                          </button>
                          
                          <button 
                            @click="emit('view-facture', projet.id)"
                            class="action-menu-item"
                            :disabled="!projet.complet"
                            :class="{ disabled: !projet.complet }"
                          >
                            <span class="action-icon">💰</span>
                            Facture
                          </button>
                          
                          <div class="menu-separator"></div>
                          
                          <button 
                            @click="emit('delete-projet', projet.id, projet.nom || 'Projet sans nom')"
                            class="action-menu-item danger"
                          >
                            <span class="action-icon">🗑️</span>
                            Supprimer
                          </button>
                        </div>
                      </Transition>
                    </div>
                  </div>

                  <div class="projet-progress">
                    <div class="progress-info">
                      <span class="progress-label">Progression</span>
                      <span class="progress-numbers">
                        {{ formatProgress(projet.nb_selections || 0, projet.nb_groupes_attendus || 0) }}
                      </span>
                    </div>
                    
                    <div class="progress-bar-container">
                      <div class="progress-bar-bg">
                        <div 
                          class="progress-bar-fill"
                          :style="{ 
                            width: `${projet.progression_percent || getProjetProgress(projet)}%`,
                            backgroundColor: getProjetStatusColor(projet)
                          }"
                        ></div>
                      </div>
                      <span class="progress-percentage">{{ projet.progression_percent || getProjetProgress(projet) }}%</span>
                    </div>
                  </div>

                  <div class="quick-actions">
                    <button 
                      @click="emit('complete-projet', projet.id)"
                      class="quick-action-btn primary"
                      :title="projet.complet ? 'Modifier les sélections' : 'Compléter le projet'"
                    >
                      <span class="quick-btn-icon">{{ projet.complet ? '✏️' : '📝' }}</span>
                      <span class="quick-btn-text">{{ projet.complet ? 'Modifier' : 'Compléter' }}</span>
                    </button>
                    
                    <button 
                      @click="emit('view-facture', projet.id)"
                      class="quick-action-btn secondary"
                      :disabled="!projet.complet"
                      title="Voir la facture"
                    >
                      <span class="quick-btn-icon">💰</span>
                      <span class="quick-btn-text">Facture</span>
                    </button>
                  </div>
                </div>
              </TransitionGroup>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
:root {
   --color-bg-default: #f7f7f7;
}

.projet-global-card {
  display: flex;
  flex-direction: column;
  height: auto;
  background: #ffffff;
  border-radius: 16px;
  transition: all 0.3s ease;
}

.projet-global-card:not(.expanded) {
  background: #f7f7f7;
}

.projet-global-card.expanded {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  border: 1px solid #f3f4f6;
  transform: scale(1);
  opacity: 1;
}

.projet-global-card.expanded:hover {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  transform: translateY(-2px);
}

.card-header {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 1.5rem; 
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 1.5rem;
  align-items: center;
  cursor: pointer;
  border-bottom: 1px solid #e2e8f0;
  transition: background 0.2s ease;
  min-height: 130px;
}

.card-header:hover {
  background: linear-gradient(135deg, #f1f5f9 0%, #d1d5db 100%);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.project-title-section {
  display: flex;
  flex-direction: column;
}

.project-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.2;
}

.sous-projet-indicator {
  color: #6b7280;
  font-weight: 500;
  font-size: 1rem;
}

.sub-project {
  margin: 0;
  font-size: 0.9rem;
  color: #6b7280;
  font-style: italic;
}

.client-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-right: 2rem;
  font-size: 0.9rem;
  color: #374151;
}

.client-icon {
  font-size: 1rem;
}

.client-name {
  font-weight: 500;
}

.header-center {
  display: flex;
  margin-right: 50%;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  padding: 0.5rem 0.8rem;
  border-radius: 20px;
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
}

.progress-circle-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-circle {
  transform: rotate(-90deg);
}

.progress-bar-circle {
  transition: stroke-dashoffset 0.5s ease;
}

.progress-text {
  position: absolute;
  font-size: 0.9rem;
  font-weight: 700;
  color: #1f2937;
}

.quick-stats {
  display: flex;
  margin-bottom: 5%;
  gap: 1rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.stat-item.success {
  color: #10b981;
}

.stat-number {
  font-size: 1.25rem;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 1rem;
  position: relative;
}

.action-btn {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 36px;
}

.action-btn:hover {
  background: #f9fafb;
  border-color: #d1d5db;
  transform: translateY(-1px);
}

.add-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-color: transparent;
  color: white;
}

.add-btn:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

.back-btn {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  border-color: transparent;
  color: white;
}

.back-btn:hover {
  background: linear-gradient(135deg, #4b5563 0%, #374151 100%);
}

.dropdown {
  position: relative;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  z-index: 10;
  min-width: 160px;
  overflow: hidden;
  margin-top: 0.5rem;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.75rem 1rem;
  background: white;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s ease;
  font-size: 0.9rem;
}

.dropdown-item:hover {
  background: #f9fafb;
}

.dropdown-item.danger {
  color: #ef4444;
}

.dropdown-item.danger:hover {
  background: #fef2f2;
}

.card-content-wrapper {
  overflow-y: auto;
  max-height: 520px; 
  transition: height 0.3s ease-in-out;
  height: auto;
}

.card-content {
  transition: all 0.3s ease-in-out;
  padding: 1.5rem;
  height: auto;
}

.sous-projets-mode {
  min-height: 200px;
}

.empty-sous-projets {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-text {
  margin: 0 0 1.5rem 0;
  font-size: 1.1rem;
}

.create-first-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.create-first-btn:hover {
  transform: translateY(-1px);
}

.sous-projets-grid {
  width: 100%;
}

.sous-projets-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  width: 100%;
}

.sous-projet-card {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.25rem;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.sous-projet-card:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
}

.sous-projet-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3b82f6, #10b981);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.sous-projet-card:hover::before {
  opacity: 1;
}

.sous-projet-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.sous-projet-icon {
  font-size: 1.8rem;
  flex-shrink: 0;
}

.sous-projet-info {
  flex: 1;
}

.sous-projet-name {
  margin: 0 0 0.25rem 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
}

.fpacks-count {
  margin: 0;
  font-size: 0.85rem;
  color: #6b7280;
}

.sous-projet-status {
  flex-shrink: 0;
}

.sous-projet-progress {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.mini-progress-bar {
  flex: 1;
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
}

.mini-progress-fill {
  height: 100%;
  transition: width 0.5s ease;
  border-radius: 2px;
}

.mini-progress-text {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  min-width: 35px;
  text-align: right;
}

.sous-projet-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.mini-action-btn {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s ease;
  opacity: 0.7;
}

.mini-action-btn:hover {
  opacity: 1;
  background: #f3f4f6;
  transform: scale(1.1);
}

.mini-action-btn.danger:hover {
  background: #fef2f2;
  color: #ef4444;
}

.fpacks-mode {
  min-height: 200px;
}

.empty-projects {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.create-first-project-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.create-first-project-btn:hover {
  transform: translateY(-1px);
}

.projects-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
  width: 100%;
}

.projet-card {
  background: #fafafa;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.25rem;
  transition: all 0.2s ease;
}

.projet-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.projet-card.complete {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  border-color: #10b981;
}

.projet-card.in-progress {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border-color: #f59e0b;
}

.projet-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}

.projet-status {
  flex-shrink: 0;
}

.status-indicator {
  font-size: 1.5rem;
}

.projet-info {
  flex: 1;
}

.projet-name {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.3;
}

.fpack-info {
  margin: 0;
  font-size: 0.9rem;
  color: #6b7280;
}

.projet-actions-container {
  position: relative;
  flex-shrink: 0;
}

.projet-menu-btn {
  background: none;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s ease;
}

.projet-menu-btn:hover,
.projet-menu-btn.active {
  background: #f3f4f6;
  color: #374151;
}

.projet-actions-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  z-index: 20;
  min-width: 160px;
  overflow: hidden;
  margin-top: 0.5rem;
}

.action-menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.75rem 1rem;
  background: white;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s ease;
  font-size: 0.9rem;
}

.action-menu-item:hover:not(.disabled) {
  background: #f9fafb;
}

.action-menu-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-menu-item.danger {
  color: #ef4444;
}

.action-menu-item.danger:hover {
  background: #fef2f2;
}

.menu-separator {
  height: 1px;
  background: #e5e7eb;
  margin: 0.5rem 0;
}

.projet-progress {
  margin-bottom: 1rem;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.progress-label {
  color: #6b7280;
  font-weight: 500;
}

.progress-numbers {
  color: #374151;
  font-weight: 600;
}

.progress-bar-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.progress-bar-bg {
  flex: 1;
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  transition: width 0.5s ease;
  border-radius: 3px;
}

.progress-percentage {
  font-size: 0.8rem;
  font-weight: 600;
  color: #6b7280;
  min-width: 40px;
  text-align: right;
}

.quick-actions {
  display: flex;
  gap: 0.75rem;
}

.quick-action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-action-btn.primary {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
}

.quick-action-btn.primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
  transform: translateY(-1px);
}

.quick-action-btn.secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #e5e7eb;
}

.quick-action-btn.secondary:hover:not(:disabled) {
  background: #e5e7eb;
  transform: translateY(-1px);
}

.quick-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.quick-btn-icon {
  font-size: 1rem;
}

.quick-btn-text {
  font-size: 0.85rem;
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
  transform-origin: top right;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-5px);
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease-in-out;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  height: 0;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.2s ease;
  transform-origin: top right;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(-10px);
}

.sous-projet-list-enter-active,
.sous-projet-list-leave-active,
.project-list-enter-active,
.project-list-leave-active {
  transition: all 0.3s ease;
}

.sous-projet-list-enter-from,
.sous-projet-list-leave-to,
.project-list-enter-from,
.project-list-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.sous-projet-list-move,
.project-list-move {
  transition: transform 0.3s ease;
}

</style>