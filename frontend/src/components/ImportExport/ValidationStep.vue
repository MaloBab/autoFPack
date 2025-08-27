<script setup lang="ts">
import { computed } from 'vue'

interface UnmatchedItem {
  id: string
  value: string
  column: string
  suggestions: any[]
  selectedMatch?: any
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

// Props
const props = defineProps<{
  step: number
  active: boolean
  visible: boolean
  unmatchedItems: UnmatchedItem[]
  fpackList: FpackItem[]
  uniqueProjectCount: number
  mappedColumnsCount: number
  canExecuteImport: boolean
  isImporting: boolean
}>()

// Emits
const emit = defineEmits<{
  executeImport: []
  previousStep: []
}>()

// Computed
const totalUnresolvedItems = computed(() => {
  return props.unmatchedItems.filter(item => !item.selectedMatch).length
})
</script>

<template>
  <div class="step-container" :class="{ active: active }">
    <div class="step-header">
      <div class="step-indicator">
        <div class="step-number">{{ step }}</div>
      </div>
      <div class="step-content-header">
        <h3>✅ Validation finale</h3>
        <p class="step-description">Vérifiez et corrigez les correspondances avant l'import</p>
      </div>
    </div>
    
    <div class="step-body" v-show="visible">
      <!-- Résolutions manuelles nécessaires -->
      <div v-if="unmatchedItems.length > 0" class="unmatched-section">
        <h4>⚠️ Correspondances à valider ({{ unmatchedItems.length }})</h4>
        <div class="unmatched-list">
          <div 
            v-for="item in unmatchedItems" 
            :key="item.id"
            class="unmatched-item"
            :class="{ resolved: item.selectedMatch }"
          >
            <div class="unmatched-info">
              <div class="unmatched-value">{{ item.value }}</div>
              <div class="unmatched-column">{{ item.column }}</div>
            </div>
            
            <div class="suggestions-dropdown">
              <select v-model="item.selectedMatch" class="form-select">
                <option value="">Sélectionner une correspondance</option>
                <option 
                  v-for="suggestion in item.suggestions" 
                  :key="suggestion.id"
                  :value="suggestion"
                >
                  {{ suggestion.nom }} ({{ suggestion.score }}% de correspondance)
                </option>
              </select>
            </div>
            
            <div class="match-status">
              <div v-if="item.selectedMatch" class="status-resolved">✅</div>
              <div v-else class="status-pending">⏳</div>
            </div>
          </div>
        </div>

        <div v-if="totalUnresolvedItems > 0" class="validation-warning">
          <div class="warning-icon">⚠️</div>
          <div class="warning-content">
            <strong>{{ totalUnresolvedItems }} correspondances non résolues</strong>
            <p>Vous devez résoudre toutes les correspondances avant de pouvoir continuer l'import.</p>
          </div>
        </div>
      </div>

      <div v-else class="no-unmatched">
        <div class="success-icon">🎉</div>
        <h4>Toutes les correspondances sont validées !</h4>
        <p>Aucune intervention manuelle requise. Vous pouvez procéder à l'import.</p>
      </div>

      <!-- Résumé de l'import -->
      <div class="import-summary">
        <h4>📊 Résumé de l'import</h4>
        <div class="summary-grid">
          <div class="summary-card">
            <div class="summary-icon">📦</div>
            <div class="summary-content">
              <div class="summary-value">{{ fpackList.length }}</div>
              <div class="summary-label">F-Packs à importer</div>
            </div>
          </div>
          <div class="summary-card">
            <div class="summary-icon">🏗️</div>
            <div class="summary-content">
              <div class="summary-value">{{ uniqueProjectCount }}</div>
              <div class="summary-label">Projets concernés</div>
            </div>
          </div>
          <div class="summary-card">
            <div class="summary-icon">🔗</div>
            <div class="summary-content">
              <div class="summary-value">{{ mappedColumnsCount }}</div>
              <div class="summary-label">Colonnes mappées</div>
            </div>
          </div>
          <div class="summary-card">
            <div class="summary-icon">⚠️</div>
            <div class="summary-content">
              <div class="summary-value">{{ unmatchedItems.length }}</div>
              <div class="summary-label">Validations</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Prévisualisation des F-Packs -->
      <div class="fpack-preview">
        <h4>👁️ Aperçu des F-Packs à importer</h4>
        <div class="preview-grid">
          <div 
            v-for="(fpack, index) in fpackList" 
            :key="index"
            class="preview-fpack"
          >
            <div class="fpack-number">{{ fpack.FPackNumber }}</div>
            <div class="fpack-location">📍 {{ fpack.RobotLocationCode }}</div>
          </div>
        </div>
      </div>
      
      <div class="step-actions">
        <button class="btn btn-secondary" @click="emit('previousStep')">
          ← Retour
        </button>
        <button 
          class="btn btn-success"
          :disabled="!canExecuteImport || isImporting"
          @click="emit('executeImport')"
        >
          <span v-if="!isImporting">🚀 Exécuter l'import</span>
          <span v-else>⏳ Import en cours...</span>
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

.step-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 28px;
  background: linear-gradient(135deg, #fcfcfc 0%, #f8f9fa 100%);
  border-bottom: 1px solid rgba(189, 195, 199, 0.15);
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

.unmatched-section {
  margin-bottom: 28px;
}

.unmatched-section h4 {
  color: #f39c12;
  margin-bottom: 16px;
  font-size: 1.15rem;
  font-weight: 700;
}

.unmatched-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.unmatched-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #ffffff;
  border-radius: 12px;
  border: 2px solid #f39c12;
  box-shadow: 0 4px 20px rgba(243, 156, 18, 0.12);
  transition: all 0.3s ease;
}

.unmatched-item.resolved {
  border-color: #27ae60;
  box-shadow: 0 4px 20px rgba(39, 174, 96, 0.12);
}

.unmatched-info {
  flex: 1;
}

.unmatched-value {
  font-weight: 600;
  color: #2c3e50;
  font-size: 1rem;
}

.unmatched-column {
  color: #7f8c8d;
  font-size: 0.9rem;
  margin-top: 3px;
}

.suggestions-dropdown {
  flex: 2;
}

.form-select {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #ecf0f1;
  border-radius: 8px;
  background: #ffffff;
  font-size: 0.9rem;
  color: #34495e;
  transition: all 0.3s ease;
}

.form-select:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.match-status {
  flex-shrink: 0;
}

.status-resolved {
  font-size: 1.2rem;
  color: #27ae60;
}

.status-pending {
  font-size: 1.2rem;
  color: #f39c12;
}

.validation-warning {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(243, 156, 18, 0.05), rgba(230, 126, 34, 0.05));
  border: 2px solid #f39c12;
  border-radius: 12px;
  margin-top: 16px;
}

.warning-icon {
  font-size: 1.5rem;
  color: #f39c12;
}

.warning-content strong {
  color: #e67e22;
  font-size: 1rem;
}

.warning-content p {
  margin: 5px 0 0 0;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.no-unmatched {
  text-align: center;
  padding: 40px;
  background: linear-gradient(135deg, rgba(39, 174, 96, 0.03), rgba(46, 204, 113, 0.03));
  border: 2px solid #27ae60;
  border-radius: 16px;
  margin-bottom: 28px;
}

.success-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}

.no-unmatched h4 {
  margin: 0 0 8px 0;
  color: #27ae60;
  font-size: 1.25rem;
  font-weight: 700;
}

.no-unmatched p {
  margin: 0;
  color: #7f8c8d;
}

.import-summary {
  margin-bottom: 28px;
}

.import-summary h4 {
  margin-bottom: 20px;
  color: #2c3e50;
  font-size: 1.15rem;
  font-weight: 700;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #ffffff;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(52, 73, 94, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid #ecf0f1;
}

.summary-card:hover {
  box-shadow: 0 8px 25px rgba(52, 73, 94, 0.1);
  transform: translateY(-2px);
}

.summary-icon {
  font-size: 2rem;
  opacity: 0.7;
}

.summary-content {
  flex: 1;
}

.summary-value {
  font-size: 1.6rem;
  font-weight: 800;
  color: #2c3e50;
  line-height: 1;
  margin-bottom: 3px;
}

.summary-label {
  color: #7f8c8d;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.fpack-preview {
  margin-bottom: 28px;
}

.fpack-preview h4 {
  margin-bottom: 20px;
  color: #2c3e50;
  font-size: 1.15rem;
  font-weight: 700;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.preview-fpack {
  background: #ffffff;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #ecf0f1;
  transition: all 0.3s ease;
}

.preview-fpack:hover {
  box-shadow: 0 4px 15px rgba(52, 73, 94, 0.06);
  transform: translateY(-1px);
}

.fpack-number {
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 4px;
}

.fpack-location {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.more-fpacks {
  background: linear-gradient(135deg, #fcfcfc 0%, #f8f9fa 100%);
  border: 2px dashed #bdc3c7;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.more-count {
  font-size: 1.5rem;
  font-weight: 700;
  color: #7f8c8d;
}

.more-text {
  font-size: 0.9rem;
  color: #95a5a6;
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
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
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

.btn-success {
  background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);
}

.btn-success:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(39, 174, 96, 0.4);
}
</style>