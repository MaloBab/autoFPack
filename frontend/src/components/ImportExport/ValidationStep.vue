<script setup lang="ts">
import { computed} from 'vue'

interface UnmatchedItem {
  id: string
  value: string
  column: string
  suggestions: any[]
  selectedMatch?: any
  type: 'subproject' | 'group'
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
  visible: boolean
  unmatchedItems: UnmatchedItem[]
  fpackList: FpackItem[]
  uniqueProjectCount: number
  mappedColumnsCount: number
  canExecuteImport: boolean
  isImporting: boolean
  mappingConfig: Record<string, any> 
}>()

const emit = defineEmits<{
  executeImport: [finalConfig: any]
  previousStep: []
  updateUnmatchedItem: [itemId: string, selectedMatch: any]
}>()

const totalUnresolvedItems = computed(() => {
  return props.unmatchedItems.filter(item => !item.selectedMatch).length
})

const finalMappingConfig = computed(() => {
  if (!props.mappingConfig) return null
  
  const finalConfig = JSON.parse(JSON.stringify(props.mappingConfig))
  
  props.unmatchedItems.forEach(item => {
    if (item.selectedMatch) {
      if (item.type === 'subproject') {
        if (!finalConfig.subproject_columns) {
          finalConfig.subproject_columns = {}
        }
        finalConfig.subproject_columns[item.column] = item.selectedMatch.nom
      } else if (item.type === 'group') {
        if (!finalConfig.groups) {
          finalConfig.groups = []
        }
        
        let existingGroup = finalConfig.groups.find((g: any) => g.group_name === item.selectedMatch.nom)
        if (!existingGroup) {
          existingGroup = {
            group_name: item.selectedMatch.nom,
            columns: []
          }
          finalConfig.groups.push(existingGroup)
        }
        
        if (!existingGroup.columns.includes(item.column)) {
          existingGroup.columns.push(item.column)
        }
      }
    }
  })
  
  return finalConfig
})

const mappingConfigSummary = computed(() => {
  if (!props.mappingConfig) return null
  
  return {
    name: props.mappingConfig.name || 'Configuration sans nom',
    originalSubprojectColumns: Object.keys(props.mappingConfig.subproject_columns || {}).length,
    originalGroups: (props.mappingConfig.groups || []).length,
    manuallyResolvedSubprojects: props.unmatchedItems.filter(item => 
      item.type === 'subproject' && item.selectedMatch
    ).length,
    manuallyResolvedGroups: props.unmatchedItems.filter(item => 
      item.type === 'group' && item.selectedMatch
    ).length
  }
})

const handleMatchSelection = (itemId: string, selectedMatch: any) => {
  emit('updateUnmatchedItem', itemId, selectedMatch)
}

const handleExecuteImport = () => {
  if (finalMappingConfig.value && props.canExecuteImport) {
    emit('executeImport', finalMappingConfig.value)
  }
}

const getMatchTypeLabel = (type: string) => {
  switch (type) {
    case 'subproject': return '🏗️ Sous-projet'
    case 'group': return '📦 Groupe'
    default: return '❓ Inconnu'
  }
}

const getMatchTypeColor = (type: string) => {
  switch (type) {
    case 'subproject': return 'type-subproject'
    case 'group': return 'type-group'
    default: return 'type-unknown'
  }
}
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
      <!-- Configuration utilisée -->
      <div v-if="mappingConfigSummary" class="config-summary">
        <h4>📋 Configuration de mapping utilisée</h4>
        <div class="config-info">
          <div class="config-name">{{ mappingConfigSummary.name }}</div>
          <div class="config-stats">
            <span class="config-stat">
              {{ mappingConfigSummary.originalSubprojectColumns }} colonnes sous-projet originales
            </span>
            <span class="config-stat">
              {{ mappingConfigSummary.originalGroups }} groupes originaux
            </span>
            <span v-if="mappingConfigSummary.manuallyResolvedSubprojects > 0" class="config-stat resolved">
              +{{ mappingConfigSummary.manuallyResolvedSubprojects }} sous-projets résolus manuellement
            </span>
            <span v-if="mappingConfigSummary.manuallyResolvedGroups > 0" class="config-stat resolved">
              +{{ mappingConfigSummary.manuallyResolvedGroups }} groupes résolus manuellement
            </span>
          </div>
        </div>
      </div>

      <!-- Correspondances à valider -->
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
              <div class="match-type" :class="getMatchTypeColor(item.type)">
                {{ getMatchTypeLabel(item.type) }}
              </div>
              <div class="unmatched-column">{{ item.column }}</div>
              <div class="unmatched-value">{{ item.value }}</div>
            </div>
            
            <div class="suggestions-dropdown">
              <select 
                :value="item.selectedMatch" 
                @change="handleMatchSelection(item.id, ($event.target as HTMLSelectElement).selectedOptions[0]?.value ? item.suggestions.find(s => s.id === ($event.target as HTMLSelectElement).value) : null)"
                class="form-select"
              >
                <option value="">Sélectionner une correspondance</option>
                <option 
                  v-for="suggestion in item.suggestions" 
                  :key="suggestion.id"
                  :value="suggestion.id"
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

      <!-- Aperçu de la configuration finale -->
      <div v-if="finalMappingConfig" class="final-config-preview">
        <h4>🔧 Configuration finale qui sera utilisée</h4>
        <div class="config-preview">
          <div class="preview-section">
            <h5>Colonnes Sous-projet ({{ Object.keys(finalMappingConfig.subproject_columns || {}).length }})</h5>
            <div class="columns-list">
              <span 
                v-for="(value, key) in finalMappingConfig.subproject_columns" 
                :key="key" 
                class="column-tag subproject"
              >
                {{ key }} → {{ value }}
              </span>
            </div>
          </div>
          
          <div v-if="finalMappingConfig.groups?.length > 0" class="preview-section">
            <h5>Groupes ({{ finalMappingConfig.groups.length }})</h5>
            <div class="groups-list">
              <div v-for="group in finalMappingConfig.groups" :key="group.group_name" class="group-item">
                <div class="group-name">{{ group.group_name }}</div>
                <div class="group-columns">
                  <span v-for="column in group.columns" :key="column" class="column-tag group">
                    {{ column }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
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
      
      <div class="step-actions">
        <button class="btn btn-secondary" @click="emit('previousStep')">
          ← Retour
        </button>
        <button 
          class="btn btn-success"
          :disabled="!canExecuteImport || isImporting || totalUnresolvedItems > 0"
          @click="handleExecuteImport"
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

.config-summary {
  margin-bottom: 28px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.02) 0%, rgba(155, 89, 182, 0.02) 100%);
  border: 1px solid rgba(52, 152, 219, 0.1);
  border-radius: 12px;
}

.config-summary h4 {
  margin: 0 0 16px 0;
  color: #2c3e50;
  font-size: 1.15rem;
  font-weight: 700;
}

.config-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: #2980b9;
  margin-bottom: 12px;
}

.config-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.config-stat {
  padding: 4px 8px;
  background: rgba(52, 152, 219, 0.1);
  border: 1px solid rgba(52, 152, 219, 0.2);
  border-radius: 6px;
  font-size: 0.85rem;
  color: #2980b9;
}

.config-stat.resolved {
  background: rgba(39, 174, 96, 0.1);
  border-color: rgba(39, 174, 96, 0.2);
  color: #27ae60;
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

.match-type {
  font-size: 0.8rem;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  margin-bottom: 4px;
  display: inline-block;
}

.type-subproject {
  background: rgba(52, 152, 219, 0.1);
  color: #2980b9;
  border: 1px solid rgba(52, 152, 219, 0.2);
}

.type-group {
  background: rgba(155, 89, 182, 0.1);
  color: #8e44ad;
  border: 1px solid rgba(155, 89, 182, 0.2);
}

.unmatched-column {
  font-weight: 600;
  color: #2c3e50;
  font-size: 1rem;
}

.unmatched-value {
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

.final-config-preview {
  margin-bottom: 28px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(39, 174, 96, 0.02) 0%, rgba(46, 204, 113, 0.02) 100%);
  border: 1px solid rgba(39, 174, 96, 0.15);
  border-radius: 12px;
}

.final-config-preview h4 {
  margin: 0 0 16px 0;
  color: #27ae60;
  font-size: 1.15rem;
  font-weight: 700;
}

.config-preview {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.preview-section h5 {
  margin: 0 0 12px 0;
  color: #2c3e50;
  font-size: 1rem;
  font-weight: 600;
}

.columns-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.groups-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.group-item {
  padding: 12px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 8px;
  border: 1px solid rgba(39, 174, 96, 0.1);
}

.group-name {
  font-weight: 600;
  color: #27ae60;
  margin-bottom: 8px;
}

.group-columns {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.column-tag {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  white-space: nowrap;
}

.column-tag.subproject {
  background: rgba(52, 152, 219, 0.1);
  border: 1px solid rgba(52, 152, 219, 0.2);
  color: #2980b9;
}

.column-tag.group {
  background: rgba(155, 89, 182, 0.1);
  border: 1px solid rgba(155, 89, 182, 0.2);
  color: #8e44ad;
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