<script setup lang="ts">


interface ProjetGlobal {
  id: number
  projet: string
  client: number 
  sous_projets?: SousProjet[]
}

interface SousProjet {
  id: number
  nom: string
  id_global: number
}

interface FpackItem {
  FPackNumber: string 
  FPack_number: string
  RobotLocationCode: string 
  Robot_Location_Code: string
  selectedProjetGlobal: number | null
  selectedSousProjet: number | null
  selectedFPackTemplate?: any 
  [key: string]: any
}

const props = defineProps<{
  step: number
  active: boolean
  completed: boolean
  visible: boolean
  previewData: any[]
  previewColumns: string[]
  fpackList: FpackItem[]
  projetsGlobaux: ProjetGlobal[]
  fpackTemplates: any
  allFPacksConfigured: boolean
  clients: any[]
}>()

const emit = defineEmits<{
  projetGlobalChange: [fpack: FpackItem]
  fpackTemplateChange: [fpack: FpackItem]
  projectsAssigned: []
  previousStep: []
}>()


const onProjetGlobalChange = (fpack: FpackItem) => {
  fpack.selectedSousProjet = null
  emit('projetGlobalChange', fpack)
}

const onFPackTemplateChange = (fpack: FpackItem) => {
  emit('fpackTemplateChange', fpack)
}

const getAvailableSousProjets = (projetGlobalId: number | null) => {
  if (!projetGlobalId) return []
  const projet = props.projetsGlobaux.find(p => p.id === projetGlobalId)
  return projet?.sous_projets || []
}

const getAvailableFPackTemplates = (projetGlobalId: number | null) => {
  if (!projetGlobalId) return []
  
  const projet = props.projetsGlobaux.find(p => p.id === projetGlobalId)
  if (!projet) return []
  
  const clientId = projet.client
  return props.fpackTemplates.fpack_templates.filter((template:any) => template.client === getClientName(clientId))
}

const getClientName = (clientId: number | null) => {
  if (!clientId) return 'N/A'
  
  const nomClient = props.clients.find(c => c.id === clientId)?.nom
  return nomClient || 'N/A'
  }

const getSelectedClientId = (fpack: FpackItem): number | null => {
  if (!fpack.selectedProjetGlobal) return null
  const projet = props.projetsGlobaux.find(p => p.id === fpack.selectedProjetGlobal)
  return projet?.client || null
}


</script>

<template>
  <div class="step-container" :class="{ active, completed }">
    <div class="step-header">
      <div class="step-indicator">
        <div class="step-number">{{ step }}</div>
        <div class="step-line"></div>
      </div>
      <div class="step-content-header">
        <h3>Configuration et attribution</h3>
        <p class="step-description">Attribuez chaque F-Pack à un projet et sélectionnez le template approprié</p>
      </div>
    </div>
    
    <div class="step-body" v-show="visible">
      <div v-if="previewData.length > 0" class="data-preview">
        <div class="preview-header">
          <h4>Aperçu des données</h4>
          <div class="preview-stats">
            <span class="stat-badge">{{ previewData.length }} lignes</span>
            <span class="stat-badge">{{ previewColumns.length }} colonnes</span>
          </div>
        </div>
        <div class="preview-table-container">
          <table class="preview-table">
            <thead>
              <tr>
                <th v-for="column in previewColumns" :key="column">
                  {{ column }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in previewData.slice(0, 3)" :key="index">
                <td v-for="column in previewColumns" :key="column">
                  {{ row[column] || '-' }}
                </td>
                <td v-if="previewColumns.length > 6">...</td>
              </tr>
            </tbody>
          </table>
          <p class="preview-note">Affichage partiel des premières lignes et colonnes</p>
        </div>
      </div>

      <div class="fpack-configuration">
        <div class="config-header">
          <h4>Configuration des F-Packs</h4>
          <p class="config-description">
            Chaque F-Pack doit être associé à un projet global, un sous-projet et un template F-Pack
          </p>
        </div>
        
        <div class="fpack-grid">
          <div 
            v-for="(fpack, index) in fpackList" 
            :key="index"
            class="fpack-card"
            :class="{ 
              'complete': fpack.selectedProjetGlobal && fpack.selectedSousProjet && fpack.selectedFPackTemplate,
              'incomplete': !fpack.selectedProjetGlobal || !fpack.selectedSousProjet || !fpack.selectedFPackTemplate
            }"
          >
            <div class="fpack-info">
              <div class="fpack-number">{{ fpack.FPack_number }}</div>
              <div class="robot-location">{{ fpack.Robot_Location_Code }}</div>
              <div class="client-info" v-if="getSelectedClientId(fpack)">
                Client: {{ getClientName(getSelectedClientId(fpack)) }}
              </div>
            </div>
            
            <div class="config-selectors">
              <div class="selector-group">
                <label class="selector-label">Projet Global</label>
                <select 
                  v-model="fpack.selectedProjetGlobal"
                  @change="onProjetGlobalChange(fpack)"
                  class="form-select"
                >
                  <option 
                    v-for="projet in projetsGlobaux" 
                    :key="projet.id"
                    :value="projet.id"
                  >
                    {{ projet.projet }} ({{ getClientName(projet.client) || 'Client N/A' }})
                  </option>
                </select>
              </div>
              
              <div class="selector-group">
                <label class="selector-label">Sous-projet</label>
                <select 
                  v-model="fpack.selectedSousProjet"
                  :disabled="!fpack.selectedProjetGlobal"
                  class="form-select"
                >
                  <option 
                    v-for="sousProjet in getAvailableSousProjets(fpack.selectedProjetGlobal)" 
                    :key="sousProjet.id"
                    :value="sousProjet.id"
                  >
                    {{ sousProjet.nom }}
                  </option>
                </select>
              </div>

              <div class="selector-group">
                <label class="selector-label">Template F-Pack</label>
                <select 
                  v-model="fpack.selectedFPackTemplate"
                  @change="onFPackTemplateChange(fpack)"
                  :disabled="!fpack.selectedProjetGlobal"
                  class="form-select"
                >
                  <option 
                    v-for="template in getAvailableFPackTemplates(fpack.selectedProjetGlobal)" 
                    :key="template.id"
                    :value="template.id"
                  >
                    {{ template.nom }} ({{ template.abbreviation }})
                  </option>
                </select>
              </div>
            </div>

            <div class="status-indicator">
              <div class="status-dot" :class="{ 
                'complete': fpack.selectedProjetGlobal && fpack.selectedSousProjet && fpack.selectedFPackTemplate,
                'incomplete': !fpack.selectedProjetGlobal || !fpack.selectedSousProjet || !fpack.selectedFPackTemplate
              }"></div>
              <span class="status-text">
                {{ (fpack.selectedProjetGlobal && fpack.selectedSousProjet && fpack.selectedFPackTemplate) ? 'Configuré' : 'En attente' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="progress-summary">
        <div class="progress-info">
          <span class="progress-text">
            Progression: {{ fpackList.filter(f => f.selectedProjetGlobal && f.selectedSousProjet && f.selectedFPackTemplate).length }} / {{ fpackList.length }} F-Packs configurés
          </span>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: `${(fpackList.filter(f => f.selectedProjetGlobal && f.selectedSousProjet && f.selectedFPackTemplate).length / fpackList.length) * 100}%` }"
            ></div>
          </div>
        </div>
      </div>
      
      <div class="step-actions">
        <button class="btn btn-secondary" @click="emit('previousStep')">
          Retour
        </button>
        <button 
          class="btn btn-primary"
          :disabled="!allFPacksConfigured"
          @click="emit('projectsAssigned')"
        >
          Continuer vers le mapping
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
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

.step-container.completed {
  background: linear-gradient(135deg, rgba(46, 204, 113, 0.02) 0%, rgba(39, 174, 96, 0.02) 100%);
  border: 1px solid rgba(46, 204, 113, 0.2);
}

@keyframes slideInUp {
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

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

.step-container.completed .step-number {
  background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
  box-shadow: 0 4px 15px rgba(39, 174, 96, 0.25);
}

.step-line {
  width: 60px;
  height: 2px;
  background: #ecf0f1;
  border-radius: 1px;
  position: relative;
  overflow: hidden;
}

.step-line::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 0;
  background: linear-gradient(90deg, #3498db, #9b59b6);
  border-radius: 1px;
  transition: width 0.6s ease-out 0.2s;
}

.step-container.active .step-line::before {
  width: 100%;
}

.step-container.completed .step-line::before {
  background: linear-gradient(90deg, #27ae60, #2ecc71);
  width: 100%;
}

.step-content-header h3 {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  color: #2c3e50;
}

.step-description {
  margin: 4px 0 0 0;
  color: #7f8c8d;
  font-size: 0.95rem;
  font-weight: 500;
}

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

.data-preview {
  margin-bottom: 28px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.preview-header h4 {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  color: #2c3e50;
}

.preview-stats {
  display: flex;
  gap: 10px;
}

.stat-badge {
  background: linear-gradient(135deg, #3498db 0%, #9b59b6 100%);
  color: white;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 0.8rem;
  font-weight: 600;
  box-shadow: 0 3px 10px rgba(52, 152, 219, 0.25);
  transition: all 0.3s ease;
}

.preview-table-container {
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 6px 20px rgba(52, 73, 94, 0.06);
  border: 1px solid #ecf0f1;
  overflow-x: auto;
}

.preview-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.preview-table th {
  background: linear-gradient(135deg, #fcfcfc 0%, #f8f9fa 100%);
  padding: 14px 16px;
  font-weight: 600;
  text-align: left;
  color: #34495e;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  position: relative;
}

.preview-table th::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #3498db, #9b59b6);
}

.preview-table td {
  padding: 14px 16px;
  color: #7f8c8d;
  font-size: 0.9rem;
  border-bottom: 1px solid #f8f9fa;
  transition: all 0.2s ease;
}

.preview-table tr:hover td {
  background: rgba(52, 152, 219, 0.02);
  color: #34495e;
}

.preview-note {
  padding: 10px 16px;
  text-align: center;
  color: #7f8c8d;
  font-size: 0.8rem;
  background: linear-gradient(135deg, #fcfcfc 0%, #f8f9fa 100%);
  margin: 0;
  font-style: italic;
}

.fpack-configuration {
  margin-bottom: 28px;
}

.config-header {
  margin-bottom: 20px;
}

.config-header h4 {
  margin: 0 0 8px 0;
  color: #2c3e50;
  font-size: 1.15rem;
  font-weight: 700;
}

.config-description {
  margin: 0;
  color: #7f8c8d;
  font-size: 0.95rem;
}

.fpack-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 20px;
}

.fpack-card {
  background: #ffffff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 3px 15px rgba(52, 73, 94, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid #ecf0f1;
  position: relative;
  overflow: hidden;
}

.fpack-card.complete {
  border-color: #27ae60;
  background: linear-gradient(135deg, rgba(46, 204, 113, 0.02) 0%, rgba(39, 174, 96, 0.02) 100%);
}

.fpack-card.incomplete {
  border-color: #e67e22;
  background: linear-gradient(135deg, rgba(230, 126, 34, 0.02) 0%, rgba(211, 84, 0, 0.02) 100%);
}

.fpack-card:hover {
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.12);
  transform: translateY(-2px);
}

.fpack-info {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ecf0f1;
}

.fpack-number {
  font-weight: 700;
  font-size: 1.2rem;
  color: #2c3e50;
  margin-bottom: 4px;
}

.robot-location {
  color: #7f8c8d;
  font-size: 0.95rem;
  font-weight: 500;
  margin-bottom: 4px;
}

.client-info {
  color: #3498db;
  font-size: 0.85rem;
  font-weight: 600;
}

.config-selectors {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.selector-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.selector-label {
  font-weight: 600;
  color: #34495e;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.form-select {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #ecf0f1;
  border-radius: 8px;
  background: #ffffff;
  font-size: 0.9rem;
  font-weight: 500;
  color: #34495e;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.form-select:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
  transform: translateY(-1px);
}

.form-select:disabled {
  background: #f8f9fa;
  color: #95a5a6;
  cursor: not-allowed;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ecf0f1;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.status-dot.complete {
  background: #27ae60;
  box-shadow: 0 0 0 3px rgba(39, 174, 96, 0.2);
}

.status-dot.incomplete {
  background: #e67e22;
  box-shadow: 0 0 0 3px rgba(230, 126, 34, 0.2);
}

.status-text {
  font-size: 0.85rem;
  font-weight: 600;
  color: #34495e;
}

.progress-summary {
  margin-bottom: 28px;
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #ecf0f1 100%);
  border-radius: 12px;
  border: 1px solid #ecf0f1;
}

.progress-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-text {
  font-weight: 600;
  color: #34495e;
  font-size: 0.95rem;
}

.progress-bar {
  height: 8px;
  background: #ecf0f1;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #27ae60, #2ecc71);
  border-radius: 4px;
  transition: width 0.5s ease;
  position: relative;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px solid #ecf0f1;
}

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

.btn-primary {
  background: linear-gradient(135deg, #3498db 0%, #9b59b6 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(52, 152, 219, 0.4);
}

.btn-secondary {
  background: linear-gradient(135deg, #7f8c8d 0%, #95a5a6 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(127, 140, 141, 0.3);
}

.btn-secondary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(127, 140, 141, 0.4);
}
</style>