<script setup lang="ts">
import { ref, computed, onMounted, reactive, onBeforeUnmount, watch, nextTick} from 'vue'

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

let observer: MutationObserver | null = null
let previewTableContainerEl: HTMLElement | null = null

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
  },
  format: "excel"
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

const handlePreviewTableWheel = (event: WheelEvent) => {
  if (!previewTableContainerEl) return;
  if (previewTableContainerEl.scrollWidth > previewTableContainerEl.clientWidth) {
    event.preventDefault();
    previewTableContainerEl.scrollLeft += event.deltaY;
  }
};

const attachListener = () => {
  previewTableContainerEl = document.querySelector('.preview-table-container')
  if (previewTableContainerEl && !previewTableContainerEl.dataset.wheelBound) {
    previewTableContainerEl.addEventListener('wheel', handlePreviewTableWheel, { passive: false })
    previewTableContainerEl.dataset.wheelBound = 'true'
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
    attachListener()

    observer = new MutationObserver(() => {
    attachListener()
    })

    observer.observe(document.body, { childList: true, subtree: true })

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

onBeforeUnmount(() => {
  if (previewTableContainerEl) {
    previewTableContainerEl.removeEventListener('wheel', handlePreviewTableWheel)
  }
  if (observer) {
    observer.disconnect()
  }
})

</script>

<template>
  <div class="project-import-export">
    <!-- Header avec onglets -->
    <div class="header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="title">Import / EXport de F-Pack</h1>
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
              <button class="btn-remove" @click.stop="removeFile">
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
/* Base styles et reset */
.project-import-export {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  line-height: 1.6;
  color: #2c3e50;
  background: #f7f7f7;
  height: 90vh;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.project-import-export * {
  box-sizing: border-box;
}

.header {
  backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.95);
  border-bottom: 1px solid rgba(52, 73, 94, 0.1);
  box-shadow: 0 4px 20px rgba(52, 73, 94, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  flex: 1;
}

.title {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #3498db 0%, #9b59b6 50%, #e74c3c 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
  line-height: 1.1;
  letter-spacing: -0.025em;
}

.tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: rgba(236, 240, 241, 0.8);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  box-shadow: inset 0 1px 3px rgba(52, 73, 94, 0.1);
  position: relative;
}

.tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  color: #7f8c8d;
  position: relative;
  z-index: 2;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  transform-origin: center;
}

.tab:hover {
  color: #34495e;
  transform: translateY(-1px);
}

.tab.active {
  color: #ffffff;
  background: linear-gradient(135deg, #3498db 0%, #9b59b6 100%);
  box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
  transform: translateY(-2px);
}

.tab-icon {
  font-size: 1.1rem;
  transition: all 0.3s ease;
}

.tab.active .tab-icon {
  transform: scale(1.1);
}

/* Conteneur principal avec scroll */
.import-section,
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
.import-section::-webkit-scrollbar,
.export-section::-webkit-scrollbar {
  width: 8px;
}

.import-section::-webkit-scrollbar-track,
.export-section::-webkit-scrollbar-track {
  background: rgba(189, 195, 199, 0.2);
  border-radius: 4px;
}

.import-section::-webkit-scrollbar-thumb,
.export-section::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #3498db, #9b59b6);
  border-radius: 4px;
}

.import-section::-webkit-scrollbar-thumb:hover,
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

/* Zone de drop */
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
  background: linear-gradient(135deg, rgba(155, 89, 182, 0.03), rgba(231, 76, 60, 0.03));
  transform: translateY(-3px);
  box-shadow: 0 12px 30px rgba(155, 89, 182, 0.15);
}

.drop-zone.has-file {
  border-color: #27ae60;
  background: linear-gradient(135deg, rgba(39, 174, 96, 0.03), rgba(46, 204, 113, 0.03));
  box-shadow: 0 8px 25px rgba(39, 174, 96, 0.1);
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

.drop-zone-content p {
  margin: 0;
  color: #7f8c8d;
  font-size: 1rem;
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

/* Fichier sélectionné */
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

/* Grille F-Pack */
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

.more-fpacks {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #fcfcfc 0%, #f8f9fa 100%);
  border: 2px dashed #bdc3c7;
  border-radius: 12px;
  padding: 28px;
  transition: all 0.3s ease;
}

.more-fpacks:hover {
  border-color: #3498db;
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.03), rgba(155, 89, 182, 0.03));
}

.more-indicator {
  color: #7f8c8d;
  font-weight: 600;
  text-align: center;
  font-size: 1rem;
}

/* Statistiques de mapping */
.mapping-overview {
  margin-bottom: 28px;
}

.mapping-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 28px;
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
  line-height: 1;
  margin-bottom: 6px;
}

.stat-label {
  color: #7f8c8d;
  font-weight: 600;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

/* Mapping preview */
.mapping-preview {
  background: #ffffff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(52, 73, 94, 0.06);
  border: 1px solid #ecf0f1;
}

.mapping-preview h5 {
  margin: 0 0 16px 0;
  color: #2c3e50;
  font-size: 1rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
}

.mapping-list-compact {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 10px;
}

.mapping-item-compact {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: linear-gradient(135deg, #fcfcfc 0%, #f8f9fa 100%);
  border-radius: 8px;
  font-size: 0.85rem;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.mapping-item-compact:hover {
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.03), rgba(155, 89, 182, 0.03));
  border-color: #3498db;
  transform: translateX(3px);
}

.column-name {
  font-weight: 600;
  color: #2c3e50;
  flex: 1;
}

.arrow {
  color: #7f8c8d;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.mapping-item-compact:hover .arrow {
  color: #3498db;
  transform: translateX(1px);
}

.target-name {
  font-weight: 500;
  flex: 1;
}

.target-name.direct {
  color: #3498db;
}

.target-name.fuzzy_match {
  color: #9b59b6;
}

.target-name.exact_match {
  color: #27ae60;
}

/* Validation */
.unmatched-section {
  margin-bottom: 28px;
}

.unmatched-section h4 {
  color: #f39c12;
  margin-bottom: 16px;
  font-size: 1.15rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
}

.unmatched-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 4px 20px rgba(243, 156, 18, 0.12);
  }
  50% {
    box-shadow: 0 6px 25px rgba(243, 156, 18, 0.18);
  }
}

.unmatched-item:hover {
  animation: none;
  box-shadow: 0 8px 25px rgba(243, 156, 18, 0.2);
  transform: translateY(-1px);
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

/* Résumé d'import */
.import-summary {
  margin-bottom: 28px;
}

.import-summary h4 {
  margin-bottom: 20px;
  color: #2c3e50;
  font-size: 1.15rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
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
  position: relative;
  overflow: hidden;
  border: 1px solid #ecf0f1;
}

.summary-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  background: linear-gradient(135deg, #3498db, #9b59b6);
  transform: scaleY(0);
  transform-origin: bottom;
  transition: transform 0.5s ease-out;
}

.summary-card:hover {
  box-shadow: 0 8px 25px rgba(52, 73, 94, 0.1);
  transform: translateY(-2px);
}

.summary-card:hover::before {
  transform: scaleY(1);
}


.summary-icon {
  font-size: 2rem;
  opacity: 0.7;
  transition: all 0.3s ease;
}

.summary-card:hover .summary-icon {
  transform: scale(1.05);
  opacity: 1;
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

/* Section Export */
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

/* Boutons */
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

/* Notifications */
.notifications {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
}

.notification {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border-radius: 10px;
  color: white;
  font-weight: 600;
  min-width: 280px;
  max-width: 420px;
  backdrop-filter: blur(20px);
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.15);
  transform: translateX(100%);
  animation: slideInNotification 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards;
  pointer-events: all;
  position: relative;
  overflow: hidden;
}

.notification::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  background: rgba(255, 255, 255, 0.3);
}

@keyframes slideInNotification {
  to {
    transform: translateX(0);
  }
}

.notification-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.notification-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.notification-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.notification-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.notification.success {
  background: linear-gradient(135deg, rgba(39, 174, 96, 0.95) 0%, rgba(46, 204, 113, 0.95) 100%);
}

.notification.warning {
  background: linear-gradient(135deg, rgba(243, 156, 18, 0.95) 0%, rgba(230, 126, 34, 0.95) 100%);
}

.notification.error {
  background: linear-gradient(135deg, rgba(231, 76, 60, 0.95) 0%, rgba(192, 57, 43, 0.95) 100%);
}

.notification.info {
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.95) 0%, rgba(155, 89, 182, 0.95) 100%);
}

.notification-icon {
  font-size: 1.1rem;
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
  font-size: 0.9rem;
  line-height: 1.3;
}

.notification-close {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  padding: 3px;
  border-radius: 3px;
  transition: all 0.3s ease;
  font-size: 0.9rem;
  flex-shrink: 0;
}

.notification-close:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  transform: scale(1.05);
}

/* Animation d'apparition en cascade */
.step-container:nth-child(1) { animation-delay: 0.1s; }
.step-container:nth-child(2) { animation-delay: 0.15s; }
.step-container:nth-child(3) { animation-delay: 0.2s; }
.step-container:nth-child(4) { animation-delay: 0.25s; }

/* Animation au scroll */
.fade-in-up {
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-in-up.visible {
  opacity: 1;
  transform: translateY(0);
}

/* Loader avec shimmer */
.loading-shimmer {
  background: linear-gradient(90deg, 
    rgba(255, 255, 255, 0) 0%, 
    rgba(255, 255, 255, 0.15) 50%, 
    rgba(255, 255, 255, 0) 100%);
  background-size: 200px 100%;
  animation: shimmer 1.2s infinite;
}

@keyframes shimmer {
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: calc(200px + 100%) 0;
  }
}
</style>