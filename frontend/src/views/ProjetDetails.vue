<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjets } from '../composables/useProjets'
import { showToast } from '../composables/useToast'

const route = useRoute()
const router = useRouter()

const {
  getProjetDetails,
  loading
} = useProjets()

// État local
const projetDetails = ref<any>(null)
const activeTab = ref('overview')
const animatedStats = ref({
  selections: 0,
  progression: 0
})

// Computed
const projetId = computed(() => parseInt(route.params.id as string))

const progressColor = computed(() => {
  if (!projetDetails.value) return '#6b7280'
  const progress = projetDetails.value.progression_percent
  if (progress >= 100) return '#10b981'
  if (progress >= 75) return '#3b82f6'
  if (progress >= 50) return '#f59e0b'
  return '#ef4444'
})

const statusConfig = computed(() => {
  if (!projetDetails.value) return { icon: '📋', text: 'Chargement...', class: 'loading' }
  
  if (projetDetails.value.complet) {
    return { icon: '✅', text: 'Terminé', class: 'complete' }
  }
  
  if (projetDetails.value.selections.length > 0) {
    return { icon: '⚡', text: 'En Cours', class: 'in-progress' }
  }
  
  return { icon: '📋', text: 'À Démarrer', class: 'not-started' }
})

const selectionsByType = computed(() => {
  if (!projetDetails.value?.selections) return {}
  
  return projetDetails.value.selections.reduce((acc: any, sel: any) => {
    if (!acc[sel.type_item]) acc[sel.type_item] = []
    acc[sel.type_item].push(sel)
    return acc
  }, {})
})

const typeIcons = computed(() => ({
  produit: '📦',
  equipement: '⚙️',
  robot: '🤖'
}))

// Méthodes
async function fetchDetails() {
  try {
    const details = await getProjetDetails(projetId.value)
    projetDetails.value = details
    
    // Animation des statistiques
    animateStats()
  } catch (error: any) {
    console.error('Erreur lors du chargement des détails:', error)
    const message = error.response?.data?.detail || 'Erreur lors du chargement des détails'
    showToast(message, '#e71717ff')
    router.push('/projet_global')
  }
}

function animateStats() {
  if (!projetDetails.value) return
  
  const targetSelections = projetDetails.value.selections.length
  const targetProgression = projetDetails.value.progression_percent
  
  const duration = 1000
  const steps = 30
  const stepTime = duration / steps
  
  let currentStep = 0
  
  const animate = () => {
    currentStep++
    const progress = currentStep / steps
    const easeOut = 1 - Math.pow(1 - progress, 3)
    
    animatedStats.value.selections = Math.round(targetSelections * easeOut)
    animatedStats.value.progression = Math.round(targetProgression * easeOut)
    
    if (currentStep < steps) {
      setTimeout(animate, stepTime)
    }
  }
  
  animate()
}

function navigateToComplete() {
  router.push(`/complete/projets/${projetId.value}`)
}

function navigateToFacture() {
  if (!projetDetails.value?.complet) {
    showToast('Le projet doit être complété pour générer une facture', '#f59e0b')
    return
  }
  router.push(`/facture/${projetId.value}`)
}

function goBack() {
  router.push('/projet_global')
}

function getTypeDisplayName(type: string) {
  const names: Record<string, string> = {
    produit: 'Produits',
    equipement: 'Équipements',
    robot: 'Robots'
  }
  return names[type] || type
}


// Watchers
watch(() => route.params.id, () => {
  if (route.params.id) {
    fetchDetails()
  }
})

onMounted(fetchDetails)
</script>

<template>
  <div class="projet-details">
    <div class="header-section">
      <div class="breadcrumb">
        <button @click="goBack" class="breadcrumb-item clickable">
          <span class="breadcrumb-icon">🏠</span>
          Projets
        </button>
        <span class="breadcrumb-separator">›</span>
        <span class="breadcrumb-item current">
          {{ projetDetails?.projet.nom || 'Chargement...' }}
        </span>
      </div>
      
      <div v-if="projetDetails" class="header-content">
        <div class="title-section">
          <h1 class="project-title">{{ projetDetails.projet.nom }}</h1>
          <div class="project-meta">
            <span class="meta-item">
              <span class="meta-icon">🏢</span>
              {{ projetDetails.client?.nom }}
            </span>
            <span class="meta-item">
              <span class="meta-icon">📦</span>
              {{ projetDetails.fpack?.nom }}
            </span>
            <div class="status-badge" :class="statusConfig.class">
              <span class="status-icon">{{ statusConfig.icon }}</span>
              {{ statusConfig.text }}
            </div>
          </div>
        </div>
        
        <div class="header-actions">
          <button 
            @click="navigateToComplete"
            class="action-btn primary"
            :class="{ 'complete': projetDetails.complet }"
          >
            <span class="btn-icon">{{ projetDetails.complet ? '✏️' : '📝' }}</span>
            {{ projetDetails.complet ? 'Modifier' : 'Compléter' }}
          </button>
          
          <button 
            @click="navigateToFacture"
            class="action-btn secondary"
            :disabled="!projetDetails.complet"
          >
            <span class="btn-icon">💰</span>
            Facture
          </button>
        </div>
      </div>
    </div>

    <!-- Statistiques compactes -->
    <div v-if="projetDetails" class="stats-section">
      <div class="stat-card">
        <div class="stat-icon">🎯</div>
        <div class="stat-content">
          <div class="stat-number">{{ animatedStats.selections }}</div>
          <div class="stat-label">Sélections</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-number">{{ animatedStats.progression }}%</div>
          <div class="stat-label">Progression</div>
        </div>
        <div class="progress-bar-mini">
          <div 
            class="progress-fill-mini" 
            :style="{ 
              width: `${animatedStats.progression}%`,
              backgroundColor: progressColor
            }"
          ></div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">📋</div>
        <div class="stat-content">
          <div class="stat-number">{{ Object.keys(selectionsByType).length }}</div>
          <div class="stat-label">Types d'Items</div>
        </div>
      </div>
    </div>

    <!-- Navigation par onglets -->
    <div class="tabs-navigation">
      <button 
        v-for="tab in [
          { id: 'overview', label: 'Vue d\'ensemble', icon: '📋' },
          { id: 'selections', label: 'Sélections', icon: '🎯' },
          { id: 'timeline', label: 'Timeline', icon: '📅' }
        ]"
        :key="tab.id"
        @click="activeTab = tab.id"
        class="tab-button"
        :class="{ active: activeTab === tab.id }"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        {{ tab.label }}
      </button>
    </div>

    <!-- Contenu principal avec hauteur fixe -->
    <div class="main-content">
      <Transition name="tab-content" mode="out-in">
        <!-- Vue d'ensemble -->
        <div v-if="activeTab === 'overview'" key="overview" class="tab-content">
          <div class="content-grid">
            <!-- Informations du projet -->
            <div class="info-card">
              <div class="card-header">
                <h3>🏗️ Informations Projet</h3>
              </div>
              <div class="card-content">
                <div class="info-grid">
                  <div class="info-item">
                    <span class="info-label">Projet Global</span>
                    <span class="info-value">{{ projetDetails?.projet_global?.projet }}</span>
                  </div>
                  <div v-if="projetDetails?.projet_global?.sous_projet" class="info-item">
                    <span class="info-label">Sous-projet</span>
                    <span class="info-value">{{ projetDetails.projet_global.sous_projet }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">FPack</span>
                    <span class="info-value">
                      {{ projetDetails?.fpack?.nom }} 
                      <span class="fpack-abbr">({{ projetDetails?.fpack?.fpack_abbr }})</span>
                    </span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">Client</span>
                    <span class="info-value">{{ projetDetails?.client?.nom }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Progression compacte -->
            <div class="progress-card">
              <div class="card-header">
                <h3>📈 Progression</h3>
              </div>
              <div class="card-content">
                <div class="progress-compact">
                  <div class="circular-progress-small">
                    <svg class="progress-ring-small" width="80" height="80" viewBox="0 0 80 80">
                      <circle cx="40" cy="40" r="35" fill="none" stroke="#e5e7eb" stroke-width="6"/>
                      <circle
                        cx="40" cy="40" r="35" fill="none" :stroke="progressColor" stroke-width="6"
                        stroke-linecap="round" :stroke-dasharray="219.91"
                        :stroke-dashoffset="219.91 - (219.91 * animatedStats.progression) / 100"
                        transform="rotate(-90 40 40)" class="progress-circle-fill"
                      />
                    </svg>
                    <div class="progress-center-small">
                      <div class="progress-percentage-small">{{ animatedStats.progression }}%</div>
                    </div>
                  </div>
                  
                  <div class="progress-info">
                    <div class="progress-item-compact">
                      <span class="progress-label">Requis:</span>
                      <span class="progress-value">{{ projetDetails?.config_columns }}</span>
                    </div>
                    <div class="progress-item-compact">
                      <span class="progress-label">Effectué:</span>
                      <span class="progress-value">{{ projetDetails?.selections.length || 0 }}</span>
                    </div>
                    <div class="progress-item-compact">
                      <span class="progress-label">Restant:</span>
                      <span class="progress-value">
                        {{ Math.max(0, (projetDetails?.config_columns || 0) - (projetDetails?.selections.length || 0)) }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Onglet Sélections -->
        <div v-else-if="activeTab === 'selections'" key="selections" class="tab-content">
          <div v-if="!projetDetails?.selections.length" class="empty-selections">
            <div class="empty-icon">🎯</div>
            <h3>Aucune sélection effectuée</h3>
            <p>Commencez par compléter votre projet.</p>
            <button @click="navigateToComplete" class="cta-button">
              📝 Commencer la configuration
            </button>
          </div>
          
          <div v-else class="selections-container">
            <div class="selections-summary">
              <h3>Résumé des Sélections</h3>
              <div class="summary-stats">
                <div v-for="(items, type) in selectionsByType" :key="String(type)" class="summary-item">
                  <span class="summary-icon">{{ typeIcons[String(type) as 'produit' | 'equipement' | 'robot'] }}</span>
                  <span class="summary-count">{{ items.length }}</span>
                  <span class="summary-type">{{ getTypeDisplayName(String(type)) }}</span>
                </div>
              </div>
            </div>
            
            <div class="selections-list-container">
              <div v-for="(items, type) in selectionsByType" :key="type" class="type-section">
                <div class="type-header">
                  <span class="type-icon">{{ typeIcons[String(type) as 'produit' | 'equipement' | 'robot'] }}</span>
                  <h4 class="type-title">{{ getTypeDisplayName(String(type)) }}</h4>
                  <span class="type-count">{{ items.length }}</span>
                </div>
                
                <div class="selections-list">
                  <div v-for="(selection, index) in items" :key="`${selection.groupe_id}-${selection.ref_id}`" class="selection-item">
                    <div class="selection-indicator">{{ index + 1 }}</div>
                    <div class="selection-content">
                      <div class="selection-group">{{ selection.groupe_nom }}</div>
                      <div class="selection-item-name">{{ selection.item_nom }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Onglet Timeline -->
        <div v-else-if="activeTab === 'timeline'" key="timeline" class="tab-content">
          <div class="timeline-container">
            <div class="timeline-header">
              <h3>📅 Timeline du Projet</h3>
            </div>
            
            <div class="timeline">
              <div class="timeline-item completed">
                <div class="timeline-marker">✅</div>
                <div class="timeline-content">
                  <div class="timeline-title">Projet créé</div>
                  <div class="timeline-description">Initialisation avec FPack {{ projetDetails?.fpack?.nom }}</div>
                </div>
              </div>
              
              <div class="timeline-item" :class="{ completed: projetDetails?.selections.length > 0 }">
                <div class="timeline-marker">{{ projetDetails?.selections.length > 0 ? '⚡' : '📋' }}</div>
                <div class="timeline-content">
                  <div class="timeline-title">Configuration en cours</div>
                  <div class="timeline-description">
                    {{ projetDetails?.selections.length || 0 }} / {{ projetDetails?.config_columns }} groupes
                  </div>
                </div>
              </div>
              
              <div class="timeline-item" :class="{ completed: projetDetails?.complet }">
                <div class="timeline-marker">{{ projetDetails?.complet ? '✅' : '⏳' }}</div>
                <div class="timeline-content">
                  <div class="timeline-title">Configuration terminée</div>
                  <div class="timeline-description">{{ projetDetails?.complet ? 'Terminé' : 'En attente' }}</div>
                </div>
              </div>
              
              <div class="timeline-item" :class="{ disabled: !projetDetails?.complet }">
                <div class="timeline-marker">💰</div>
                <div class="timeline-content">
                  <div class="timeline-title">Génération facture</div>
                  <div class="timeline-description">{{ projetDetails?.complet ? 'Disponible' : 'À venir' }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- État de chargement -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-content">
        <div class="loading-spinner"></div>
        <p>Chargement...</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.projet-details {
  max-width: 1400px;
  margin: 0 ;
  padding: 1.5rem;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
}

/* Header Section - Optimized for desktop */
.header-section {
  flex-shrink: 0;
  margin-bottom: 1.5rem;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  color: #6b7280;
  font-size: 0.9rem;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  text-decoration: none;
  color: inherit;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.breadcrumb-item.clickable {
  background: none;
  border: none;
  cursor: pointer;
}

.breadcrumb-item.clickable:hover {
  background: #f3f4f6;
  color: #374151;
}

.breadcrumb-item.current {
  color: #1f2937;
  font-weight: 500;
}

.breadcrumb-separator {
  color: #d1d5db;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 2rem;
  padding: 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
  position: relative;
  overflow: hidden;
}

.title-section {
  flex: 1;
}

.project-title {
  margin: 0 0 1rem 0;
  font-size: 2.2rem;
  font-weight: 700;
  line-height: 1.2;
  color: white;
}

.project-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  align-items: center;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  opacity: 0.9;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border-radius: 25px;
  font-weight: 600;
  font-size: 0.95rem;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn.primary {
  background: rgba(255, 255, 255, 0.9);
  color: #1f2937;
}

.action-btn.primary.complete {
  background: rgba(16, 185, 129, 0.9);
  color: white;
}

.action-btn.secondary {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-bottom: 0.75rem;
  flex-shrink: 0;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 1.5rem;
  position: relative;
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(to bottom, #3b82f6, #1d4ed8);
}

.stat-icon {
  font-size: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: #f8fafc;
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
}

.stat-label {
  font-size: 1rem;
  color: #6b7280;
}

.progress-bar-mini {
  width: 100%;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  margin-top: 0.75rem;
  overflow: hidden;
}

.progress-fill-mini {
  height: 100%;
  border-radius: 2px;
  transition: width 0.5s ease, background-color 0.5s ease;
}

.tabs-navigation {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 0.75rem;
  flex-shrink: 0;
  min-height: 0;
}

.tab-button {
  background: none;
  border: none;
  font-weight: 600;
  color: #6b7280;
  padding: 0.75rem 1.25rem;
  cursor: pointer;
  position: relative;
  transition: all 0.3s;
  font-size: 1rem;
}

.tab-button.active {
  color: #3b82f6;
}

.tab-button.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  height: 3px;
  width: 100%;
  background: #3b82f6;
  border-radius: 2px;
}

.main-content {
  overflow-y: auto;
  max-height: 380px;
  min-height: 0;
}

.tab-content {
  height: 100%;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1rem;
  height: 100%;
}

.info-card, .progress-card{
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  height: fit-content;
}

.card-header {
  padding: 1.25rem 1.25rem 0.75rem 1.25rem;
  border-bottom: 1px solid #f3f4f6;
}

.card-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
}

.card-content {
  padding: 1.25rem;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-height: 0;
}
.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-label {
  font-size: 0.9rem;
  color: #6b7280;
  font-weight: 500;
}

.info-value {
  font-size: 1rem;
  color: #1f2937;
  font-weight: 600;
}

.fpack-abbr {
  color: #6b7280;
  font-weight: 400;
}

.progress-compact {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.circular-progress-small {
  position: relative;
}

.progress-ring-small {
  transform: rotate(-90deg);
}

.progress-center-small {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.progress-percentage-small {
  font-size: 1.4rem;
  font-weight: 700;
  color: #1f2937;
}

.progress-info {
  flex: 1;
}

.progress-item-compact {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.progress-label {
  font-size: 0.9rem;
  color: #6b7280;
}

.progress-value {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
}


/* Selections Section - Compact */
.empty-selections {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-selections h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.2rem;
  color: #374151;
}

.empty-selections p {
  margin: 0 0 1.5rem 0;
  font-size: 0.9rem;
}

.cta-button {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cta-button:hover {
  background: #2563eb;
  transform: translateY(-1px);
}

.selections-container {
  height: 100%; 
  display: flex;
  flex-direction: column;
}

.selections-summary {
  margin-bottom: 1rem;
}

.selections-summary h3 {
  margin: 0 0 0.75rem 0;
  font-size: 1.1rem;
  color: #374151;
}

.summary-stats {
  display: flex;
  gap: 1rem;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.summary-icon {
  font-size: 1.2rem;
}

.summary-count {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1f2937;
}

.summary-type {
  font-size: 0.9rem;
  color: #6b7280;
}

.selections-list-container {

  overflow-y: auto;
  max-height: 100%;
  min-height: 0;
}

.type-section {
  margin-bottom: 1rem;
}

.type-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 8px;
}

.type-icon {
  font-size: 1.2rem;
}

.type-title {
  margin: 0;
  font-size: 1rem;
  color: #374151;
  flex: 1;
}

.type-count {
  font-size: 0.8rem;
  color: #6b7280;
  background: white;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
}

.selections-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.selection-item {
  background: white;
  padding: 0.75rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.selection-indicator {
  background: #3b82f6;
  color: white;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  border-radius: 50%;
  font-size: 0.8rem;
}

.selection-content {
  flex: 1;
}

.selection-group {
  font-weight: 600;
  font-size: 0.9rem;
  color: #374151;
}

.selection-item-name {
  font-size: 0.8rem;
  color: #6b7280;
}

.more-items {
  text-align: center;
  padding: 0.75rem;
  color: #6b7280;
  font-size: 0.9rem;
  font-style: italic;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px dashed #d1d5db;
}

/* Timeline - Compact */
.timeline-container {
  height: 100%;
}

.timeline-header {
  margin-bottom: 0.5rem;
}

.timeline-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #374151;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.timeline-item {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  opacity: 0.7;
  transition: all 0.3s;
}

.timeline-item.completed {
  opacity: 1;
}

.timeline-item.disabled {
  opacity: 0.3;
}

.timeline-marker {
  font-size: 1.2rem;
  width: 1.5rem;
  text-align: center;
  line-height: 1.5rem;
}

.timeline-content {
  background: white;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  flex: 1;
}

.timeline-title {
  font-weight: 600;
  font-size: 0.95rem;
  color: #111827;
  margin-bottom: 0.25rem;
}

.timeline-description {
  font-size: 0.85rem;
  color: #6b7280;
}

/* Loading overlay */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-content {
  text-align: center;
  color: #374151;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #3b82f6;
  border-top: 3px solid transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 0.75rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Animations */
.tab-content-enter-active,
.tab-content-leave-active {
  transition: all 0.3s ease;
}

.tab-content-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.tab-content-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

</style>