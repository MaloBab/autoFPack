<template>
  <div class="export-section">
    <div class="step-container active">
      <div class="step-header">
        <div class="step-indicator">
          <div class="step-number">1</div>
        </div>
        <div class="step-content-header">
          <h3>📤 Sélection des données à exporter</h3>
          <p class="step-description">Choisissez les projets à inclure dans votre export Excel</p>
        </div>
      </div>
      
      <div class="step-body">
        <!-- Contrôles d'export -->
        <div class="export-controls">
          <div class="selection-actions">
            <button class="btn btn-outline" @click="selectAllProjects">
              ✅ Tout sélectionner
            </button>
            <button class="btn btn-outline" @click="deselectAllProjects">
              ❌ Tout désélectionner
            </button>
          </div>
        </div>

        <!-- Sélection des projets -->
        <div class="projects-selection">
          <div class="projects-header">
            <h4>🏗️ Projets disponibles</h4>
            <div class="selected-count">
              {{ totalSelectedItems }} projet(s) sélectionné(s)
            </div>
          </div>
          
          <div class="projects-grid">
            <div 
              v-for="projet in projetsGlobaux" 
              :key="projet.id"
              class="project-card"
              :class="{ selected: isProjetSelected(projet.id) }"
              @click="toggleProjetSelection(projet.id)"
            >
              <div class="project-header">
                <div class="project-checkbox">
                  <input 
                    type="checkbox"
                    :checked="isProjetSelected(projet.id)"
                    @click.stop
                    @change="toggleProjetSelection(projet.id)"
                  />
                </div>
                <div class="project-info">
                  <h5 class="project-name">{{ projet.projet }}</h5>
                  <p class="project-client">🏢 {{ projet.client }}</p>
                </div>
              </div>
              
              <div class="project-stats" v-if="projet.sous_projets">
                <div class="stat-item">
                  <span class="stat-icon">📁</span>
                  <span class="stat-text">{{ projet.sous_projets.length }} sous-projets</span>
                </div>
                <div class="stat-item">
                  <span class="stat-icon">📦</span>
                  <span class="stat-text">
                    {{ projet.sous_projets.reduce((total, sp) => total + (sp.fpacks?.length || 0), 0) }} F-Packs
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Résumé de l'export -->
        <div class="export-summary">
          <h4>📈 Résumé de l'export</h4>
          <div class="summary-stats">
            <div class="stat-bubble">
              <div class="stat-number">{{ selectedExportData.project_ids.length }}</div>
              <div class="stat-label">Projets</div>
            </div>
            <div class="stat-bubble">
              <div class="stat-number">
                {{ projetsGlobaux
                  .filter(p => isProjetSelected(p.id))
                  .reduce((total, p) => total + (p.sous_projets?.length || 0), 0) }}
              </div>
              <div class="stat-label">Sous-projets</div>
            </div>
            <div class="stat-bubble">
              <div class="stat-number">
                {{ projetsGlobaux
                  .filter(p => isProjetSelected(p.id))
                  .reduce((total, p) => total + (p.sous_projets?.reduce((sp_total, sp) => sp_total + (sp.fpacks?.length || 0), 0) || 0), 0) }}
              </div>
              <div class="stat-label">F-Packs</div>
            </div>
          </div>
        </div>
        
        <div class="step-actions">
          <button 
            class="btn btn-success btn-large"
            :disabled="totalSelectedItems === 0 || isExporting"
            @click="executeExport"
          >
            <span v-if="!isExporting">📤 Générer l'export Excel</span>
            <span v-else>⏳ Génération en cours...</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed, ref } from 'vue'

// Types
interface ProjetGlobal {
  id: number
  projet: string
  client: string
  sous_projets?: SousProjet[]
}

interface SousProjet {
  id: number
  id_global: number
  nom: string
  fpacks?: FpackData[]
}

interface FpackData {
  id: number
  nom: string
  fpack_abbr: string
  FPack_number: string
  Robot_Location_Code: string
  contractor?: string
  required_delivery_time?: string
  delivery_site?: string
  tracking?: string
  selections?: Selection[]
}

interface Selection {
  groupe_id: number
  groupe_nom: string
  type_item: string
  ref_id: number
  item_nom: string
}

// Props
const props = defineProps<{
  projetsGlobaux: ProjetGlobal[]
}>()

// Emits
const emit = defineEmits<{
  'add-notification': [type: 'success' | 'warning' | 'error' | 'info', message: string]
}>()

// État local
const isExporting = ref(false)
const selectedExportData = reactive({
  project_ids: [] as number[],
  options: {
    includeSelections: true,
  },
  format: "excel"
})

// Computed
const totalSelectedItems = computed(() => {
  return selectedExportData.project_ids.length
})

// Méthodes de sélection
const isProjetSelected = (projetId: number): boolean => {
  return selectedExportData.project_ids.includes(projetId)
}

const toggleProjetSelection = (projetId: number) => {
  const index = selectedExportData.project_ids.indexOf(projetId)
  if (index > -1) {
    selectedExportData.project_ids.splice(index, 1)
  } else {
    selectedExportData.project_ids.push(projetId)
  }
}

const selectAllProjects = () => {
  selectedExportData.project_ids = props.projetsGlobaux.map(p => p.id)
}

const deselectAllProjects = () => {
  selectedExportData.project_ids = []
}

// Méthode d'export
const executeExport = async () => {
  if (selectedExportData.project_ids.length === 0) {
    emit('add-notification', 'error', 'Veuillez sélectionner au moins un projet')
    return
  }

  isExporting.value = true
  try {
    const response = await fetch('http://localhost:8000/export/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(selectedExportData)
    })
    
    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `export_fpack_${new Date().toISOString().slice(0, 10)}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      emit('add-notification', 'success', 'Export généré avec succès!')
    } else {
      emit('add-notification', 'error', 'Erreur lors de l\'export')
    }
  } catch (error) {
    emit('add-notification', 'error', 'Erreur lors de l\'export')
    console.error(error)
  } finally {
    isExporting.value = false
  }
}
</script>

<style scoped>
/* Conteneur principal avec scroll */
.export-section {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 30px 32px 60px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  scroll-behavior: smooth;
}

/* Scrollbar personnalisée */
.export-section::-webkit-scrollbar {
  width: 8px;
}

.export-section::-webkit-scrollbar-track {
  background: rgba(189, 195, 199, 0.2);
  border-radius: 4px;
}

.export-section::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #3498db, #9b59b6);
  border-radius: 4px;
}

.export-section::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #2980b9, #8e44ad);
}

/* Étapes avec animation */
.step-container {
  background: #ffffff;
  border-radius: 16px;
  margin-bottom: 24px;
  overflow: hidden;
  box-shadow: 0 6px 25px rgba(52, 73, 94, 0.08);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  transform: translateY(10px);
  opacity: 0;
  animation: slideInUp 0.5s ease-out forwards;
  position: relative;
  border: 1px solid rgba(189, 195, 199, 0.2);
}

.step-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3498db, #9b59b6, #e74c3c);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.5s ease-out;
}

.step-container.active::before {
  transform: scaleX(1);
}

.step-container.active {
  box-shadow: 0 12px 35px rgba(52, 152, 219, 0.12);
  transform: translateY(-2px);
}

@keyframes slideInUp {
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* En-têtes d'étapes */
.step-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 28px;
  background: linear-gradient(135deg, #fcfcfc 0%, #f8f9fa 100%);
  border-bottom: 1px solid rgba(189, 195, 199, 0.15);
  position: relative;
  overflow: hidden;
}

.step-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-number {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #3498db 0%, #9b59b6 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.1rem;
  box-shadow: 0 4px 15px rgba(52, 152, 219, 0.25);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.step-container.active .step-number {
  transform: scale(1.05) rotate(360deg);
  box-shadow: 0 6px 20px rgba(52, 152, 219, 0.3);
}

.step-content-header h3 {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 10px;
}

.step-description {
  margin: 4px 0 0 0;
  color: #7f8c8d;
  font-size: 0.95rem;
  font-weight: 500;
}

/* Corps des étapes */
.step-body {
  padding: 28px;
  animation: fadeIn 0.4s ease-out 0.2s both;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Contrôles d'export */
.export-controls {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 28px;
  padding: 20px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(52, 73, 94, 0.06);
  border: 1px solid #ecf0f1;
}

.selection-actions {
  display: flex;
  gap: 10px;
}

/* Sélection de projets */
.projects-selection {
  margin-bottom: 28px;
}

.projects-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.projects-header h4 {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 10px;
}

.selected-count {
  background: linear-gradient(135deg, #3498db 0%, #9b59b6 100%);
  color: white;
  padding: 6px 14px;
  border-radius: 16px;
  font-size: 0.85rem;
  font-weight: 600;
  box-shadow: 0 3px 10px rgba(52, 152, 219, 0.25);
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.project-card {
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(52, 73, 94, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
  cursor: pointer;
  position: relative;
}

.project-card:hover {
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.12);
  transform: translateY(-2px);
  border-color: #3498db;
}

.project-card.selected {
  border-color: #27ae60;
  background: linear-gradient(135deg, rgba(39, 174, 96, 0.02) 0%, rgba(46, 204, 113, 0.02) 100%);
  box-shadow: 0 8px 25px rgba(39, 174, 96, 0.12);
}

.project-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  position: relative;
  z-index: 2;
}

.project-checkbox {
  position: relative;
}

.project-checkbox input[type="checkbox"] {
  width: 20px;
  height: 20px;
  accent-color: #27ae60;
  border-radius: 3px;
  transition: all 0.3s ease;
}

.project-checkbox input[type="checkbox"]:checked {
  transform: scale(1.05);
}

.project-info {
  flex: 1;
}

.project-name {
  margin: 0 0 3px 0;
  font-size: 1rem;
  font-weight: 700;
  color: #2c3e50;
}

.project-client {
  margin: 0;
  color: #7f8c8d;
  font-size: 0.9rem;
  font-weight: 500;
}

.project-stats {
  padding: 0 18px 18px;
  display: flex;
  gap: 14px;
  position: relative;
  z-index: 2;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.85rem;
  color: #7f8c8d;
}

.stat-icon {
  font-size: 0.9rem;
}

/* Résumé export */
.export-summary {
  margin-bottom: 28px;
}

.export-summary h4 {
  margin-bottom: 20px;
  color: #2c3e50;
  font-size: 1.15rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
}

.summary-stats {
  display: flex;
  justify-content: center;
  gap: 28px;
  padding: 28px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(52, 73, 94, 0.06);
  border: 1px solid #ecf0f1;
}

.stat-bubble {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 18px;
  background: linear-gradient(135deg, #fcfcfc 0%, #f8f9fa 100%);
  border-radius: 50%;
  width: 100px;
  height: 100px;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  border: 2px solid transparent;
}

.stat-bubble::before {
  content: '';
  position: absolute;
  inset: -2px;
  background: linear-gradient(135deg, #3498db, #9b59b6, #e74c3c);
  border-radius: 50%;
  z-index: -1;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-bubble:hover {
  transform: translateY(-3px) scale(1.03);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.12);
}

.stat-bubble:hover::before {
  opacity: 1;
}

.stat-number {
  font-size: 1.6rem;
  font-weight: 800;
  background: linear-gradient(135deg, #3498db 0%, #9b59b6 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1;
}

.stat-label {
  color: #7f8c8d;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  text-align: center;
}

/* Actions d'étapes */
.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px solid #ecf0f1;
}

/* Boutons */
.btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 14px 28px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
}

.btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.15);
  transform: translateX(-100%);
  transition: transform 0.5s ease;
}

.btn:hover::before {
  transform: translateX(100%);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.btn:disabled:hover::before {
  transform: translateX(-100%);
}

.btn-success {
  background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);
}

.btn-success:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(39, 174, 96, 0.4);
}

.btn-outline {
  background: #ffffff;
  color: #3498db;
  border-color: #3498db;
  backdrop-filter: blur(10px);
}

.btn-outline:hover:not(:disabled) {
  background: linear-gradient(135deg, #3498db 0%, #9b59b6 100%);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(52, 152, 219, 0.3);
}

.btn-large {
  padding: 18px 36px;
  font-size: 1rem;
  font-weight: 700;
}
</style>