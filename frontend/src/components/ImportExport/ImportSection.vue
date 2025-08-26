<script setup lang="ts">
import { ref, computed } from 'vue'
import FileUploadStep from '../ImportExport/FileUploadStep.vue'
import ProjectAssignmentStep from '../ImportExport/ProjectAssignementStep.vue'
import MappingConfigStep from '../ImportExport/MappingConfigStep.vue'
import ValidationStep from '../ImportExport/ValidationStep.vue'

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

interface UnmatchedItem {
  id: string
  value: string
  column: string
  suggestions: any[]
  selectedMatch?: any
}

// Props
const props = defineProps<{
  projetsGlobaux: ProjetGlobal[]
  clients: any[]
}>()

// Emits
const emit = defineEmits<{
  addNotification: [type: 'success' | 'warning' | 'error' | 'info', message: string]
}>()

// État
const importStep = ref(1)
const selectedFile = ref<File | null>(null)
const previewData = ref<any[]>([])
const previewColumns = ref<string[]>([])
const fpackList = ref<FpackItem[]>([])
const mappingConfig = ref<Record<string, any>>({})
const unmatchedItems = ref<UnmatchedItem[]>([])
const isImporting = ref(false)
const selectedClient = ref<number | null>(null)

// Configuration de mapping par défaut
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

// Computed
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

// Methods
const onFileAnalyzed = (data: any) => {
  previewData.value = data.preview
  previewColumns.value = data.columns
  
  fpackList.value = data.preview.map((row: any) => ({
    FPackNumber: row['FPack Number'] || '',
    RobotLocationCode: row['Robot location code'] || '',
    selectedProjetGlobal: null,
    selectedSousProjet: null,
    ...row
  }))
  
  mappingConfig.value = { ...defaultMappingConfig }
  importStep.value = 2
}

const onProjectsAssigned = () => {
  importStep.value = 3
}

const onMappingConfigured = async () => {
  if (!selectedClient.value) {
    emit('addNotification', 'error', 'Veuillez sélectionner un client')
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
      emit('addNotification', 'success', 'Prévisualisation générée avec succès')
    } else {
      emit('addNotification', 'error', result.detail || 'Erreur lors de la prévisualisation')
    }
  } catch (error) {
    emit('addNotification', 'error', 'Erreur lors de la prévisualisation')
    console.error(error)
  }
}

const executeImport = async () => {
  if (!selectedClient.value) {
    emit('addNotification', 'error', 'Veuillez sélectionner un client')
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
      emit('addNotification', 'success', `Import réalisé avec succès! ${result.results.created_projects} projets créés.`)
      resetImport()
    } else {
      emit('addNotification', 'error', result.detail || 'Erreur lors de l\'import')
    }
  } catch (error) {
    emit('addNotification', 'error', 'Erreur lors de l\'import')
    console.error(error)
  } finally {
    isImporting.value = false
  }
}

const resetImport = () => {
  selectedFile.value = null
  previewData.value = []
  previewColumns.value = []
  fpackList.value = []
  mappingConfig.value = {}
  unmatchedItems.value = []
  importStep.value = 1
}

const onProjetGlobalChange = (fpack: FpackItem) => {
  fpack.selectedSousProjet = null
}

const getAvailableSousProjets = (projetGlobalId: number | null) => {
  if (!projetGlobalId) return []
  const projet = props.projetsGlobaux.find(p => p.id === projetGlobalId)
  return projet?.sous_projets || []
}
</script>

<template>
  <div class="import-section">
    <!-- Étape 1: Upload du fichier -->
    <FileUploadStep 
        :step="1"
        :active="importStep >= 1"
        :completed="importStep > 1"
        :selected-file="selectedFile"
        @file-analyzed="onFileAnalyzed"
        @add-notification="emit('addNotification', $event.type, $event.message)"
        @update:selectedFile="selectedFile = $event"
    />

    <!-- Étape 2: Aperçu et sélection des projets -->
    <ProjectAssignmentStep 
      :step="2"
      :active="importStep >= 2"
      :completed="importStep > 2"
      :visible="importStep === 2"
      :preview-data="previewData"
      :preview-columns="previewColumns"
      :fpack-list="fpackList"
      :projets-globaux="projetsGlobaux"
      :clients="clients"
      :allFPacksHaveProject="allFPacksHaveProject"
      v-model:selectedClient="selectedClient"
      @projet-global-change="onProjetGlobalChange"
      @projects-assigned="onProjectsAssigned"
      @previous-step="importStep = 1"
      @get-available-sous-projets="getAvailableSousProjets"
    />

    <!-- Étape 3: Configuration du mapping -->
    <MappingConfigStep 
      :step="3"
      :active="importStep >= 3"
      :completed="importStep > 3"
      :visible="importStep === 3"
      :mapping-config="mappingConfig"
      :preview-columns="previewColumns"
      :mapped-columns-count="mappedColumnsCount"
      :unique-project-count="uniqueProjectCount"
      @mapping-configured="onMappingConfigured"
      @previous-step="importStep = 2"
    />

    <!-- Étape 4: Prévisualisation et validation -->
    <ValidationStep 
      :step="4"
      :active="importStep >= 4"
      :visible="importStep === 4"
      :unmatched-items="unmatchedItems"
      :fpack-list="fpackList"
      :unique-project-count="uniqueProjectCount"
      :mapped-columns-count="mappedColumnsCount"
      :can-execute-import="canExecuteImport"
      :is-importing="isImporting"
      @execute-import="executeImport"
      @previous-step="importStep = 3"
    />
  </div>
</template>

<style scoped>
.import-section {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 30px 32px 60px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  scroll-behavior: smooth;
}

.import-section::-webkit-scrollbar {
  width: 8px;
}

.import-section::-webkit-scrollbar-track {
  background: rgba(189, 195, 199, 0.2);
  border-radius: 4px;
}

.import-section::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #3498db, #9b59b6);
  border-radius: 4px;
}

.import-section::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #2980b9, #8e44ad);
}
</style>