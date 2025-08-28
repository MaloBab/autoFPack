<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  step: number
  active: boolean
  completed: boolean
  visible: boolean
  mappingConfig: Record<string, any>
  previewColumns: string[]
  mappedColumnsCount: number
  uniqueProjectCount: number
}>()

const emit = defineEmits<{
  mappingConfigured: [config: {
    jsonConfig: any,
    fileName: string,
    fileSize: number
  }]
  previousStep: []
}>()

const selectedFile = ref<File | null>(null)
const jsonContent = ref<any>(null)
const fileInputRef = ref<HTMLInputElement>()
const isLoading = ref(false)
const error = ref<string>('')
const isDragOver = ref(false)

const canProceed = computed(() => {
  return selectedFile.value && jsonContent.value && !error.value
})

const jsonInfo = computed(() => {
  if (!jsonContent.value) return null
  
  const info = {
    subprojectColumns: 0,
    groups: 0,
    totalMappings: 0,
    name: null as string | null,
    subprojectColumnsList: [] as string[],
    groupsList: [] as string[]
  }
  
  if (jsonContent.value.subproject_columns) {
    info.subprojectColumns = Object.keys(jsonContent.value.subproject_columns).length
    info.subprojectColumnsList = Object.keys(jsonContent.value.subproject_columns)
  }
  
  if (jsonContent.value.groups && Array.isArray(jsonContent.value.groups)) {
    info.groups = jsonContent.value.groups.length
    info.groupsList = jsonContent.value.groups.map((group: any) => group.group_name || 'Groupe sans nom')
  }
  
  info.totalMappings = info.subprojectColumns + info.groups
  info.name = jsonContent.value.name || null
  
  return info
})

const processFile = async (file: File) => {
  if (!file.name.toLowerCase().endsWith('.json')) {
    error.value = 'Veuillez sélectionner un fichier JSON valide'
    return
  }
  
  selectedFile.value = file
  isLoading.value = true
  error.value = ''
  
  try {
    const text = await file.text()
    const parsed = JSON.parse(text)
    
    if (!parsed.subproject_columns && !parsed.groups) {
      error.value = 'Le fichier JSON doit contenir au moins "subproject_columns" ou "groups"'
      selectedFile.value = null
      jsonContent.value = null
      return
    }
    
    jsonContent.value = parsed
  } catch (e) {
    error.value = 'Erreur lors de la lecture du fichier JSON. Vérifiez que le fichier est valide.'
    selectedFile.value = null
    jsonContent.value = null
  } finally {
    isLoading.value = false
  }
}

const triggerFileSelect = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return
  
  await processFile(file)
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
}

const handleDrop = async (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
  
  const files = event.dataTransfer?.files
  if (!files || files.length === 0) return
  
  const file = files[0]
  await processFile(file)
}

const removeFile = () => {
  selectedFile.value = null
  jsonContent.value = null
  error.value = ''
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const handleNext = () => {
  if (canProceed.value && selectedFile.value) {
    emit('mappingConfigured', {
      jsonConfig: jsonContent.value,
      fileName: selectedFile.value.name,
      fileSize: selectedFile.value.size
    })

  }
}
</script>

<template>
  <div class="step-container" :class="{ active, completed }">
    <div class="step-header">
      <div class="step-indicator">
        <div class="step-number">{{ props.step }}</div>
        <div class="step-line"></div>
      </div>
      <div class="step-content-header">
        <h3>🔗 Configuration du mapping</h3>
        <p class="step-description">Sélectionnez le fichier JSON de configuration du mapping F-Pack Matrix</p>
      </div>
    </div>
    
    <div class="step-body" v-show="props.visible">
      <div class="file-selection-section">
        <h4 class="section-title">📁 Fichier de configuration JSON</h4>
        
        <div class="file-input-area" :class="{ 'has-file': selectedFile, 'has-error': error }">
          <input 
            ref="fileInputRef"
            type="file" 
            accept=".json"
            @change="handleFileSelect"
            class="hidden-file-input"
          />
          
          <div 
            v-if="!selectedFile" 
            class="file-drop-zone" 
            :class="{ 'drag-over': isDragOver }"
            @click="triggerFileSelect"
            @dragover="handleDragOver"
            @dragleave="handleDragLeave"
            @drop="handleDrop"
          >
            <div class="file-drop-icon">📄</div>
            <p class="file-drop-text">
              {{ isDragOver ? 'Déposez votre fichier JSON ici' : 'Cliquez ou glissez-déposez votre fichier JSON' }}
            </p>
            <p class="file-drop-hint">Format supporté: .json</p>
          </div>
          
          <div v-else class="selected-file-info">
            <div class="file-icon">✅</div>
            <div class="file-details">
              <div class="file-name">{{ selectedFile.name }}</div>
              <div class="file-size">{{ Math.round(selectedFile.size / 1024) }} KB</div>
            </div>
            <button class="remove-file-btn" @click="removeFile" title="Supprimer le fichier">
              ✕
            </button>
          </div>
        </div>
        
        <div v-if="error" class="error-message">
          ⚠️ {{ error }}
        </div>
        
        <div v-if="isLoading" class="loading-message">
          <div class="loading-spinner"></div>
          Chargement du fichier...
        </div>
      </div>
      <div v-if="jsonInfo" class="json-info-section">
        <h4 class="section-title">ℹ️ Informations du fichier de mapping</h4>
        
        <div class="json-stats">
          <div class="stat-card">
            <div class="stat-value">{{ jsonInfo.totalMappings }}</div>
            <div class="stat-label">Total mappings</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ jsonInfo.subprojectColumns }}</div>
            <div class="stat-label">Colonnes Sous-Projet</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ jsonInfo.groups }}</div>
            <div class="stat-label">Groupes définis</div>
          </div>
        </div>
        
        <div class="json-details">
          <div v-if="jsonInfo.name" class="metadata-item">
            <span class="metadata-label">Configuration:</span>
            <span class="metadata-value">{{ jsonInfo.name }}</span>
          </div>
          
          <div v-if="jsonInfo.subprojectColumnsList.length > 0" class="mapping-preview">
            <h5>🔧 Colonnes Sous-projet configurées</h5>
            <div class="columns-list">
              <span v-for="column in jsonInfo.subprojectColumnsList" :key="column" class="column-tag subproject">
                {{ column }}
              </span>
            </div>
          </div>
          
          <div v-if="jsonInfo.groupsList.length > 0" class="mapping-preview">
            <h5>📦 Groupes configurés</h5>
            <div class="columns-list">
              <span v-for="group in jsonInfo.groupsList" :key="group" class="column-tag group">
                {{ group }}
              </span>
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
          :disabled="!canProceed"
          @click="handleNext"
        >
          👁️ Prévisualiser l'import
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

.file-selection-section {
  margin-bottom: 28px;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
}

.file-input-area {
  margin-bottom: 12px;
}

.hidden-file-input {
  display: none;
}

.file-drop-zone {
  border: 2px dashed #bdc3c7;
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: #fafbfc;
  position: relative;
}

.file-drop-zone:hover {
  border-color: #3498db;
  background: #f0f8ff;
  transform: translateY(-2px);
}

.file-drop-zone.drag-over {
  border-color: #27ae60;
  background: #f0fff4;
  transform: scale(1.02);
  box-shadow: 0 8px 25px rgba(39, 174, 96, 0.15);
}

.file-drop-zone.drag-over .file-drop-icon {
  transform: scale(1.1);
  filter: drop-shadow(0 4px 8px rgba(39, 174, 96, 0.3));
}

.file-drop-zone.drag-over .file-drop-text {
  color: #27ae60;
}

.file-drop-icon {
  font-size: 3rem;
  margin-bottom: 12px;
  transition: all 0.3s ease;
}

.file-drop-text {
  margin: 0 0 8px 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #34495e;
}

.file-drop-hint {
  margin: 0;
  font-size: 0.9rem;
  color: #7f8c8d;
}

.selected-file-info {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(46, 204, 113, 0.05) 0%, rgba(39, 174, 96, 0.05) 100%);
  border: 1px solid rgba(46, 204, 113, 0.2);
  border-radius: 12px;
}

.file-icon {
  font-size: 1.5rem;
}

.file-details {
  flex: 1;
}

.file-name {
  font-weight: 600;
  color: #27ae60;
  margin-bottom: 4px;
}

.file-size {
  font-size: 0.9rem;
  color: #7f8c8d;
}

.remove-file-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(231, 76, 60, 0.1);
  color: #e74c3c;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
}

.remove-file-btn:hover {
  background: rgba(231, 76, 60, 0.2);
  transform: scale(1.1);
}

.error-message {
  padding: 12px 16px;
  background: rgba(231, 76, 60, 0.1);
  border: 1px solid rgba(231, 76, 60, 0.2);
  border-radius: 8px;
  color: #c0392b;
  font-weight: 500;
}

.loading-message {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(52, 152, 219, 0.1);
  border: 1px solid rgba(52, 152, 219, 0.2);
  border-radius: 8px;
  color: #2980b9;
  font-weight: 500;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(52, 152, 219, 0.3);
  border-top: 2px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.json-info-section {
  margin-bottom: 28px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.02) 0%, rgba(155, 89, 182, 0.02) 100%);
  border: 1px solid rgba(52, 152, 219, 0.1);
  border-radius: 12px;
}

.json-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.json-details {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.metadata-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 8px;
  border: 1px solid rgba(52, 152, 219, 0.1);
}

.metadata-label {
  font-weight: 600;
  color: #34495e;
  min-width: 100px;
}

.metadata-value {
  color: #2980b9;
  font-weight: 500;
}

.mapping-preview {
  padding: 16px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 8px;
  border: 1px solid rgba(52, 152, 219, 0.1);
}

.mapping-preview h5 {
  margin: 0 0 12px 0;
  font-size: 1rem;
  font-weight: 600;
  color: #2c3e50;
}

.columns-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.column-tag {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.column-tag.subproject {
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.1) 0%, rgba(155, 89, 182, 0.1) 100%);
  border: 1px solid rgba(52, 152, 219, 0.2);
  color: #2980b9;
}

.column-tag.group {
  background: linear-gradient(135deg, rgba(46, 204, 113, 0.1) 0%, rgba(39, 174, 96, 0.1) 100%);
  border: 1px solid rgba(46, 204, 113, 0.2);
  color: #27ae60;
}

.column-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-card {
  background: #ffffff;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 4px 20px rgba(52, 73, 94, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  border: 1px solid #ecf0f1;
}

.stat-card::before {
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

.stat-card:hover {
  box-shadow: 0 8px 25px rgba(52, 73, 94, 0.1);
  transform: translateY(-3px);
}

.stat-card:hover::before {
  transform: scaleX(1);
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #3498db 0%, #9b59b6 50%, #e74c3c 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 6px;
  line-height: 1.1;
}

.stat-label {
  font-size: 1rem;
  color: #7f8c8d;
  font-weight: 600;
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
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
}

.btn-primary {
  background: linear-gradient(135deg, #3498db 0%, #9b59b6 100%);
  color: white;
  box-shadow: 0 6px 20px rgba(52, 152, 219, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
}

.btn-secondary {
  background: #ecf0f1;
  color: #34495e;
}

.btn-secondary:hover {
  background: #d0d7de;
  transform: translateY(-1px);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}
</style>