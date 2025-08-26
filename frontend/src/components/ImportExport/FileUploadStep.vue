<script setup lang="ts">
import { ref } from 'vue'
import StepContainer from '../ImportExport/StepContainer.vue'

const props = defineProps<{
  step: number
  active: boolean
  completed: boolean
  selectedFile: File | null
}>()

const emit = defineEmits<{
  fileAnalyzed: [data: any]
  addNotification: [event: { type: 'success' | 'warning' | 'error' | 'info', message: string }]
  'update:selectedFile': [file: File | null]
}>()

const isDragOver = ref(false)
const isAnalyzing = ref(false)
const fileInput = ref<HTMLInputElement>()

// Fonction pour valider le type de fichier
const isValidFileType = (file: File): boolean => {
  const validTypes = ['.xlsx', '.xls', '.xlsm']
  return validTypes.some(type => file.name.toLowerCase().endsWith(type))
}

// Fonction pour traiter la sélection de fichier
const processFile = (file: File) => {
  if (isValidFileType(file)) {
    emit('update:selectedFile', file)
    emit('addNotification', { 
      type: 'success', 
      message: `Fichier "${file.name}" sélectionné avec succès` 
    })
  } else {
    emit('addNotification', { 
      type: 'error', 
      message: 'Format de fichier non supporté. Utilisez .xlsx, .xls ou .xlsm' 
    })
  }
}

// Gestion du drag & drop
const handleDragEnter = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = true
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  // Nécessaire pour permettre le drop
}

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault()
  // Ne déclencher que si on sort vraiment de la zone (pas d'un enfant)
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const x = event.clientX
  const y = event.clientY
  
  if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
    isDragOver.value = false
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
  
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    processFile(files[0])
  }
}

// Gestion de la sélection via l'input
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  
  if (files && files.length > 0) {
    processFile(files[0])
  }
}

// Ouvrir le sélecteur de fichier
const openFileSelector = () => {
  if (fileInput.value) {
    fileInput.value.click()
  }
}

const removeFile = () => {
  emit('update:selectedFile', null)
  // Réinitialiser l'input file
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  emit('addNotification', { 
    type: 'info', 
    message: 'Fichier retiré' 
  })
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const analyzeFile = async () => {
  if (!props.selectedFile) return
  
  isAnalyzing.value = true
  try {
    const formData = new FormData()
    formData.append('file', props.selectedFile)
    
    const response = await fetch('http://localhost:8000/import/upload', {
      method: 'POST',
      body: formData
    })
    
    const result = await response.json()
    
    if (result.success) {
      emit('fileAnalyzed', result)
      emit('addNotification', { 
        type: 'success', 
        message: `Fichier analysé avec succès. ${result.preview.length} lignes détectées.` 
      })
    } else {
      emit('addNotification', { 
        type: 'error', 
        message: result.detail || 'Erreur lors de l\'analyse du fichier' 
      })
    }
  } catch (error) {
    emit('addNotification', { 
      type: 'error', 
      message: 'Erreur lors de l\'upload du fichier' 
    })
    console.error(error)
  } finally {
    isAnalyzing.value = false
  }
}
</script>

<template>
  <StepContainer
    :step="step"
    :active="active"
    :completed="completed"
    title="Sélection du fichier Excel"
    description="Glissez-déposez ou sélectionnez votre fichier F-Pack Matrix"
    icon="📁"
    :visible="step === 1"
  >
    <div 
      class="drop-zone"
      :class="{ 'dragover': isDragOver, 'has-file': selectedFile }"
      @drop="handleDrop"
      @dragenter="handleDragEnter"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @click="!selectedFile ? openFileSelector() : null"
    >
      <div v-if="!selectedFile" class="drop-zone-content">
        <div class="upload-icon">📊</div>
        <h4>Glissez-déposez votre fichier Excel</h4>
        <p class="drop-zone-subtitle">ou cliquez pour parcourir</p>
        <div class="supported-formats">
          <span class="format-badge">.xlsx</span>
          <span class="format-badge">.xlsm</span>
          <span class="format-badge">.xls</span>
        </div>
      </div>
      
      <div v-else class="file-selected">
        <div class="file-icon">✅</div>
        <div class="file-info">
          <h4 class="file-name">{{ selectedFile.name }}</h4>
          <p class="file-size">{{ formatFileSize(selectedFile.size) }}</p>
        </div>
        <button class="btn-remove" @click.stop="removeFile" title="Supprimer le fichier">
          ❌
        </button>
      </div>
    </div>
    
    <input 
      ref="fileInput"
      type="file"
      accept=".xlsx,.xls,.xlsm"
      @change="handleFileSelect"
      style="display: none"
    />
    
    <div class="step-actions">
      <button 
        class="btn btn-secondary"
        v-if="selectedFile"
        @click="openFileSelector"
        :disabled="isAnalyzing"
      >
        🔄 Changer de fichier
      </button>
      
      <button 
        class="btn btn-primary"
        :disabled="!selectedFile || isAnalyzing"
        @click="analyzeFile"
      >
        <span v-if="!isAnalyzing">🔍 Analyser le fichier</span>
        <span v-else>⏳ Analyse...</span>
      </button>
    </div>
  </StepContainer>
</template>

<style scoped>
.drop-zone {
  border: 2px dashed #bdc3c7;
  border-radius: 16px;
  padding: 40px 28px;
  text-align: center;
  cursor: pointer;
  background: linear-gradient(135deg, #fdfdfd 0%, #f8f9fa 100%);
  margin-bottom: 20px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.drop-zone:hover {
  border-color: #3498db;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.1);
}

.drop-zone.dragover {
  border-color: #9b59b6;
  background: linear-gradient(135deg, rgba(155, 89, 182, 0.1), rgba(231, 76, 60, 0.1));
  transform: translateY(-3px);
  box-shadow: 0 12px 30px rgba(155, 89, 182, 0.2);
}

.drop-zone.has-file {
  border-color: #27ae60;
  background: linear-gradient(135deg, rgba(39, 174, 96, 0.03), rgba(46, 204, 113, 0.03));
  box-shadow: 0 8px 25px rgba(39, 174, 96, 0.1);
  cursor: default;
}

.drop-zone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  position: relative;
  z-index: 2;
}

.upload-icon {
  font-size: 3.5rem;
  opacity: 0.7;
  transition: all 0.3s ease;
}

.drop-zone:hover .upload-icon {
  transform: scale(1.05);
  opacity: 1;
}

.drop-zone-content h4 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
}

.drop-zone-subtitle {
  margin: 0;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.supported-formats {
  display: flex;
  gap: 6px;
  margin-top: 6px;
}

.format-badge {
  background: linear-gradient(135deg, #3498db 0%, #9b59b6 100%);
  color: white;
  padding: 5px 14px;
  border-radius: 16px;
  font-size: 0.8rem;
  font-weight: 600;
  box-shadow: 0 3px 10px rgba(52, 152, 219, 0.25);
  transition: all 0.3s ease;
}

.format-badge:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
}

.file-selected {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #ffffff;
  padding: 18px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(39, 174, 96, 0.08);
  border: 2px solid #27ae60;
  animation: successPulse 0.5s ease-out;
  position: relative;
  overflow: hidden;
}

@keyframes successPulse {
  0% {
    transform: scale(0.98);
    opacity: 0.9;
  }
  50% {
    transform: scale(1.01);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.file-icon {
  font-size: 2rem;
  color: #27ae60;
  animation: bounce 0.5s ease-out;
}

@keyframes bounce {
  0%, 20%, 53%, 80%, 100% {
    transform: translate3d(0,0,0);
  }
  40%, 43% {
    transform: translate3d(0, -6px, 0);
  }
  70% {
    transform: translate3d(0, -3px, 0);
  }
  90% {
    transform: translate3d(0, -1px, 0);
  }
}

.file-info {
  flex: 1;
  text-align: left;
}

.file-name {
  margin: 0;
  font-weight: 600;
  color: #2c3e50;
  font-size: 1rem;
}

.file-size {
  margin: 3px 0 0 0;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.btn-remove {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.1rem;
  opacity: 0.6;
  transition: all 0.3s ease;
  padding: 6px;
  border-radius: 50%;
}

.btn-remove:hover {
  opacity: 1;
  background: rgba(231, 76, 60, 0.1);
  transform: scale(1.05) rotate(90deg);
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

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
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
  background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(149, 165, 166, 0.3);
}

.btn-secondary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(149, 165, 166, 0.4);
}
</style>