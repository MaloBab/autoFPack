<script setup lang="ts">
import { ref, computed, onMounted, reactive, nextTick } from 'vue'

// Types adaptés au backend existant
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

interface FpackItem {
  FPackNumber: string
  RobotLocationCode: string
  selectedProjetGlobal: number | null
  selectedSousProjet: number | null
  [key: string]: any
}

interface ValidationResult {
  column: string
  value: string
  status: 'success' | 'warning' | 'error' | 'manual'
  message: string
  suggestions?: any[]
  selectedMatch?: number
}

interface Notification {
  id: number
  type: 'success' | 'warning' | 'error' | 'info'
  message: string
}

interface UnmatchedItem {
  id: string
  value: string
  column: string
  suggestions: any[]
  selectedMatch?: any
}

// État réactif
const activeTab = ref<'import' | 'export'>('import')
const importStep = ref(1)

// Import state
const selectedFile = ref<File | null>(null)
const isDragOver = ref(false)
const isAnalyzing = ref(false)
const previewData = ref<any[]>([])
const previewColumns = ref<string[]>([])
const fpackList = ref<FpackItem[]>([])
const mappingConfig = ref<Record<string, any>>({})
const unmatchedItems = ref<UnmatchedItem[]>([])
const isImporting = ref(false)

// Export state
const isExporting = ref(false)
const selectedExportData = reactive({
  project_ids: [] as number[],
  options: {
    includeSelections: true,
    includeComments: false
  },
  format: "excel" as "excel" | "csv"
})

// Données
const projetsGlobaux = ref<ProjetGlobal[]>([])
const availableGroupes = ref<any[]>([])
const notifications = ref<Notification[]>([])
const clients = ref<any[]>([])
const selectedClient = ref<number | null>(null)

// Configuration de mapping basée sur le backend
const defaultMappingConfig = {
  "excel_columns": {
    "FPack Number": {
      "target": "sous_projet_fpack.FPack_number",
      "type": "direct"
    },
    "Plant": {
      "target": "sous_projet_fpack.plant", 
      "type": "direct"
    },
    "Area/Line": {
      "target": "sous_projet_fpack.area_line",
      "type": "direct"
    },
    "Station/Mode zone": {
      "target": "sous_projet_fpack.station_mode_zone",
      "type": "direct"
    },
    "Machine code": {
      "target": "sous_projet_fpack.machine_code",
      "type": "direct"
    },
    "Robot location code": {
      "target": "sous_projet_fpack.Robot_Location_Code",
      "type": "direct"
    },
    "Area section": {
      "target": "sous_projet_fpack.area_section", 
      "type": "direct"
    },
    "Direct Link": {
      "target": "sous_projet_fpack.direct_link",
      "type": "direct"
    },
    "Contractor": {
      "target": "sous_projet_fpack.contractor",
      "type": "direct"
    },
    "Required Delivery time": {
      "target": "sous_projet_fpack.required_delivery_time",
      "type": "direct"
    },
    "Delivery site": {
      "target": "sous_projet_fpack.delivery_site",
      "type": "direct"
    },
    "Tracking": {
      "target": "sous_projet_fpack.tracking",
      "type": "direct"
    },
    "Mechanical Unit": {
      "target": "selection",
      "groupe_nom": "Mechanical Unit",
      "search_in": ["robots", "equipements"],
      "search_fields": ["nom", "model"],
      "type": "fuzzy_match"
    },
    "Robot Controller": {
      "target": "selection",
      "groupe_nom": "Robot Controller", 
      "search_in": ["produits", "equipements"],
      "search_fields": ["nom", "description"],
      "type": "fuzzy_match"
    },
    "Media Panel (G)": {
      "target": "selection",
      "groupe_nom": "Media Panel",
      "search_in": ["produits"],
      "search_fields": ["nom"],
      "type": "exact_match"
    },
    "Key Equipment (G)": {
      "target": "selection", 
      "groupe_nom": "Key Equipment",
      "search_in": ["equipements"],
      "search_fields": ["nom"],
      "type": "fuzzy_match"
    }
  }
}

// Computed properties
const allFPacksHaveProject = computed(() => {
  return fpackList.value.every(fpack => 
    fpack.selectedProjetGlobal && fpack.selectedSousProjet
  )
})

const mappedColumnsCount = computed(() => {
  return Object.keys(mappingConfig.value.excel_columns || {}).length
})

const uniqueProjectCount = computed(() => {
  const projects = new Set(fpackList.value.map(f => f.selectedProjetGlobal).filter(Boolean))
  return projects.size
})

const canExecuteImport = computed(() => {
  return unmatchedItems.value.every(item => item.selectedMatch)
})

const totalSelectedItems = computed(() => {
  return selectedExportData.project_ids.length
})

// Methods
const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
  
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    handleFileSelect({ target: { files } } as any)
  }
}

const handleFileSelect = (event: any) => {
  const file = event.target.files[0]
  if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
    selectedFile.value = file
  } else {
    addNotification('error', 'Format de fichier non supporté. Utilisez .xlsx ou .xls')
  }
}

const removeFile = () => {
  selectedFile.value = null
  previewData.value = []
  previewColumns.value = []
  fpackList.value = []
  importStep.value = 1
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const analyzeFile = async () => {
  if (!selectedFile.value) return
  
  isAnalyzing.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    
    const response = await fetch('http://localhost:8000/import/upload', {
      method: 'POST',
      body: formData
    })
    
    const result = await response.json()
    
    if (result.success) {
      previewData.value = result.preview
      previewColumns.value = result.columns
      
      // Extraire les F-Packs
      fpackList.value = result.preview.map((row: any) => ({
        FPackNumber: row['FPack Number'] || '',
        RobotLocationCode: row['Robot location code'] || '',
        selectedProjetGlobal: null,
        selectedSousProjet: null,
        ...row
      }))
      
      // Initialiser le mapping avec la config par défaut
      mappingConfig.value = { ...defaultMappingConfig }
      
      importStep.value = 2
      addNotification('success', `Fichier analysé avec succès. ${result.preview.length} lignes détectées.`)
    } else {
      addNotification('error', result.detail || 'Erreur lors de l\'analyse du fichier')
    }
  } catch (error) {
    addNotification('error', 'Erreur lors de l\'upload du fichier')
    console.error(error)
  } finally {
    isAnalyzing.value = false
  }
}

const onProjetGlobalChange = (fpack: FpackItem) => {
  fpack.selectedSousProjet = null
}

const getAvailableSousProjets = (projetGlobalId: number | null) => {
  if (!projetGlobalId) return []
  const projet = projetsGlobaux.value.find(p => p.id === projetGlobalId)
  return projet?.sous_projets || []
}

const getSampleValue = (column: string): string => {
  const firstRow = previewData.value[0]
  return firstRow?.[column] || '-'
}

const previewImport = async () => {
  if (!selectedClient.value) {
    addNotification('error', 'Veuillez sélectionner un client')
    return
  }

  try {
    const requestData = {
      preview_data: previewData.value,
      mapping_config: mappingConfig.value,
      client_id: selectedClient.value
    }
    
    const response = await fetch('http://localhost:8000/import/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData)
    })
    
    const result = await response.json()
    
    if (result.success) {
      unmatchedItems.value = result.unmatched_items || []
      importStep.value = 4
      addNotification('success', 'Prévisualisation générée avec succès')
    } else {
      addNotification('error', result.detail || 'Erreur lors de la prévisualisation')
    }
  } catch (error) {
    addNotification('error', 'Erreur lors de la prévisualisation')
    console.error(error)
  }
}

const executeImport = async () => {
  if (!selectedClient.value) {
    addNotification('error', 'Veuillez sélectionner un client')
    return
  }

  isImporting.value = true
  try {
    const manualMatches = unmatchedItems.value
      .filter(item => item.selectedMatch)
      .map(item => ({
        row_index: parseInt(item.id.split('_')[0]),
        column: item.column,
        selectedMatch: item.selectedMatch
      }))

    const requestData = {
      file_data: previewData.value,
      mapping_config: mappingConfig.value,
      client_id: selectedClient.value,
      manual_matches: manualMatches
    }
    
    const response = await fetch('http://localhost:8000/import/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData)
    })
    
    const result = await response.json()
    
    if (result.success) {
      addNotification('success', `Import réalisé avec succès! ${result.results.created_projects} projets créés.`)
      resetImport()
    } else {
      addNotification('error', result.detail || 'Erreur lors de l\'import')
    }
  } catch (error) {
    addNotification('error', 'Erreur lors de l\'import')
    console.error(error)
  } finally {
    isImporting.value = false
  }
}

const executeExport = async () => {
  if (selectedExportData.project_ids.length === 0) {
    addNotification('error', 'Veuillez sélectionner au moins un projet')
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
      
      addNotification('success', 'Export généré avec succès!')
    } else {
      addNotification('error', 'Erreur lors de l\'export')
    }
  } catch (error) {
    addNotification('error', 'Erreur lors de l\'export')
    console.error(error)
  } finally {
    isExporting.value = false
  }
}

// Export selection methods
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
  selectedExportData.project_ids = projetsGlobaux.value.map(p => p.id)
}

const deselectAllProjects = () => {
  selectedExportData.project_ids = []
}

// Utility functions
const resetImport = () => {
  selectedFile.value = null
  previewData.value = []
  previewColumns.value = []
  fpackList.value = []
  mappingConfig.value = {}
  unmatchedItems.value = []
  importStep.value = 1
}

const getValidationIcon = (status: string): string => {
  switch (status) {
    case 'success': return '✅'
    case 'warning': return '⚠️'
    case 'error': return '❌'
    case 'manual': return '✏️'
    default: return 'ℹ️'
  }
}

const getNotificationIcon = (type: string): string => {
  switch (type) {
    case 'success': return '✅'
    case 'warning': return '⚠️'
    case 'error': return '❌'
    case 'info': return 'ℹ️'
    default: return 'ℹ️'
  }
}

let notificationId = 0
const addNotification = (type: 'success' | 'warning' | 'error' | 'info', message: string) => {
  const id = ++notificationId
  notifications.value.push({ id, type, message })
  
  // Auto-remove after 5 seconds
  setTimeout(() => {
    removeNotification(id)
  }, 5000)
}

const removeNotification = (id: number) => {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index > -1) {
    notifications.value.splice(index, 1)
  }
}

const loadProjects = async () => {
  try {
    const response = await fetch('http://localhost:8000/projets_tree')
    const data = await response.json()
    if (data.projets_global) {
      projetsGlobaux.value = data.projets_global
    }
  } catch (error) {
    console.error('Erreur lors du chargement des projets:', error)
    addNotification('error', 'Erreur lors du chargement des projets')
  }
}

// Lifecycle
onMounted(async () => {
  try {
    // Charger les projets
    await loadProjects()
    
    // Simuler le chargement des clients (à adapter selon votre API)
    clients.value = [
      { id: 1, nom: 'Client 1' },
      { id: 2, nom: 'Client 2' }
    ]
    
    // Simuler les groupes disponibles
    availableGroupes.value = [
      { id: 1, nom: 'Mechanical Unit' },
      { id: 2, nom: 'Robot Controller' },
      { id: 3, nom: 'Media Panel' },
      { id: 4, nom: 'Key Equipment' }
    ]
    
  } catch (error) {
    console.error('Erreur lors du chargement des données:', error)
    addNotification('error', 'Erreur lors du chargement des données')
  }
})
</script>

<template>
  <div class="project-import-export">
    <!-- Header avec onglets -->
    <div class="header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="title">🚀 F-Pack Matrix Manager</h1>
          <p class="subtitle">Gestion avancée de l'import/export des données F-Pack</p>
        </div>
        <div class="tabs">
          <button 
            class="tab"
            :class="{ active: activeTab === 'import' }"
            @click="activeTab = 'import'"
          >
            <div class="tab-icon">📥</div>
            <span>Import</span>
          </button>
          <button 
            class="tab"
            :class="{ active: activeTab === 'export' }"
            @click="activeTab = 'export'"
          >
            <div class="tab-icon">📤</div>
            <span>Export</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Section Import -->
    <div v-if="activeTab === 'import'" class="import-section">
      <!-- Étape 1: Upload du fichier -->
      <div class="step-container" :class="{ active: importStep >= 1, completed: importStep > 1 }">
        <div class="step-header">
          <div class="step-indicator">
            <div class="step-number">1</div>
            <div class="step-line"></div>
          </div>
          <div class="step-content-header">
            <h3>📁 Sélection du fichier Excel</h3>
            <p class="step-description">Glissez-déposez ou sélectionnez votre fichier F-Pack Matrix</p>
          </div>
        </div>
        
        <div class="step-body" v-show="importStep === 1">
          <div 
            class="drop-zone"
            :class="{ 'dragover': isDragOver, 'has-file': selectedFile }"
            @drop="handleDrop"
            @dragover.prevent="isDragOver = true"
            @dragleave="isDragOver = false"
          >
            <div v-if="!selectedFile" class="drop-zone-content">
              <div class="upload-icon">📊</div>
              <h4>Glissez-déposez votre fichier Excel</h4>
              <p>ou cliquez pour parcourir</p>
              <div class="supported-formats">
                <span class="format-badge">.xlsx</span>
                <span class="format-badge">.xls</span>
              </div>
            </div>
            
            <div v-else class="file-selected">
              <div class="file-icon">✅</div>
              <div class="file-info">
                <h4 class="file-name">{{ selectedFile.name }}</h4>
                <p class="file-size">{{ formatFileSize(selectedFile.size) }}</p>
              </div>
              <button class="btn-remove" @click.stop="removeFile">
                ❌
              </button>
            </div>
          </div>
          
          <input 
            ref="fileInput"
            type="file"
            accept=".xlsx,.xls"
            @change="handleFileSelect"
            style="display: none"
          />
          
          <div class="step-actions">
            <button 
              class="btn btn-primary"
              :disabled="!selectedFile || isAnalyzing"
              @click="analyzeFile"
            >
              <span v-if="!isAnalyzing">🔍 Analyser le fichier</span>
              <span v-else>⏳ Analyse...</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Étape 2: Aperçu et sélection des projets -->
      <div class="step-container" :class="{ active: importStep >= 2, completed: importStep > 2 }">
        <div class="step-header">
          <div class="step-indicator">
            <div class="step-number">2</div>
            <div class="step-line"></div>
          </div>
          <div class="step-content-header">
            <h3>👁️ Aperçu et attribution des projets</h3>
            <p class="step-description">Vérifiez les données et attribuez les F-Packs aux projets</p>
          </div>
        </div>
        
        <div class="step-body" v-show="importStep === 2">
          <!-- Sélection du client -->
          <div class="client-selection">
            <label class="form-label">🏢 Client:</label>
            <select v-model="selectedClient" class="form-select">
              <option value="">Sélectionner un client</option>
              <option v-for="client in clients" :key="client.id" :value="client.id">
                {{ client.nom }}
              </option>
            </select>
          </div>

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
                    <th v-for="column in previewColumns.slice(0, 8)" :key="column">
                      {{ column }}
                    </th>
                    <th v-if="previewColumns.length > 8">...</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, index) in previewData.slice(0, 3)" :key="index">
                    <td v-for="column in previewColumns.slice(0, 8)" :key="column">
                      {{ row[column] || '-' }}
                    </td>
                    <td v-if="previewColumns.length > 8">...</td>
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
                v-for="(fpack, index) in fpackList.slice(0, 5)" 
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
              
              <div v-if="fpackList.length > 5" class="more-fpacks">
                <div class="more-indicator">
                  +{{ fpackList.length - 5 }} autres F-Packs
                </div>
              </div>
            </div>
          </div>
          
          <div class="step-actions">
            <button class="btn btn-secondary" @click="importStep = 1">
              ← Retour
            </button>
            <button 
              class="btn btn-primary"
              :disabled="!allFPacksHaveProject || !selectedClient"
              @click="importStep = 3"
            >
              Configuration mapping →
            </button>
          </div>
        </div>
      </div>

      <!-- Étape 3: Configuration du mapping -->
      <div class="step-container" :class="{ active: importStep >= 3, completed: importStep > 3 }">
        <div class="step-header">
          <div class="step-indicator">
            <div class="step-number">3</div>
            <div class="step-line"></div>
          </div>
          <div class="step-content-header">
            <h3>🔗 Configuration du mapping</h3>
            <p class="step-description">Configuration automatique basée sur les standards F-Pack Matrix</p>
          </div>
        </div>
        
        <div class="step-body" v-show="importStep === 3">
          <div class="mapping-overview">
            <div class="mapping-stats">
              <div class="stat-card">
                <div class="stat-value">{{ mappedColumnsCount }}</div>
                <div class="stat-label">Colonnes mappées</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ previewColumns.length }}</div>
                <div class="stat-label">Colonnes détectées</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ uniqueProjectCount }}</div>
                <div class="stat-label">Projets concernés</div>
              </div>
            </div>
            
            <div class="mapping-preview">
              <h5>🎯 Mapping automatique configuré</h5>
              <div class="mapping-list-compact">
                <div v-for="(config, column) in mappingConfig.excel_columns" :key="column" class="mapping-item-compact">
                  <span class="column-name">{{ column }}</span>
                  <span class="arrow">→</span>
                  <span class="target-name" :class="config.type">
                    {{ config.target === 'selection' ? `📋 ${config.groupe_nom}` : `📝 ${config.target.split('.')[1]}` }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="step-actions">
            <button class="btn btn-secondary" @click="importStep = 2">
              ← Retour
            </button>
            <button class="btn btn-primary" @click="previewImport">
              👁️ Prévisualiser l'import
            </button>
          </div>
        </div>
      </div>

      <!-- Étape 4: Prévisualisation et validation -->
      <div class="step-container" :class="{ active: importStep >= 4 }">
        <div class="step-header">
          <div class="step-indicator">
            <div class="step-number">4</div>
          </div>
          <div class="step-content-header">
            <h3>✅ Validation finale</h3>
            <p class="step-description">Vérifiez et corrigez les correspondances avant l'import</p>
          </div>
        </div>
        
        <div class="step-body" v-show="importStep === 4">
          <!-- Résolutions manuelles nécessaires -->
          <div v-if="unmatchedItems.length > 0" class="unmatched-section">
            <h4>⚠️ Correspondances à valider ({{ unmatchedItems.length }})</h4>
            <div class="unmatched-list">
              <div 
                v-for="item in unmatchedItems" 
                :key="item.id"
                class="unmatched-item"
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
                  <div class="summary-label">À valider</div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="step-actions">
            <button class="btn btn-secondary" @click="importStep = 3">
              ← Retour
            </button>
            <button 
              class="btn btn-success"
              :disabled="!canExecuteImport || isImporting"
              @click="executeImport"
            >
              <span v-if="!isImporting">🚀 Exécuter l'import</span>
              <span v-else>⏳ Import en cours...</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Section Export -->
    <div v-if="activeTab === 'export'" class="export-section">
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
            
            <div class="export-options">
              <label class="checkbox-label">
                <input type="checkbox" v-model="selectedExportData.options.includeSelections" />
                <span class="checkmark"></span>
                Inclure les sélections d'équipements
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="selectedExportData.options.includeComments" />
                <span class="checkmark"></span>
                Inclure les commentaires
              </label>
            </div>
            
            <div class="format-selection">
              <label class="form-label">Format d'export:</label>
              <div class="format-buttons">
                <button 
                  class="format-btn"
                  :class="{ active: selectedExportData.format === 'excel' }"
                  @click="selectedExportData.format = 'excel'"
                >
                  📊 Excel
                </button>
                <button 
                  class="format-btn"
                  :class="{ active: selectedExportData.format === 'csv' }"
                  @click="selectedExportData.format = 'csv'"
                >
                  📄 CSV
                </button>
              </div>
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

    <!-- Notifications -->
    <div class="notifications" v-if="notifications.length > 0">
      <transition-group name="notification" tag="div">
        <div 
          v-for="notification in notifications" 
          :key="notification.id"
          class="notification"
          :class="notification.type"
        >
          <div class="notification-icon">
            {{ getNotificationIcon(notification.type) }}
          </div>
          <div class="notification-content">
            <span>{{ notification.message }}</span>
          </div>
          <button class="notification-close" @click="removeNotification(notification.id)">
            ❌
          </button>
        </div>
      </transition-group>
    </div>
  </div>
</template>

<style scoped>
/* Variables CSS pour le thème */
:root {
  --primary-color: #667eea;
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --secondary-color: #f093fb;
  --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  --success-color: #10b981;
  --success-gradient: linear-gradient(135deg, #10b981 0%, #059669 100%);
  --warning-color: #f59e0b;
  --error-color: #ef4444;
  --info-color: #3b82f6;
  
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-card: #ffffff;
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --border-color: #e2e8f0;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 40px rgba(0, 0, 0, 0.1);
  
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-2xl: 48px;
}

/* Base styles */
.project-import-export {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  color: var(--text-primary);
}

/* Header */
.header {
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--spacing-lg);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  flex: 1;
}

.title {
  font-size: 2rem;
  font-weight: 800;
  background: var(--primary-gradient);
  -webkit-text-fill-color: transparent;
  margin: 0;
  line-height: 1.2;
}

.subtitle {
  color: var(--text-secondary);
  margin: var(--spacing-xs) 0 0 0;
  font-size: 0.9rem;
}

/* Onglets */
.tabs {
  display: flex;
  gap: var(--spacing-xs);
}

.tab {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  background: transparent;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 600;
  color: var(--text-secondary);
}

.tab:hover {
  border-color: var(--primary-color);
  background: rgba(102, 126, 234, 0.05);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.tab.active {
  background: var(--primary-gradient);
  border-color: transparent;
  color: white;
  box-shadow: var(--shadow-lg);
}

.tab-icon {
  font-size: 1.2rem;
}

/* Sections principales */
.import-section,
.export-section {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--spacing-2xl) var(--spacing-lg);
}

/* Étapes */
.step-container {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  margin-bottom: var(--spacing-xl);
  overflow: hidden;
  box-shadow: var(--shadow-md);
  transition: all 0.3s ease;
}

.step-container.active {
  box-shadow: var(--shadow-lg);
  border: 2px solid var(--primary-color);
}

.step-container.completed {
  opacity: 0.8;
}

.step-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg) var(--spacing-xl);
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-bottom: 1px solid var(--border-color);
}

.step-indicator {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.step-number {
  width: 40px;
  height: 40px;
  background: var(--primary-gradient);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.1rem;
  box-shadow: var(--shadow-md);
}

.step-line {
  width: 60px;
  height: 2px;
  background: var(--border-color);
}

.step-container.completed .step-number {
  background: var(--success-gradient);
}

.step-container.completed .step-line {
  background: var(--success-color);
}

.step-content-header h3 {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--text-primary);
}

.step-description {
  margin: var(--spacing-xs) 0 0 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.step-body {
  padding: var(--spacing-xl);
}

/* Drop zone */
.drop-zone {
  border: 3px dashed var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--spacing-2xl);
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--bg-secondary);
  margin-bottom: var(--spacing-lg);
}

.drop-zone:hover {
  border-color: var(--primary-color);
  background: rgba(102, 126, 234, 0.05);
}

.drop-zone.dragover {
  border-color: var(--primary-color);
  background: rgba(102, 126, 234, 0.1);
  transform: scale(1.02);
}

.drop-zone.has-file {
  border-color: var(--success-color);
  background: rgba(16, 185, 129, 0.05);
}

.drop-zone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
}

.upload-icon {
  font-size: 4rem;
  opacity: 0.7;
}

.drop-zone-content h4 {
  margin: 0;
  font-size: 1.2rem;
  color: var(--text-primary);
}

.drop-zone-content p {
  margin: 0;
  color: var(--text-secondary);
}

.supported-formats {
  display: flex;
  gap: var(--spacing-sm);
}

.format-badge {
  background: var(--primary-color);
  color: white;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  font-weight: 600;
}

.file-selected {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  background: white;
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.file-icon {
  font-size: 2rem;
}

.file-info {
  flex: 1;
  text-align: left;
}

.file-name {
  margin: 0;
  font-weight: 600;
  color: var(--text-primary);
}

.file-size {
  margin: var(--spacing-xs) 0 0 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.btn-remove {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.btn-remove:hover {
  opacity: 1;
}

/* Formulaires */
.form-label {
  display: block;
  margin-bottom: var(--spacing-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.form-select {
  width: 100%;
  padding: var(--spacing-md);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.form-select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-select.compact {
  padding: var(--spacing-sm);
  font-size: 0.85rem;
}

.client-selection {
  margin-bottom: var(--spacing-xl);
  max-width: 400px;
}

/* Aperçu des données */
.data-preview {
  margin-bottom: var(--spacing-xl);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.preview-header h4 {
  margin: 0;
  font-size: 1.2rem;
  color: var(--text-primary);
}

.preview-stats {
  display: flex;
  gap: var(--spacing-sm);
}

.stat-badge {
  background: var(--primary-color);
  color: white;
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--radius-lg);
  font-size: 0.8rem;
  font-weight: 600;
}

.preview-table-container {
  background: white;
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
}

.preview-table th {
  background: var(--bg-secondary);
  padding: var(--spacing-md);
  font-weight: 600;
  text-align: left;
  border-bottom: 2px solid var(--border-color);
  color: var(--text-primary);
}

.preview-table td {
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.preview-note {
  padding: var(--spacing-md);
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.8rem;
  background: var(--bg-secondary);
  margin: 0;
}

/* Attribution F-Packs */
.fpack-assignment {
  margin-bottom: var(--spacing-xl);
}

.fpack-assignment h4 {
  margin-bottom: var(--spacing-lg);
  color: var(--text-primary);
}

.fpack-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-lg);
}

.fpack-card {
  background: white;
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.fpack-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--primary-color);
}

.fpack-info {
  margin-bottom: var(--spacing-md);
}

.fpack-number {
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--text-primary);
}

.robot-location {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-top: var(--spacing-xs);
}

.project-selectors {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.more-fpacks {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
}

.more-indicator {
  color: var(--text-secondary);
  font-weight: 600;
  text-align: center;
}

/* Configuration mapping */
.mapping-overview {
  margin-bottom: var(--spacing-xl);
}

.mapping-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.stat-card {
  background: white;
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  text-align: center;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
}

.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 800;
  background: var(--primary-gradient);
  -webkit-text-fill-color: transparent;
  line-height: 1;
}

.stat-label {
  color: var(--text-secondary);
  font-weight: 600;
  margin-top: var(--spacing-xs);
}

.mapping-preview {
  background: white;
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.mapping-preview h5 {
  margin: 0 0 var(--spacing-lg) 0;
  color: var(--text-primary);
}

.mapping-list-compact {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-sm);
}

.mapping-item-compact {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
}

.column-name {
  font-weight: 600;
  color: var(--text-primary);
}

.arrow {
  color: var(--text-secondary);
  font-weight: 600;
}

.target-name {
  font-weight: 500;
}

.target-name.direct {
  color: var(--info-color);
}

.target-name.selection {
  color: var(--secondary-color);
}

/* Validation */
.unmatched-section {
  margin-bottom: var(--spacing-xl);
}

.unmatched-section h4 {
  color: var(--warning-color);
  margin-bottom: var(--spacing-lg);
}

.unmatched-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.unmatched-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: white;
  border-radius: var(--radius-lg);
  border: 2px solid var(--warning-color);
  box-shadow: var(--shadow-sm);
}

.unmatched-info {
  flex: 1;
}

.unmatched-value {
  font-weight: 600;
  color: var(--text-primary);
}

.unmatched-column {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.suggestions-dropdown {
  flex: 2;
}

/* Résumé import */
.import-summary {
  margin-bottom: var(--spacing-xl);
}

.import-summary h4 {
  margin-bottom: var(--spacing-lg);
  color: var(--text-primary);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-lg);
}

.summary-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  background: white;
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
}

.summary-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.summary-icon {
  font-size: 2rem;
  opacity: 0.8;
}

.summary-value {
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1;
}

.summary-label {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-top: var(--spacing-xs);
}

/* Export */
.export-controls {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-lg);
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.selection-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.export-options {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  font-weight: 500;
  color: var(--text-primary);
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--primary-color);
}

.format-selection .form-label {
  margin-bottom: var(--spacing-sm);
}

.format-buttons {
  display: flex;
  gap: var(--spacing-xs);
}

.format-btn {
  flex: 1;
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
  color: var(--text-primary);
}

.project-import-export {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Header */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e5e7eb;
}

.title {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.tabs {
  display: flex;
  gap: 8px;
}

.tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border: 2px solid #e5e7eb;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
  color: #6b7280;
}

.tab:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.tab.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
}

/* Steps */
.step {
  margin-bottom: 30px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s;
}

.step.active {
  border-color: #3b82f6;
  box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.1);
}

.step.completed {
  border-color: #10b981;
  background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
}

.step-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  cursor: pointer;
}

.step.completed .step-header {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #6b7280;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.step.active .step-number {
  background: #3b82f6;
}

.step.completed .step-number {
  background: #10b981;
}

.step-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.step-content {
  padding: 24px;
}

/* Drop Zone */
.drop-zone {
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafafa;
}

.drop-zone:hover, .drop-zone.dragover {
  border-color: #3b82f6;
  background: #eff6ff;
}

.drop-zone.has-file {
  border-color: #10b981;
  background: #ecfdf5;
}

.drop-zone-content i {
  font-size: 48px;
  color: #6b7280;
  margin-bottom: 16px;
  display: block;
}

.drop-zone-content p {
  font-size: 18px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 8px 0;
}

.drop-zone-content span {
  font-size: 14px;
  color: #6b7280;
  display: block;
  margin-bottom: 16px;
}

.drop-zone-content small {
  font-size: 12px;
  color: #9ca3af;
}

.file-selected {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #10b981;
}

.file-selected i {
  font-size: 24px;
  color: #10b981;
}

.file-info {
  flex: 1;
  text-align: left;
}

.file-name {
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 4px 0;
}

.file-size {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.btn-remove {
  background: none;
  border: none;
  color: #ef4444;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s;
}

.btn-remove:hover {
  background: #fee2e2;
}

/* Preview Table */
.data-preview {
  margin-bottom: 24px;
}

.data-preview h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 16px;
}

.preview-table-container {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: auto;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.preview-table th {
  background: #f9fafb;
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
}

.preview-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
  color: #6b7280;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-note {
  padding: 8px 16px;
  background: #f9fafb;
  color: #6b7280;
  font-size: 12px;
  margin: 0;
  text-align: center;
  border-top: 1px solid #e5e7eb;
}

/* F-Pack Selection */
.fpack-selection h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 16px;
}

.fpack-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.fpack-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: border-color 0.2s;
}

.fpack-item:hover {
  border-color: #3b82f6;
}

.fpack-info {
  min-width: 200px;
}

.fpack-number {
  display: block;
  font-weight: 600;
  color: #1f2937;
  font-size: 14px;
}

.robot-location {
  display: block;
  font-size: 12px;
  color: #6b7280;
}

.project-selectors {
  display: flex;
  gap: 12px;
  flex: 1;
}

.select-projet, .select-sous-projet {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  font-size: 14px;
}

.select-projet:focus, .select-sous-projet:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Mapping Configuration */
.mapping-config h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 16px;
}

.mapping-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.mapping-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mapping-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.2s;
}

.mapping-item.mapped {
  border-color: #10b981;
  background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
}

.excel-column {
  min-width: 200px;
}

.excel-column strong {
  display: block;
  color: #1f2937;
  font-size: 14px;
  margin-bottom: 4px;
}

.sample-value {
  font-size: 12px;
  color: #6b7280;
  font-style: italic;
}

.mapping-arrow {
  font-size: 18px;
  color: #6b7280;
  font-weight: bold;
}

.target-config {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mapping-type, .target-field, .groupe-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  font-size: 14px;
}

.direct-config, .groupe-config {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.match-config {
  margin-top: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #374151;
  cursor: pointer;
}

/* Buttons */
.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: 8px;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-secondary {
  background: #6b7280;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #4b5563;
}

.btn-success {
  background: #10b981;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #059669;
}

.btn-outline {
  background: white;
  color: #3b82f6;
  border: 1px solid #3b82f6;
}

.btn-outline:hover {
  background: #3b82f6;
  color: white;
}

/* Import Summary */
.import-summary {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-item .label {
  font-size: 12px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.summary-item .value {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

/* Validation Results */
.validation-results h5 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 16px;
}

.validation-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.validation-item {
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid;
}

.validation-item.success {
  background: #ecfdf5;
  border-color: #10b981;
}

.validation-item.warning {
  background: #fffbeb;
  border-color: #f59e0b;
}

.validation-item.error {
  background: #fef2f2;
  border-color: #ef4444;
}

.validation-item.manual {
  background: #f0f9ff;
  border-color: #0ea5e9;
}

.validation-info {
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
}

.validation-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #6b7280;
}

.manual-selection {
  margin-top: 12px;
}

.manual-selection select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
}

/* Export Section */
.export-selection {
  margin-bottom: 24px;
}

.selection-tree {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: white;
}

.projet-node {
  border-bottom: 1px solid #f3f4f6;
}

.projet-node:last-child {
  border-bottom: none;
}

.projet-header {
  padding: 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.sous-projets {
  padding-left: 20px;
}

.sous-projet-node {
  padding: 12px 16px;
  border-bottom: 1px solid #f9fafb;
}

.fpack-configs {
  padding-left: 20px;
  background: #fafafa;
}

.fpack-config-node {
  padding: 8px 16px;
  font-size: 14px;
}

.export-summary h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 16px;
}

.summary-stats {
  display: flex;
  gap: 32px;
  padding: 20px;
  background: #f9fafb;
  border-radius: 8px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat .count {
  font-size: 24px;
  font-weight: 700;
  color: #3b82f6;
}

.stat .label {
  font-size: 12px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Notifications */
.notifications {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  min-width: 300px;
  animation: slideIn 0.3s ease-out;
}

.notification.success {
  background: #10b981;
}

.notification.warning {
  background: #f59e0b;
}

.notification.error {
  background: #ef4444;
}

.notification.info {
  background: #3b82f6;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Icons (utilisation de classes CSS pour les icônes) */
[class^="icon-"] {
  display: inline-block;
  width: 1em;
  height: 1em;
}

.icon-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
  .project-import-export {
    padding: 16px;
  }
  
  .header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .fpack-item {
    flex-direction: column;
    align-items: stretch;
  }
  
  .project-selectors {
    flex-direction: column;
  }
  
  .mapping-item {
    flex-direction: column;
    align-items: stretch;
  }
  
  .mapping-arrow {
    transform: rotate(90deg);
    align-self: center;
  }
  
  .summary-stats {
    flex-direction: column;
    gap: 16px;
  }
  
  .import-summary {
    flex-direction: column;
    gap: 12px;
  }
}
</style>