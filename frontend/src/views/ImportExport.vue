<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'

// Types
interface Client {
  id: number
  nom: string
}

interface Project {
  id: number
  projet: string
  client_nom: string
  nb_sous_projets: number
  nb_selections: number
}

interface UnmatchedItem {
  id: string
  value: string
  column: string
  suggestions: Array<{id: number, nom: string, type: string}>
  selectedMatch?: any
}

interface MappingRule {
  target: string
  groupe_nom?: string
  type?: 'exact_match' | 'fuzzy_match'
  search_in?: string[]
  search_fields?: string[]
}

interface MappingConfig {
  excel_columns: Record<string, MappingRule>
}

// État réactif
const activeTab = ref<'import' | 'export'>('import')
const importStep = ref<'upload' | 'preview' | 'confirm'>('upload')

// Import
const selectedFile = ref<File | null>(null)
const selectedClient = ref<number | null>(null)
const clients = ref<Client[]>([])
const excelColumns = ref<string[]>([])
const previewData = ref<any[]>([])
const unmatchedItems = ref<UnmatchedItem[]>([])
const mappingConfig = ref<MappingConfig>({ excel_columns: {} })
const showMappingEditor = ref(false)
const isDragOver = ref(false)
const uploadError = ref('')
const isUploading = ref(false)

// Progress & Results
const importProgress = ref(0)
const importInProgress = ref(false)
const importCompleted = ref(false)
const importSuccess = ref(false)
const importError = ref('')
const currentImportStep = ref('')
const importResults = ref({ created_projects: 0, created_selections: 0 })

const summaryData = reactive({
  nb_projets: 0,
  nb_sous_projets: 0,
  nb_selections: 0
})

// Export
const availableProjects = ref<Project[]>([])
const selectedProjects = ref<number[]>([])
const projectSearchTerm = ref('')
const exportOptions = reactive({
  includeSelections: true,
  includeEmptyRows: false,
  groupByClient: false
})
const exportFormat = ref('excel')
const isExporting = ref(false)

// Computed
const validationStats = computed(() => {
  const stats = { success: 0, warning: 0, error: 0 }
  previewData.value.forEach(row => {
    stats[row._status as keyof typeof stats]++
  })
  return stats
})

const hasUnmatchedItems = computed(() => {
  return unmatchedItems.value.some(item => !item.selectedMatch)
})

const filteredProjects = computed(() => {
  if (!projectSearchTerm.value) return availableProjects.value
  
  return availableProjects.value.filter(project => 
    project.projet.toLowerCase().includes(projectSearchTerm.value.toLowerCase()) ||
    project.client_nom.toLowerCase().includes(projectSearchTerm.value.toLowerCase())
  )
})

// Méthodes
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files?.[0]) {
    selectedFile.value = target.files[0]
    uploadError.value = ''
  }
}

const handleFileDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
  
  if (event.dataTransfer?.files[0]) {
    selectedFile.value = event.dataTransfer.files[0]
    uploadError.value = ''
  }
}

const uploadFile = async () => {
  if (!selectedFile.value || !selectedClient.value) return
  
  isUploading.value = true
  uploadError.value = ''
  
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('client_id', selectedClient.value.toString())
  
  try {
    const response = await axios.post('http://localhost:8000/import/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    excelColumns.value = response.data.columns
    console.log('Colonnes détectées:', excelColumns.value)
    previewData.value = response.data.preview
    importStep.value = 'preview'
    
    await loadMappingConfig()
    await generatePreview()
    
  } catch (error: any) {
    uploadError.value = error.response?.data?.detail || 'Erreur lors de l\'analyse du fichier'
    console.error('Erreur upload:', error)
  } finally {
    isUploading.value = false
  }
}

const generatePreview = async () => {
  try {
    const response = await axios.post('http://localhost:8000/projets/import/preview', {
      preview_data: previewData.value,
      mapping_config: mappingConfig.value,
      client_id: selectedClient.value
    })
    
    previewData.value = response.data.processed_data
    unmatchedItems.value = response.data.unmatched_items
    
    summaryData.nb_projets = response.data.summary.nb_projets || 0
    summaryData.nb_sous_projets = response.data.summary.nb_sous_projets || 0
    summaryData.nb_selections = response.data.summary.nb_selections || 0
  } catch (error) {
    console.error('Erreur preview:', error)
  }
}

const executeImport = async () => {
  importStep.value = 'confirm'
  importInProgress.value = true
  importProgress.value = 0
  importCompleted.value = false
  importSuccess.value = false
  currentImportStep.value = 'Préparation...'
  
  try {
    const response = await axios.post('http://localhost:8000/projets/import/execute', {
      file_data: previewData.value,
      mapping_config: mappingConfig.value,
      client_id: selectedClient.value,
      manual_matches: unmatchedItems.value.filter(item => item.selectedMatch)
    })
    
    // Simulation de progression
    const steps = [
      'Création des projets...',
      'Import des sous-projets...',
      'Traitement des sélections...',
      'Finalisation...'
    ]
    
    let stepIndex = 0
    const interval = setInterval(() => {
      importProgress.value += 25
      if (stepIndex < steps.length) {
        currentImportStep.value = steps[stepIndex]
        stepIndex++
      }
      
      if (importProgress.value >= 100) {
        clearInterval(interval)
        importInProgress.value = false
        importCompleted.value = true
        importSuccess.value = true
        importResults.value = response.data.results || { created_projects: 0, created_selections: 0 }
      }
    }, 800)
    
  } catch (error: any) {
    importInProgress.value = false
    importCompleted.value = true
    importSuccess.value = false
    importError.value = error.response?.data?.detail || 'Erreur lors de l\'import'
    console.error('Erreur import:', error)
  }
}

const exportProjects = async () => {
  if (selectedProjects.value.length === 0) return
  
  isExporting.value = true
  
  try {
    const response = await axios.post('http://localhost:8000/projets/export/batch', {
      project_ids: selectedProjects.value,
      options: exportOptions,
      format: exportFormat.value
    }, {
      responseType: 'blob'
    })
    
    // Télécharger le fichier
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `export_projets_${new Date().toISOString().split('T')[0]}.${exportFormat.value === 'excel' ? 'xlsx' : 'csv'}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    
    // Reset sélection après export
    selectedProjects.value = []
  } catch (error) {
    console.error('Erreur export:', error)
  } finally {
    isExporting.value = false
  }
}

const loadMappingConfig = async () => {
  try {
    const response = await axios.get('http://localhost:8000/projets/import/mapping-config')
    mappingConfig.value = response.data
  } catch (error) {
    // Utiliser config par défaut si pas trouvée
    mappingConfig.value = {
      excel_columns: excelColumns.value.reduce((acc, col) => {
        acc[col] = { target: 'ignore' }
        return acc
      }, {} as Record<string, MappingRule>)
    }
  }
}

const saveMappingConfig = async () => {
  try {
    await axios.put('http://localhost:8000/projets/import/mapping-config', mappingConfig.value)
    showMappingEditor.value = false
    await generatePreview() // Régénérer avec nouvelle config
  } catch (error) {
    console.error('Erreur sauvegarde mapping:', error)
  }
}

const resetMappingConfig = () => {
  mappingConfig.value = {
    excel_columns: excelColumns.value.reduce((acc, col) => {
      acc[col] = { target: 'ignore' }
      return acc
    }, {} as Record<string, MappingRule>)
  }
}

const closeMappingEditor = () => {
  showMappingEditor.value = false
}

const updateMappingRule = (rule: MappingRule) => {
  if (rule.target !== 'selection') {
    delete rule.groupe_nom
    delete rule.type
  }
}

const toggleSelectAll = (event: Event) => {
  const checked = (event.target as HTMLInputElement).checked
  if (checked) {
    selectedProjects.value = filteredProjects.value.map(p => p.id)
  } else {
    selectedProjects.value = []
  }
}

const resetImport = () => {
  importStep.value = 'upload'
  selectedFile.value = null
  previewData.value = []
  unmatchedItems.value = []
  importProgress.value = 0
  importCompleted.value = false
  importSuccess.value = false
  uploadError.value = ''
}

const getStatusLabel = (status: string): string => {
  switch (status) {
    case 'success': return '✓ Valide'
    case 'warning': return '⚠ Attention'
    case 'error': return '✗ Erreur'
    default: return status
  }
}

// Lifecycle
onMounted(async () => {
  try {
    // Charger les clients
    const clientsResponse = await axios.get('http://localhost:8000/clients')
    clients.value = clientsResponse.data
    
    // Charger les projets pour export
    const projectsResponse = await axios.get('http://localhost:8000/projets_globaux')
    availableProjects.value = projectsResponse.data
  } catch (error) {
    console.error('Erreur chargement initial:', error)
  }
})
</script>

<template>
  <div class="import-export-container">
    <!-- Header avec onglets Import/Export -->
    <div class="tabs-header">
      <button @click="activeTab = 'import'" :class="{active: activeTab === 'import'}">Import</button>
      <button @click="activeTab = 'export'" :class="{active: activeTab === 'export'}">Export</button>
    </div>

    <!-- Section Import -->
    <div v-if="activeTab === 'import'" class="import-section">
      <!-- Étape 1: Upload du fichier -->
      <div class="step-container" v-if="importStep === 'upload'">
        <h2>Étape 1 : Sélection du fichier</h2>
        <div class="file-drop-zone" 
             @dragover.prevent 
             @dragenter.prevent
             @drop="handleFileDrop"
             :class="{ 'dragover': isDragOver }"
             @dragenter="isDragOver = true"
             @dragleave="isDragOver = false">
          <input type="file" 
                 ref="fileInput"
                 @change="handleFileSelect" 
                 accept=".xlsx,.xls"
                 style="display: none" />
          <div class="upload-icon">📁</div>
          <p v-if="!selectedFile">Glissez votre fichier Excel ici</p>
          <p v-else class="file-selected">✅ {{ selectedFile.name }}</p>
        </div>
        
        <div class="client-selector">
          <label for="client-select">Client :</label>
          <select id="client-select" v-model="selectedClient" required>
            <option value="">Sélectionnez un client</option>
            <option v-for="client in clients" :key="client.id" :value="client.id">
              {{ client.nom }}
            </option>
          </select>
        </div>

        <div class="error-message" v-if="uploadError">
          {{ uploadError }}
        </div>
      </div>

      <!-- Étape 2: Prévisualisation et mapping -->
      <div class="step-container" v-if="importStep === 'preview'">
        <h2>Étape 2 : Vérification et mapping</h2>
        
        <div class="mapping-config">
          <h3>Configuration du mapping</h3>
          <button @click="showMappingEditor = true" class="btn btn-secondary">
            ⚙️ Éditer le mapping
          </button>
          <span class="mapping-status">
            {{ Object.keys(mappingConfig.excel_columns || {}).length }} colonnes mappées
          </span>
        </div>
        
        <div class="preview-table-container">
          <h3>Aperçu des données ({{ previewData.length }} lignes)</h3>
          <div class="table-scroll">
            <table class="data-preview">
              <thead>
                <tr>
                  <th v-for="col in excelColumns" :key="col">{{ col }}</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, index) in previewData.slice(0, 10)" :key="index" :class="'status-' + row._status">
                  <td v-for="col in excelColumns" :key="col">{{ row[col] || '-' }}</td>
                  <td>
                    <span class="status-badge" :class="row._status">{{ getStatusLabel(row._status) }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-if="previewData.length > 10" class="preview-note">
            Seules les 10 premières lignes sont affichées. Total : {{ previewData.length }} lignes
          </p>
        </div>

        <div class="unmatched-items" v-if="unmatchedItems.length > 0">
          <h3>⚠️ Éléments nécessitant une correspondance manuelle ({{ unmatchedItems.length }})</h3>
          <div class="unmatched-list">
            <div v-for="item in unmatchedItems" :key="item.id" class="unmatched-item">
              <div class="unmatched-info">
                <strong>{{ item.value }}</strong>
                <span class="unmatched-column">dans {{ item.column }}</span>
              </div>
              <select v-model="item.selectedMatch" class="match-selector">
                <option value="">Choisir une correspondance</option>
                <option v-for="suggestion in item.suggestions" :key="suggestion.id" :value="suggestion">
                  {{ suggestion.nom }} ({{ suggestion.type }})
                </option>
              </select>
            </div>
          </div>
        </div>

        <div class="validation-summary">
          <div class="validation-stats">
            <div class="stat success">
              <span class="stat-number">{{ validationStats.success }}</span>
              <span class="stat-label">Valides</span>
            </div>
            <div class="stat warning">
              <span class="stat-number">{{ validationStats.warning }}</span>
              <span class="stat-label">Avertissements</span>
            </div>
            <div class="stat error">
              <span class="stat-number">{{ validationStats.error }}</span>
              <span class="stat-label">Erreurs</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Étape 3: Confirmation et import -->
      <div class="step-container" v-if="importStep === 'confirm'">
        <h2>Étape 3 : Import en cours</h2>
        
        <div class="import-summary">
          <h3>Résumé de l'import</h3>
          <div class="summary-grid">
            <div class="summary-item">
              <span class="summary-number">{{ summaryData.nb_projets }}</span>
              <span class="summary-label">projets à créer</span>
            </div>
            <div class="summary-item">
              <span class="summary-number">{{ summaryData.nb_sous_projets }}</span>
              <span class="summary-label">sous-projets</span>
            </div>
            <div class="summary-item">
              <span class="summary-number">{{ summaryData.nb_selections }}</span>
              <span class="summary-label">sélections</span>
            </div>
          </div>
        </div>
        
        <div class="progress-container" v-if="importInProgress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{width: importProgress + '%'}"></div>
          </div>
          <p class="progress-text">{{ importProgress }}% - {{ currentImportStep }}</p>
        </div>

        <div class="import-results" v-if="importCompleted">
          <div class="alert alert-success" v-if="importSuccess">
            ✅ Import terminé avec succès !
            <ul>
              <li>{{ importResults.created_projects }} projets créés</li>
              <li>{{ importResults.created_selections }} sélections importées</li>
            </ul>
          </div>
          <div class="alert alert-error" v-else>
            ❌ Erreur lors de l'import : {{ importError }}
          </div>
        </div>
      </div>
    </div>

    <!-- Section Export -->
    <div v-if="activeTab === 'export'" class="export-section">
      <h2>Export de projets</h2>
      
      <div class="project-selector">
        <h3>Sélectionner les projets à exporter</h3>
        <div class="project-search">
          <input type="text" 
                 v-model="projectSearchTerm" 
                 placeholder="Rechercher un projet..."
                 class="search-input">
        </div>
        
        <div class="project-list">
          <div class="select-all-container">
            <label class="checkbox-label">
              <input type="checkbox" 
                     :checked="selectedProjects.length === filteredProjects.length && filteredProjects.length > 0"
                     :indeterminate="selectedProjects.length > 0 && selectedProjects.length < filteredProjects.length"
                     @change="toggleSelectAll">
              Sélectionner tout ({{ selectedProjects.length }}/{{ filteredProjects.length }})
            </label>
          </div>
          
          <div class="project-items">
            <div v-for="project in filteredProjects" :key="project.id" class="project-item">
              <label class="checkbox-label">
                <input type="checkbox" 
                       :id="'proj-' + project.id" 
                       v-model="selectedProjects" 
                       :value="project.id">
                <div class="project-info">
                  <div class="project-name">{{ project.projet }}</div>
                  <div class="project-details">
                    Client: {{ project.client_nom }} | 
                    {{ project.nb_sous_projets }} sous-projets |
                    {{ project.nb_selections }} sélections
                  </div>
                </div>
              </label>
            </div>
          </div>
        </div>
      </div>
      
      <div class="export-options">
        <h3>Options d'export</h3>
        <div class="options-grid">
          <label class="checkbox-label">
            <input type="checkbox" v-model="exportOptions.includeSelections">
            Inclure les sélections d'éléments
          </label>
          <label class="checkbox-label">
            <input type="checkbox" v-model="exportOptions.includeEmptyRows">
            Inclure les lignes vides pour template
          </label>
          <label class="checkbox-label">
            <input type="checkbox" v-model="exportOptions.groupByClient">
            Grouper par client
          </label>
        </div>
      </div>>
    </div>

    <!-- Modal d'édition du mapping -->
    <div v-if="showMappingEditor" class="modal-overlay" @click="closeMappingEditor">
      <div class="mapping-editor-modal" @click.stop>
        <div class="modal-header">
          <h3>Configuration du mapping des colonnes</h3>
          <button @click="closeMappingEditor" class="close-btn">✕</button>
        </div>
        
        <div class="mapping-rules">
          <div class="mapping-header">
            <div class="col-header">Colonne Excel</div>
            <div class="col-header">Cible</div>
            <div class="col-header">Options</div>
          </div>
          
          <div v-for="(rule, column) in mappingConfig.excel_columns" :key="column" class="mapping-rule">
            <div class="column-name">{{ column }}</div>
            <select v-model="rule.target" @change="updateMappingRule(rule)" class="mapping-select">
              <option value="ignore">Ignorer</option>
              <option value="sous_projet_fpack.FPack_number">FPack Number</option>
              <option value="sous_projet_fpack.Robot_Location_Code">Robot Location Code</option>
              <option value="sous_projet_fpack.contractor">Contractor</option>
              <option value="sous_projet_fpack.delivery_site">Delivery Site</option>
              <option value="selection">Sélection de groupe</option>
            </select>
            <div class="mapping-options">
              <input v-if="rule.target === 'selection'" 
                     v-model="rule.groupe_nom" 
                     placeholder="Nom du groupe"
                     class="group-input">
              <select v-if="rule.target === 'selection'" 
                      v-model="rule.type" 
                      class="match-type-select">
                <option value="exact_match">Correspondance exacte</option>
                <option value="fuzzy_match">Correspondance approximative</option>
              </select>
            </div>
          </div>
        </div>
        
        <div class="modal-actions">
          <button @click="saveMappingConfig" class="btn btn-primary">💾 Sauvegarder</button>
          <button @click="resetMappingConfig" class="btn btn-secondary">🔄 Réinitialiser</button>
          <button @click="closeMappingEditor" class="btn btn-secondary">Annuler</button>
        </div>
      </div>
    </div>

    <!-- Actions en bas -->
    <div class="action-buttons">
      <div class="button-group">
        <!-- Boutons Import -->
        <template v-if="activeTab === 'import'">
          <button v-if="importStep === 'upload'" 
                  @click="uploadFile" 
                  :disabled="!selectedFile || !selectedClient || isUploading"
                  class="btn btn-primary">
            {{ isUploading ? '📤 Analyse...' : '📤 Analyser le fichier' }}
          </button>
          
          <template v-if="importStep === 'preview'">
            <button @click="importStep = 'upload'" class="btn btn-secondary">
              ← Retour
            </button>
            <button @click="executeImport" 
                    :disabled="hasUnmatchedItems || validationStats.error > 0"
                    class="btn btn-primary">
              🚀 Lancer l'import
            </button>
          </template>
          
          <button v-if="importStep === 'confirm' && importCompleted" 
                  @click="resetImport" 
                  class="btn btn-primary">
            🔄 Nouvel import
          </button>
        </template>
        
        <!-- Boutons Export -->
        <button v-if="activeTab === 'export'" 
                @click="exportProjects" 
                :disabled="selectedProjects.length === 0 || isExporting"
                class="btn btn-primary">
          {{ isExporting ? '📥 Export...' : `📥 Exporter ${selectedProjects.length} projet(s)` }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.import-export-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Tabs */
.tabs-header {
  display: flex;
  border-bottom: 2px solid #e0e0e0;
  margin-bottom: 30px;
}

.tabs-header button {
  padding: 12px 24px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.3s ease;
  border-radius: 8px 8px 0 0;
}

.tabs-header button:hover {
  background-color: #f8f9fa;
}

.tabs-header button.active {
  background: #007bff;
  color: white;
  box-shadow: 0 -2px 0 #007bff;
}

/* Steps */
.step-container {
  background: white;
  border-radius: 12px;
  padding: 30px;
  margin-bottom: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.step-container h2 {
  margin-top: 0;
  color: #333;
  font-size: 24px;
  margin-bottom: 20px;
}

/* File Upload */
.file-drop-zone {
  border: 2px dashed #007bff;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  margin-bottom: 20px;
  transition: all 0.3s ease;
  background: #f8f9ff;
}

.file-drop-zone:hover,
.file-drop-zone.dragover {
  background-color: #e3f2fd;
  border-color: #0056b3;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.file-drop-zone p {
  margin: 0;
  color: #666;
  font-size: 16px;
}

.file-selected {
  color: #28a745 !important;
  font-weight: 500;
}

.link-button {
  background: none;
  border: none;
  color: #007bff;
  text-decoration: underline;
  cursor: pointer;
  font-size: inherit;
}

/* Form Elements */
.client-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.client-selector label {
  font-weight: 500;
  color: #333;
}

.client-selector select {
  flex: 1;
  max-width: 300px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

/* Preview Table */
.preview-table-container {
  margin: 20px 0;
}

.table-scroll {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.data-preview {
  width: 100%;
  border-collapse: collapse;
  min-width: 600px;
}

.data-preview th {
  background: #f8f9fa;
  padding: 12px 8px;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid #e0e0e0;
  position: sticky;
  top: 0;
}

.data-preview td {
  padding: 8px;
  border-bottom: 1px solid #e0e0e0;
}

.data-preview tr:hover {
  background-color: #f8f9fa;
}

.data-preview tr.status-error {
  background-color: #ffeaea;
}

.data-preview tr.status-warning {
  background-color: #fff8e1;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  white-space: nowrap;
}

.status-badge.success { 
  background: #d4edda; 
  color: #155724; 
}

.status-badge.warning { 
  background: #fff3cd; 
  color: #856404; 
}

.status-badge.error { 
  background: #f8d7da; 
  color: #721c24; 
}

.preview-note {
  margin-top: 10px;
  color: #666;
  font-style: italic;
}

/* Mapping Configuration */
.mapping-config {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.mapping-config h3 {
  margin: 0;
  color: #333;
}

.mapping-status {
  color: #666;
  font-size: 14px;
}

/* Unmatched Items */
.unmatched-items {
  margin: 20px 0;
  padding: 20px;
  background: #fff8e1;
  border-radius: 8px;
  border-left: 4px solid #ffc107;
}

.unmatched-items h3 {
  margin-top: 0;
  color: #856404;
}

.unmatched-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.unmatched-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.unmatched-info {
  flex: 1;
}

.unmatched-info strong {
  display: block;
  color: #333;
}

.unmatched-column {
  font-size: 12px;
  color: #666;
}

.match-selector {
  min-width: 200px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

/* Validation Summary */
.validation-summary {
  margin: 20px 0;
}

.validation-stats {
  display: flex;
  gap: 20px;
  justify-content: center;
}

.stat {
  text-align: center;
  padding: 15px;
  border-radius: 8px;
  min-width: 80px;
}

.stat.success {
  background: #d4edda;
  color: #155724;
}

.stat.warning {
  background: #fff3cd;
  color: #856404;
}

.stat.error {
  background: #f8d7da;
  color: #721c24;
}

.stat-number {
  display: block;
  font-size: 24px;
  font-weight: bold;
}

.stat-label {
  font-size: 12px;
  text-transform: uppercase;
}

/* Import Summary */
.import-summary {
  margin: 20px 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
  margin-top: 15px;
}

.summary-item {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.summary-number {
  display: block;
  font-size: 28px;
  font-weight: bold;
  color: #007bff;
}

.summary-label {
  font-size: 14px;
  color: #666;
}

/* Progress */
.progress-container {
  margin: 20px 0;
}

.progress-bar {
  width: 100%;
  height: 20px;
  background: #e0e0e0;
  border-radius: 10px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #007bff, #0056b3);
  transition: width 0.3s ease;
  border-radius: 10px;
}

.progress-text {
  text-align: center;
  margin-top: 10px;
  font-weight: 500;
  color: #333;
}

/* Alerts */
.alert {
  padding: 15px;
  border-radius: 8px;
  margin: 15px 0;
}

.alert-success {
  background: #d4edda;
  border: 1px solid #c3e6cb;
  color: #155724;
}

.alert-error {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
}

.alert ul {
  margin: 10px 0 0 0;
  padding-left: 20px;
}

/* Export Section */
.export-section {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.export-section h2 {
  margin-top: 0;
  color: #333;
}

.project-selector {
  margin-bottom: 30px;
}

.project-search {
  margin: 15px 0;
}

.search-input {
  width: 100%;
  max-width: 400px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.project-list {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.select-all-container {
  padding: 15px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
  font-weight: 500;
}

.project-items {
  padding: 10px;
}

.project-item {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.project-item:hover {
  background-color: #f8f9fa;
}

.project-item:last-child {
  border-bottom: none;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  margin: 0;
}

.project-info {
  flex: 1;
}

.project-name {
  font-weight: 500;
  color: #333;
}

.project-details {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

/* Export Options */
.export-options,
.export-format {
  margin: 30px 0;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.format-options {
  display: flex;
  gap: 20px;
  margin-top: 15px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  transition: all 0.2s;
}

.radio-label:hover {
  background-color: #f8f9fa;
}

.radio-label input[type="radio"]:checked + span {
  font-weight: 500;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.mapping-editor-modal {
  background: white;
  border-radius: 12px;
  max-width: 900px;
  width: 90vw;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 5px;
  color: #666;
}

.close-btn:hover {
  color: #333;
}

.mapping-rules {
  flex: 1;
  overflow-y: auto;
  padding: 20px 30px;
}

.mapping-header {
  display: grid;
  grid-template-columns: 2fr 2fr 3fr;
  gap: 15px;
  padding: 10px 0;
  border-bottom: 2px solid #e0e0e0;
  margin-bottom: 15px;
}

.col-header {
  font-weight: 600;
  color: #333;
}

.mapping-rule {
  display: grid;
  grid-template-columns: 2fr 2fr 3fr;
  gap: 15px;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.column-name {
  font-weight: 500;
  color: #333;
}

.mapping-select,
.match-type-select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  width: 100%;
}

.mapping-options {
  display: flex;
  gap: 10px;
  align-items: center;
}

.group-input {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  flex: 1;
}

.modal-actions {
  padding: 20px 30px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

/* Buttons */
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
  transform: translateY(-1px);
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #545b62;
}

.action-buttons {
  position: sticky;
  bottom: 0;
  background: white;
  border-top: 1px solid #e0e0e0;
  padding: 20px 0;
  margin-top: 30px;
}

.button-group {
  display: flex;
  gap: 15px;
  justify-content: center;
}

/* Error Messages */
.error-message {
  background: #f8d7da;
  color: #721c24;
  padding: 10px;
  border-radius: 6px;
  border: 1px solid #f5c6cb;
  margin: 10px 0;
}

/* Responsive */
@media (max-width: 768px) {
  .import-export-container {
    padding: 10px;
  }
  
  .step-container,
  .export-section {
    padding: 20px;
  }
  
  .mapping-header,
  .mapping-rule {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .validation-stats {
    flex-direction: column;
    gap: 10px;
  }
  
  .summary-grid {
    grid-template-columns: 1fr;
  }
  
  .format-options {
    flex-direction: column;
    gap: 10px;
  }
  
  .button-group {
    flex-direction: column;
  }
  
  .mapping-editor-modal {
    width: 95vw;
    margin: 10px;
  }
  
  .modal-header,
  .mapping-rules,
  .modal-actions {
    padding: 15px 20px;
  }
}
</style>