<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

interface DashboardStats {
  produits: number
  equipements: number
  robots: number
  clients: number
  fournisseurs: number
  fpacks: number
  groupes: number
  relations: number
  config_columns: number
  projets: number
  [key: string]: number
}

const stats = ref<DashboardStats | null>(null)
const isLoading = ref(true)
const currentStep = ref(0)
const hoveredCard = ref<string | null>(null)
let autoStepInterval: number | undefined

const cardConfigs: Array<{
  key: keyof DashboardStats
  icon: string
  color: string
  bgColor: string
  label: string
}> = [
  { key: 'produits', icon: '📦', color: '#2563eb', bgColor: '#eff6ff', label: 'Produits'},
  { key: 'equipements', icon: '⚙️', color: '#059669', bgColor: '#ecfdf5', label: 'Équipements'},
  { key: 'robots', icon: '🤖', color: '#7c3aed', bgColor: '#f3e8ff', label: 'Robots'},
  { key: 'clients', icon: '👥', color: '#dc2626', bgColor: '#fef2f2', label: 'Clients'},
  { key: 'fournisseurs', icon: '🏭', color: '#ea580c', bgColor: '#fff7ed', label: 'Fournisseurs'},
  { key: 'fpacks', icon: '📋', color: '#4f46e5', bgColor: '#eef2ff', label: 'F-Packs'},
  { key: 'projets', icon: '📈', color: '#be185d', bgColor: '#fdf2f8', label: 'Projets'}
]

const workflowSteps = [
    {
    id: 'relations',
    title: "🤝 Renseignez les différents acteurs",
    subtitle: "Clients et fournisseurs",
    description: "Ajouter facilement vos clients et fournisseurs pour avoir toutes les informations importantes à portée de main et préparer vos projets.",
    actions: ["Enregistrer les clients", "Gérer les fournisseurs"],
    color: "#99ccff",
    icon: "🤝"
  },
  {
    id: 'setup',
    title: "🏗️ Construire la base",
    subtitle: "Ajouter tous les éléments",
    description: "Créer les produits avec leurs prix, définissez vos équipements et configurez vos robots avec leurs spécifications techniques. Définissez ensuite les incompatibilités",
    actions: ["Ajouter des produits", "Créer des équipements", "Configurer des robots", "Définir des incompatibilités"],
    color: "#66b3ff",
    icon: "🏗️"
  },
  {
    id: 'fpacks',
    title: "📦 Créer des F-Packs",
    subtitle: "Des modèles prêts à l'emploi",
    description: "Créer facilement des configurations types avec des options groupées et une gestion d'incompatibilités.",
    actions: ["Définir des modèles", "Créer des groupes", "Configurer des options"],
    color: "#3399ff",
    icon: "📦"
  },
  {
    id: 'projects',
    title: "🎯 Définir des projets",
    subtitle: "Organisation et suivi",
    description: "Configurez vos projets à partir des modèles de F-Packs, ajoutez des sous-projets et renseignez le matériel nécéssaire à chaque étape.",
    actions: ["Nouveau projet", "Associer F-Packs", "Compléter les besoins"],
    color: "#0066cc",
    icon: "🎯"
  },
  {
    id: 'validate',
    title: "✅ Documents générés",
    subtitle: "Matrices et Factures instantanés",
    description: "Générez automatiquement vos exports Excel et vos factures Disponible dans l'onglet Projets et Import/Export.",
    actions: ["Générer des factures", "Exporter vers Excel"],
    color: "#003366",
    icon: "✅"
  }
]

const totalItems = computed(() => {
  if (!stats.value) return 0
  return Object.values(stats.value).reduce((sum, val) => sum + val, 0)
})

async function fetchStats() {
  try {
    const response = await axios.get('http://localhost:8000/dashboard/stats')
    stats.value = response.data
  } catch (err) {
    console.warn('Impossible de récupérer les données du serveur, utilisation des données de démonstration')

  } finally {
    isLoading.value = false
  }
}

function selectStep(index: number) {
  currentStep.value = index
  startAutoStep()
}

function nextStep() {
  currentStep.value = (currentStep.value + 1) % workflowSteps.length
}

function startAutoStep() {
  if (autoStepInterval) clearInterval(autoStepInterval)

  autoStepInterval = setInterval(() => {
    nextStep()
  }, 6000)
}

onMounted(() => {
  fetchStats()
  startAutoStep()
})
</script>

<template>
  <div class="dashboard">
    <header class="dashboard-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="main-title">
            <div class="title-icon-container">
              <span class="title-icon">📊</span>
              <div class="title-glow"></div>
            </div>
            <div class="title-text">
              <span class="title-main">Tableau de bord</span>
              <span class="title-subtitle">Gestion de F-Packs</span>
            </div>
          </h1>
        </div>
        <div class="header-right">
          <div class="total-counter">
            <div class="counter-decoration">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                viewBox="0 0 32 32" 
                class="w-8 h-8 text-gray-700"
                fill="none" 
                stroke="currentColor" 
                stroke-width="2"
                stroke-linecap="round" 
                stroke-linejoin="round"
              >
                <rect x="4" y="6" width="18" height="12" rx="2" ry="2" stroke="currentColor" fill="none"/>
                <rect x="6" y="9" width="18" height="12" rx="2" ry="2" stroke="currentColor" fill="none" opacity="0.7"/>
                <rect x="8" y="12" width="18" height="12" rx="2" ry="2" stroke="currentColor" fill="none" opacity="0.4"/>
                
                <circle cx="24" cy="8" r="6" fill="currentColor"/>
                <text x="25" y="10" text-anchor="middle" font-size="7" stroke="none" font-family="sans-serif" fill="white">n°</text>
              </svg>
            </div>
            <div class="counter-content">
              <span class="counter-value">{{ totalItems.toLocaleString() }}</span>
              <span class="counter-label">éléments totaux</span>
            </div>
          </div>
        </div>
      </div>
    </header>

    <div class="dashboard-content">
      <section class="stats-section">        
        <div class="stats-grid">
          <div 
            v-for="config in cardConfigs" 
            :key="config.key"
            class="stat-card"
            :class="{ 
              'hovered': hoveredCard === config.key 
            }"
            :style="{ 
              '--card-color': config.color,
              '--card-bg': config.bgColor 
            }"
            @mouseenter="hoveredCard = config.key.toString()"
            @mouseleave="hoveredCard = null"
          >
            <div class="card-glow"></div>
            <div class="card-content">
              <div class="card-header">
                <div class="icon-container">
                  <span class="card-icon">{{ config.icon }}</span>
                </div>
                <div class="card-value">{{ stats?.[config.key] || 0 }}</div>
              </div>
              <div class="card-info">
                <h3 class="card-title">{{ config.label }}</h3>
              </div>
              <div class="card-progress">
                <div class="progress-track">
                  <div 
                    class="progress-fill"
                    :style="{ width: `${Math.min((stats?.[config.key] || 0) / totalItems * 100, 100)}%` }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="workflow-section">
        <div class="workflow-container">
          <div class="timeline-nav">
            <div class="timeline-line"></div>
            <div 
              v-for="(step, index) in workflowSteps" 
              :key="step.id"
              class="timeline-step"
              :class="{ 'active': currentStep === index, 'completed': currentStep > index }"
              @click="selectStep(index)"
            >
              <div class="timeline-dot">
                <span v-if="currentStep > index" class="check-icon">✓</span>
                <span v-else class="step-number">{{ index + 1 }}</span>
              </div>
              <div class="timeline-content">
                <h4 class="timeline-title">{{ step.title }}</h4>
                <p class="timeline-subtitle">{{ step.subtitle }}</p>
              </div>
            </div>
          </div>

          <div class="workflow-content">
            <div class="workflow-card" :style="{ '--step-color': workflowSteps[currentStep].color }">
              <div class="workflow-header">
                <div class="workflow-icon">{{ workflowSteps[currentStep].icon }}</div>
                <div class="workflow-title-section">
                  <h3 class="workflow-title">{{ workflowSteps[currentStep].title }}</h3>
                  <p class="workflow-subtitle">{{ workflowSteps[currentStep].subtitle }}</p>
                </div>
              </div>
              
              <p class="workflow-description">{{ workflowSteps[currentStep].description }}</p>
              
              <div class="workflow-actions-preview">
                <div 
                  v-for="action in workflowSteps[currentStep].actions.slice(0, 3)" 
                  :key="action"
                  class="action-chip"
                >
                  {{ action }}
                </div>
              </div>
              <div class="progress-section">
                <div class="progress-info">
                  <span class="progress-text">Étape {{ currentStep + 1 }} / {{ workflowSteps.length }}</span>
                </div>
                <div class="progress-container">
                  <div class="progress-bar">
                    <div 
                      class="progress-indicator"
                      :style="{ width: `${((currentStep + 1) / workflowSteps.length) * 100}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
:root {
  --bg-primary: #f7f7f7;
  --bg-white: #ffffff;
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  --text-light: #9ca3af;
  --border-color: #e5e7eb;
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  --border-radius: 16px;
  --border-radius-sm: 8px;
  --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  --transition-fast: all 0.15s ease-out;
}

.dashboard {
  max-height: 90vh;
  min-height: auto;
  background: var(--bg-primary);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  color: var(--text-primary);
  overflow-y: auto;
}

.dashboard-header {
  background: linear-gradient(135deg, #003366 0%, #3399ff 100%);
  border: none;
  padding: 1.5rem 0;
  position: relative;
  overflow: hidden;
}

.dashboard-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="20" cy="20" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="80" cy="40" r="0.5" fill="rgba(255,255,255,0.1)"/><circle cx="40" cy="80" r="1.5" fill="rgba(255,255,255,0.05)"/></svg>');
  animation: float-particles 20s linear infinite;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 2;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.main-title {
  display: flex;
  align-items: center;
  gap: 2rem;
  margin: 0;
  color: white;
}

.title-icon-container {
  position: relative;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.title-icon {
  font-size: 3rem;
  position: relative;
  z-index: 2;
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
  animation: gentle-bounce 3s infinite;
}

.title-glow {
  position: absolute;
  inset: -10px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255,255,255,0.2), transparent 60%);
  animation: pulse-glow 2s ease-in-out infinite alternate;
}

.title-text {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.title-main {
  font-size: 2.5rem;
  font-weight: 800;
  line-height: 1;
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.title-subtitle {
  font-size: 1rem;
  font-weight: 400;
  opacity: 0.9;
  font-style: italic;
}

.total-counter {
  position: relative;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.5rem 2rem;
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.2);
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
}

.counter-decoration {
  position: relative;
  width: 60px;
  height: 60px;
}

.counter-content {
  text-align: left;
  color: white;
}

.counter-value {
  display: block;
  font-size: 2.75rem;
  font-weight: 900;
  line-height: 1;
  margin-bottom: 0.25rem;
  text-shadow: 0 2px 4px rgba(0,0,0,0.2);
  animation: number-glow 2s ease-in-out infinite alternate;
}

.counter-label {
  display: block;
  font-size: 0.875rem;
  opacity: 0.9;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.dashboard-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.section-header {
  margin-bottom: 2rem;
  text-align: center;
}

.section-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
}

.section-subtitle {
  color: var(--text-secondary);
  font-size: 1rem;
  margin: 0;
}

.stats-section {
  margin-bottom: 2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 2rem;
}

.stat-card {
  background: color-mix(in srgb, var(--card-color) 10%, white);
  border-radius: 20%;
  padding: 5px;
  cursor: pointer;
  transition: var(--transition);
  overflow: hidden;
  position: relative;
}

.stat-card:hover {
  background: color-mix(in srgb, var(--card-color) 20%, white);
  transform: translateY(-4px);
  scale: 1.05;
  
}

.card-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--card-color);
  opacity: 0;
  transition: var(--transition);
}

.stat-card:hover .card-glow, .card-glow {
  opacity: 1;
}

.card-content {
  padding: 0.5rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.icon-container {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--card-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.card-icon {
  font-size: 1.75rem;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
}

.card-value {
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--card-color);
  line-height: 1;
}

.card-info {
  margin-bottom: 1rem;
}

.card-title {
  margin: 0 0 0.25rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
}


.card-progress {
  margin-top: 1rem;
}

.progress-track {
  width: 100%;
  height: 4px;
  background: #e1e1e1;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--card-color);
  border-radius: 2px;
  transition: width 1s ease-out;
}
.workflow-container {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 3rem;
  background: var(--bg-white);
  border-radius: var(--border-radius);
  padding: 2rem;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-color);
}

.timeline-nav {
  position: relative;
  padding-left: 1rem;
}

.timeline-line {
  position: absolute;
  left: 2rem;
  top: 2rem;
  bottom: 2rem;
  width: 2px;
  background: linear-gradient(to bottom, #e5e7eb, #d1d5db);
}

.timeline-step {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem 0;
  cursor: pointer;
  transition: var(--transition);
  border-radius: var(--border-radius-sm);
  margin: 0 -0.5rem;
  position: relative;
  z-index: 2;
}

.timeline-step:hover {
  background: #f9fafb;
}

.timeline-step.active {
  background: #eff6ff;
}

.timeline-dot {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--bg-white);
  border: 3px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  transition: var(--transition);
  flex-shrink: 0;
  position: relative;
  z-index: 3;
}

.timeline-step.active .timeline-dot {
  border-color: #3b82f6;
  background: #3b82f6;
  color: white;
}

.timeline-step.completed .timeline-dot {
  border-color: #3b82f6;
  background: #3b82f6;
  color: white;
}

.check-icon {
  font-size: 1rem;
}

.timeline-content {
  flex: 1;
  min-width: 0;
}

.timeline-title {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.timeline-subtitle {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.workflow-content {
  display: flex;
  flex-direction: column;
}

.workflow-card {
  background: linear-gradient(135deg, var(--step-color), color-mix(in srgb, var(--step-color) 90%, white));
  color: white;
  padding: 2rem;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-lg);
  position: relative;
  overflow: hidden;
}

.workflow-card::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 100px;
  height: 100px;
  background: radial-gradient(circle, rgba(255,255,255,0.1), transparent);
  border-radius: 50%;
  transform: translate(30%, -30%);
}

.workflow-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.workflow-icon {
  font-size: 3rem;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}

.workflow-title-section {
  flex: 1;
}

.workflow-title {
  margin: 0 0 0.5rem 0;
  font-size: 1.75rem;
  font-weight: 700;
}

.workflow-subtitle {
  margin: 0;
  font-size: 1rem;
  opacity: 0.9;
}

.details-toggle {
  background: rgba(255,255,255,0.2);
  border: none;
  color: white;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
}

.details-toggle:hover {
  background: rgba(255,255,255,0.3);
}

.details-toggle span {
  transition: var(--transition);
}

.rotate-180 {
  transform: rotate(180deg);
}

.workflow-description {
  font-size: 1.125rem;
  line-height: 1.6;
  margin-bottom: 1.5rem;
  opacity: 0.95;
}

.workflow-actions-preview {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.action-chip {
  background: rgba(255,255,255,0.15);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 500;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.1);
}

.workflow-details {
  background: rgba(255,255,255,0.1);
  padding: 1.5rem;
  border-radius: var(--border-radius-sm);
  margin-bottom: 1.5rem;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.1);
}

.details-content h4 {
  margin: 0 0 1rem 0;
  font-size: 1.125rem;
  font-weight: 600;
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.95rem;
}

.action-bullet {
  color: rgba(255,255,255,0.7);
  font-weight: 600;
}

.detail-actions {
  display: flex;
  gap: 1rem;
}

.action-btn {
  padding: 0.75rem 1.5rem;
  border-radius: var(--border-radius-sm);
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
  border: none;
  font-size: 0.875rem;
}

.action-btn.primary {
  background: white;
  color: var(--step-color);
}

.action-btn.primary:hover {
  background: #f9fafb;
}

.action-btn.secondary {
  background: transparent;
  color: white;
  border: 1px solid rgba(255,255,255,0.3);
}

.action-btn.secondary:hover {
  background: rgba(255,255,255,0.1);
}

.progress-section {
  margin-top: 2rem;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  opacity: 0.9;
}

.progress-container {
  position: relative;
}

.progress-bar {
  width: 100%;
  height: 6px;
  background: rgba(255,255,255,0.2);
  border-radius: 3px;
  overflow: hidden;
}

.progress-indicator {
  height: 100%;
  background: white;
  border-radius: 3px;
  transition: width 0.8s ease-out;
  box-shadow: 0 0 10px rgba(255,255,255,0.3);
}


.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.quick-action-card {
  background: var(--bg-white);
  border: 2px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 1.5rem;
  cursor: pointer;
  transition: var(--transition);
  display: flex;
  align-items: center;
  gap: 1rem;
  text-align: left;
  position: relative;
  overflow: hidden;
}

.quick-action-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.05), transparent);
  transition: left 0.5s ease-out;
}

.quick-action-card:hover::before {
  left: 100%;
}

.quick-action-card:hover {
  border-color: #3b82f6;
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.action-icon-container {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
  z-index: 2;
}

.action-icon {
  font-size: 1.5rem;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}

.action-content {
  flex: 1;
  min-width: 0;
}

.action-content h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
}

.action-content p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.action-arrow {
  font-size: 1.25rem;
  color: var(--text-light);
  transition: var(--transition);
}

.slide-down-enter-active, .slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from, .slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
  max-height: 0;
}

.slide-down-enter-to, .slide-down-leave-from {
  opacity: 1;
  transform: translateY(0);
  max-height: 300px;
}

@keyframes gentle-bounce {
  0%, 100% { 
    transform: translateY(0) rotate(0deg); 
  }
  50% { 
    transform: translateY(-5px) rotate(5deg); 
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

@keyframes float-particles {
  0% { transform: translateX(0); }
  100% { transform: translateX(100px); }
}

@keyframes pulse-glow {
  0% { opacity: 0.5; transform: scale(1); }
  100% { opacity: 0.8; transform: scale(1.1); }
}


@keyframes number-glow {
  0% { text-shadow: 0 2px 4px rgba(0,0,0,0.2); }
  100% { text-shadow: 0 2px 4px rgba(0,0,0,0.2), 0 0 20px rgba(255,255,255,0.3); }
}

</style>