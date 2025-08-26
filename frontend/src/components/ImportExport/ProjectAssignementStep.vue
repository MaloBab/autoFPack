<script setup lang="ts">
import { computed } from 'vue'

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
}

interface FpackItem {
  FPackNumber: string
  RobotLocationCode: string
  selectedProjetGlobal: number | null
  selectedSousProjet: number | null
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
  clients: any[]
  allFPacksHaveProject: boolean
  selectedClient: number | null
}>()

const emit = defineEmits<{
  'update:selectedClient': [value: number | null]
  projetGlobalChange: [fpack: FpackItem]
  projectsAssigned: []
  previousStep: []
  getAvailableSousProjets: [projetGlobalId: number | null]
}>()

const selectedClient = computed({
  get: () => props.selectedClient,
  set: (value) => emit('update:selectedClient', value)
})

const onProjetGlobalChange = (fpack: FpackItem) => {
  emit('projetGlobalChange', fpack)
}

const getAvailableSousProjets = (projetGlobalId: number | null) => {
  if (!projetGlobalId) return []
  const projet = props.projetsGlobaux.find(p => p.id === projetGlobalId)
  return projet?.sous_projets || []
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
        <h3>👁️ Aperçu et attribution des projets</h3>
        <p class="step-description">Vérifiez les données et attribuez les F-Packs aux projets</p>
      </div>
    </div>
    
    <div class="step-body" v-show="visible">
      <!-- Aperçu des données -->
      <div v-if="previewData.length > 0" class="data-preview">
        <div class="preview-header">
          <h4>📋 Aperçu des données</h4>
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
              <tr v-for="(row, index) in previewData.slice(0, 4)" :key="index">
                <td v-for="column in previewColumns" :key="column">
                  {{ row[column] || '-' }}
                </td>
              </tr>
            </tbody>
          </table>
          <p class="preview-note">Affichage partiel des données</p>
        </div>
      </div>

      <!-- Attribution des projets par F-Pack -->
      <div class="fpack-assignment">
        <h4>🎯 Attribution des F-Packs</h4>
        <div class="fpack-grid">
          <div 
            v-for="(fpack, index) in fpackList" 
            :key="index"
            class="fpack-card"
          >
            <div class="fpack-info">
              <div class="fpack-number">{{ fpack.FPackNumber }}</div>
              <div class="robot-location">📍 {{ fpack.RobotLocationCode }}</div>
            </div>
            
            <div class="project-selectors">
              <select 
                v-model="fpack.selectedProjetGlobal"
                @change="onProjetGlobalChange(fpack)"
                class="form-select compact"
              >
                <option value="">Projet...</option>
                <option 
                  v-for="projet in projetsGlobaux" 
                  :key="projet.id"
                  :value="projet.id"
                >
                  {{ projet.projet }} - {{ projet.client }}
                </option>
              </select>
              
              <select 
                v-model="fpack.selectedSousProjet"
                :disabled="!fpack.selectedProjetGlobal"
                class="form-select compact"
              >
                <option value="">Sous-projet...</option>
                <option 
                  v-for="sousProjet in getAvailableSousProjets(fpack.selectedProjetGlobal)" 
                  :key="sousProjet.id"
                  :value="sousProjet.id"
                >
                  {{ sousProjet.nom }}
                </option>
              </select>
            </div>
          </div>
        </div>
      </div>
      
      <div class="step-actions">
        <button class="btn btn-secondary" @click="emit('previousStep')">
          ← Retour
        </button>
        <button 
          class="btn btn-primary"
          :disabled="!allFPacksHaveProject || !selectedClient"
          @click="emit('projectsAssigned')"
        >
          Configuration mapping →
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Conteneur principal avec animation */
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

/* En-tête d'étape */
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

/* Corps de l'étape */
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

/* Sélection client */
.client-selection {
  margin-bottom: 28px;
  max-width: 350px;
}

.form-label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  color: #34495e;
  font-size: 0.95rem;
}

.form-select {
  width: 100%;
  padding: 14px 16px;
  border: 2px solid #ecf0f1;
  border-radius: 10px;
  background: #ffffff;
  font-size: 0.95rem;
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

.form-select.compact {
  padding: 10px 14px;
  font-size: 0.85rem;
}

/* Aperçu des données */
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
  display: flex;
  align-items: center;
  gap: 10px;
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

.stat-badge:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
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

/* Attribution F-Packs */
.fpack-assignment {
  margin-bottom: 28px;
}

.fpack-assignment h4 {
  margin-bottom: 20px;
  color: #2c3e50;
  font-size: 1.15rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
}

.fpack-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.fpack-card {
  background: #ffffff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 3px 15px rgba(52, 73, 94, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid #ecf0f1;
  position: relative;
  overflow: hidden;
}

.fpack-card:hover {
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.12);
  transform: translateY(-2px);
  border-color: #3498db;
}

.fpack-info {
  margin-bottom: 16px;
  position: relative;
  z-index: 2;
}

.fpack-number {
  font-weight: 700;
  font-size: 1.1rem;
  color: #2c3e50;
  margin-bottom: 3px;
}

.robot-location {
  color: #7f8c8d;
  font-size: 0.95rem;
  font-weight: 500;
}

.project-selectors {
  display: flex;
  flex-direction: column;
  gap: 10px;
  position: relative;
  z-index: 2;
}

/* Actions */
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