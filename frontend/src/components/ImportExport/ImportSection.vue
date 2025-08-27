<script setup lang="ts">
import { ref, computed } from 'vue'
import FileUploadStep from '../ImportExport/FileUploadStep.vue'
import ProjectAssignmentStep from '../ImportExport/ProjectAssignementStep.vue'
import MappingConfigStep from '../ImportExport/MappingConfigStep.vue'
import ValidationStep from '../ImportExport/ValidationStep.vue'
import MappingConfigEditor from '../ImportExport/MappingConfigEditor.vue'

interface ProjetGlobal {
  id: number
  projet: string
  client: number
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
  FPack_number: string
  RobotLocationCode: string 
  Robot_Location_Code: string
  selectedProjetGlobal: number | null
  selectedSousProjet: number | null
  selectedFPackTemplate?: any 
  [key: string]: any
}

interface UnmatchedItem {
  id: string
  value: string
  column: string
  suggestions: any[]
  selectedMatch?: any
  type: 'subproject' | 'group'
}

// Nouvelle interface pour la configuration de mapping (JSON)
interface MappingConfig {
  name: string
  subproject_columns: Record<string, string>
  groups: Array<{
    group_name: string
    excel_column: string
  }>
}

// Props
const props = defineProps<{
  projetsGlobaux: ProjetGlobal[]
  clients: any[]
  fpackTemplates?: any[]
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

// Configuration de mapping JSON (importée depuis l'éditeur)
const emptyMappingConfig: MappingConfig = {
  name: '',
  subproject_columns: {},
  groups: []
}
const mappingConfig = ref<MappingConfig>(emptyMappingConfig)

const unmatchedItems = ref<UnmatchedItem[]>([])
const isImporting = ref(false)
const selectedClient = ref<number | null>(null)
const showConfigEditor = ref(false)

// Computed
const allFPacksHaveProject = computed(() => {
  return fpackList.value.every(fpack => 
    fpack.selectedProjetGlobal && fpack.selectedSousProjet
  )
})

const allFPacksConfigured = computed(() => {
  return fpackList.value.every(fpack => 
    fpack.selectedProjetGlobal && 
    fpack.selectedSousProjet && 
    fpack.selectedFPackTemplate
  )
})

const mappedColumnsCount = computed(() => {
  const subprojectCount = Object.keys(mappingConfig.value.subproject_columns || {}).length
  const groupsCount = (mappingConfig.value.groups || []).length
  return subprojectCount + groupsCount
})

const uniqueProjectCount = computed(() => {
  const projects = new Set(fpackList.value.map(f => f.selectedProjetGlobal).filter(Boolean))
  return projects.size
})

const canExecuteImport = computed(() => {
  return unmatchedItems.value.every(item => item.selectedMatch) &&
         allFPacksConfigured.value
})

// Methods
const onFileAnalyzed = (data: any) => {
  previewData.value = data.preview
  previewColumns.value = data.columns
  
  // Créer les objets FpackItem avec toutes les propriétés requises
  fpackList.value = data.preview.map((row: any) => ({
    FPack_number: row['FPack Number'] || '',
    Robot_Location_Code: row['Robot location code'] || '',
    selectedProjetGlobal: null,
    selectedSousProjet: null,
    selectedFPackTemplate: null,
    ...row
  } as FpackItem))
  
  importStep.value = 2
}

const toggleConfigEditor = () => {
  showConfigEditor.value = !showConfigEditor.value
}

// Handler pour recevoir la configuration de mapping depuis l'éditeur
const onMappingConfigFromEditor = (config: MappingConfig) => {
  mappingConfig.value = config || emptyMappingConfig
  emit('addNotification', 'success', `Configuration "${config.name}" appliquée avec succès`)
  showConfigEditor.value = false
}

const onProjectsAssigned = () => {
  importStep.value = 3
}

const onMappingConfigured = async (payload: { jsonConfig: any, fileName: string, fileSize: number }) => {

  mappingConfig.value = payload.jsonConfig || emptyMappingConfig
  emit('addNotification', 'success', `Configuration "${payload.fileName}" appliquée avec succès`)
  showConfigEditor.value = false

  const incompletePacksCount = fpackList.value.filter(f => 
    !f.selectedProjetGlobal || !f.selectedSousProjet || !f.selectedFPackTemplate
  ).length

  if (incompletePacksCount > 0) {
    console.log('Incomplete packs:', incompletePacksCount)
    emit('addNotification', 'error', `${incompletePacksCount} F-Pack(s) ne sont pas entièrement configurés`)
    return
  }

  if (!mappingConfig.value || !mappingConfig.value.name) {
    console.log(mappingConfig.value)
    emit('addNotification', 'error', 'Configuration de mapping manquante')
    return
  }

  try {
    // Préparer les configurations F-Pack
    const fpackConfigurations = fpackList.value.map(fpack => ({
      selectedProjetGlobal: fpack.selectedProjetGlobal,
      selectedSousProjet: fpack.selectedSousProjet, 
      selectedFPackTemplate: fpack.selectedFPackTemplate,
      clientId: getClientIdFromProjet(fpack.selectedProjetGlobal)
    }))

    // Vérifier que tous les F-Packs ont un client valide
    const invalidConfigs = fpackConfigurations.filter(config => !config.clientId)
    if (invalidConfigs.length > 0) {
      emit('addNotification', 'error', `${invalidConfigs.length} F-Pack(s) n'ont pas de client valide`)
      return
    }

    const requestData = {
      preview_data: previewData.value,
      mapping_config: mappingConfig.value, // Configuration JSON complète
      fpack_configurations: fpackConfigurations
    }
    
    console.log('Sending request data:', requestData)
    
    const response = await fetch('http://localhost:8000/import/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData)
    })
    
    const result = await response.json()
    console.log("Preview result:", result)
    
    if (result.success) {
      unmatchedItems.value = result.unmatched_items || []
      importStep.value = 4
      
      const clientsCount = result.summary?.clients_count || 0
      const templatesCount = result.summary?.templates_used?.length || 0
      
      if (clientsCount > 1) {
        emit('addNotification', 'success', 
          `Prévisualisation générée avec succès! ${clientsCount} clients et ${templatesCount} templates traités.`)
      } else {
        emit('addNotification', 'success', 'Prévisualisation générée avec succès')
      }
    } else {
      emit('addNotification', 'error', result.detail || 'Erreur lors de la prévisualisation')
    }
  } catch (error) {
    emit('addNotification', 'error', 'Erreur lors de la prévisualisation')
    console.error('Error:', error)
  }
}

// Fonction utilitaire pour récupérer l'ID du client depuis un projet
const getClientIdFromProjet = (projetGlobalId: number | null): number | null => {
  if (!projetGlobalId) return null
  const projet = props.projetsGlobaux.find(p => p.id === projetGlobalId)
  return projet?.client || null
}

// Handler pour mettre à jour un élément non matché
const updateUnmatchedItem = (itemId: string, selectedMatch: any) => {
  const item = unmatchedItems.value.find(item => item.id === itemId)
  if (item) {
    item.selectedMatch = selectedMatch
  }
}

// Exécution de l'import avec la configuration finale
const executeImport = async (finalMappingConfig: MappingConfig) => {
  const incompletePacksCount = fpackList.value.filter(f => 
    !f.selectedProjetGlobal || !f.selectedSousProjet || !f.selectedFPackTemplate
  ).length

  if (incompletePacksCount > 0) {
    emit('addNotification', 'error', `${incompletePacksCount} F-Pack(s) ne sont pas entièrement configurés`)
    return
  }

  isImporting.value = true
  try {
    // Préparer les correspondances manuelles
    const manualMatches = unmatchedItems.value
      .filter(item => item.selectedMatch)
      .map(item => {
        // Extraire l'index de la ligne depuis l'ID
        const parts = item.id.split('_')
        return {
          row_index: parseInt(parts[0]),
          column: item.column,
          selectedMatch: item.selectedMatch
        }
      })

    // Préparer les configurations F-Pack
    const fpackConfigurations = fpackList.value.map(fpack => ({
      selectedProjetGlobal: fpack.selectedProjetGlobal,
      selectedSousProjet: fpack.selectedSousProjet, 
      selectedFPackTemplate: fpack.selectedFPackTemplate,
      clientId: getClientIdFromProjet(fpack.selectedProjetGlobal)
    }))

    // Vérifier que tous les F-Packs ont un client valide
    const invalidConfigs = fpackConfigurations.filter(config => !config.clientId)
    if (invalidConfigs.length > 0) {
      emit('addNotification', 'error', `${invalidConfigs.length} F-Pack(s) n'ont pas de client valide`)
      return
    }

    const requestData = {
      file_data: previewData.value,
      mapping_config: finalMappingConfig, // Configuration finale avec les résolutions manuelles
      fpack_configurations: fpackConfigurations,
      manual_matches: manualMatches
    }
    
    console.log('Executing import with data:', requestData)
    
    const response = await fetch('http://localhost:8000/import/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData)
    })
    
    const result = await response.json()
    console.log('Import result:', result)
    
    if (result.success) {
      const stats = result.results || {}
      let message = `Import réalisé avec succès!`
      
      if (stats.created_fpacks) {
        message += ` ${stats.created_fpacks} F-Packs créés.`
      }
      
      if (stats.created_selections) {
        message += ` ${stats.created_selections} sélections ajoutées.`
      }
      
      if (stats.warnings && stats.warnings.length > 0) {
        message += ` ${stats.warnings.length} avertissements.`
      }
      
      emit('addNotification', 'success', message)
      resetImport()
    } else {
      let errorMessage = result.detail || 'Erreur lors de l\'import'
      
      if (result.results && result.results.errors) {
        errorMessage += ` (${result.results.errors.length} erreurs)`
      }
      
      emit('addNotification', 'error', errorMessage)
    }
  } catch (error) {
    emit('addNotification', 'error', 'Erreur lors de l\'import')
    console.error('Import error:', error)
  } finally {
    isImporting.value = false
  }
}

const resetImport = () => {
  selectedFile.value = null
  previewData.value = []
  previewColumns.value = []
  fpackList.value = []
  mappingConfig.value = emptyMappingConfig
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
    <!-- Configuration du mapping -->
    <div class="mapping-config-panel" v-show="showConfigEditor">
      <MappingConfigEditor 
        @mapping-configured="onMappingConfigFromEditor"
      />
    </div>

    <!-- Barre d'outils -->
    <div class="toolbar">
      <button 
        class="btn btn-config"
        :class="{ active: showConfigEditor }"
        @click="toggleConfigEditor"
      >
        <span class="icon">⚙️</span>
        Configuration Mapping
      </button>
    </div>

    <!-- Étapes d'import -->
    <div class="import-steps">
      <!-- Étape 1: Upload du fichier -->
      <FileUploadStep 
        :step="1"
        :active="importStep >= 1"
        :completed="importStep > 1"
        :visible="importStep === 1"
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
        :fpack-templates="props.fpackTemplates || []"
        :allFPacksHaveProject="allFPacksHaveProject"
        :allFPacksConfigured="allFPacksConfigured"
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
        :mapping-config="mappingConfig"
        @execute-import="executeImport"
        @previous-step="importStep = 3"
        @update-unmatched-item="updateUnmatchedItem"
      />
    </div>
  </div>
</template>

<style scoped>
.import-section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.mapping-config-panel {
  margin-bottom: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  background-color: #f9f9f9;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding: 16px;
  background-color: #f5f5f5;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.btn-config {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-config:hover {
  background-color: #f0f0f0;
}

.btn-config.active {
  background-color: #007bff;
  color: white;
  border-color: #007bff;
}

.config-loaded {
  color: #28a745;
  font-weight: bold;
}

.current-config {
  color: #495057;
  font-size: 14px;
  padding: 8px 12px;
  background-color: #e9ecef;
  border-radius: 4px;
  border: 1px solid #ced4da;
}

.import-steps {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>

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

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 15px 20px;
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.btn-config {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #6c5ce7, #a29bfe);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(108, 92, 231, 0.2);
}

.btn-config:hover {
  background: linear-gradient(135deg, #5f3dc4, #7950f2);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(108, 92, 231, 0.3);
}

.btn-config.active {
  background: linear-gradient(135deg, #fd79a8, #fdcb6e);
  box-shadow: 0 4px 12px rgba(253, 121, 168, 0.3);
}



.mapping-config-panel {
  margin-bottom: 20px;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>