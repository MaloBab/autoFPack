<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'

// Types
interface Client {
  id: number
  nom: string
}

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
  fpacks?: SousProjetFpack[]
}

interface SousProjetFpack {
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

interface ExportValidationResponse {
  valid: boolean
  errors: string[]
  warnings: string[]
  summary: {
    requested_fpacks: number
    existing_fpacks: number
    fpacks_with_data: number
    missing_fpacks: number
  }
}

// Props
const props = defineProps<{
  projetsGlobaux: ProjetGlobal[],
  clients: Client[]
}>()


// Emits
const emit = defineEmits<{
  'add-notification': [type: 'success' | 'warning' | 'error' | 'info', message: string]
}>()

// État local
const loading = ref(false)
const isExporting = ref(false)
const isValidating = ref(false)
const selectedClientFilter = ref<number | string>('')
const exportValidation = ref<ExportValidationResponse | null>(null)

// États de sélection
const selectedFpacks = ref(new Set<number>())
const expandedProjets = ref(new Set<number>())
const expandedSousProjets = ref(new Set<number>())

// Configuration API
const API_BASE_URL = 'http://localhost:8000'

// Computed
const filteredProjets = computed(() => {
  if (!selectedClientFilter.value) {
    return props.projetsGlobaux
  }
  return props.projetsGlobaux.filter(p => p.client === Number(selectedClientFilter.value))
})

const totalSelectedFpacks = computed(() => {
  return selectedFpacks.value.size
})

// Méthodes utilitaires
const getClientName = (clientId: number): string => {
  const client = props.clients.find(c => c.id === clientId)
  return client ? client.nom : `Client ${clientId}`
}

const getTotalFpacksForProjet = (projet: ProjetGlobal): number => {
  return projet.sous_projets?.reduce((total, sp) => total + (sp.fpacks?.length || 0), 0) || 0
}

// Méthodes de sélection - Projets
const isProjetSelected = (projetId: number): boolean => {
  const projet = props.projetsGlobaux.find(p => p.id === projetId)
  if (!projet?.sous_projets) return false
  
  const allFpackIds = getAllFpackIds(projet)
  return allFpackIds.length > 0 && allFpackIds.every(id => selectedFpacks.value.has(id))
}

const isProjetIndeterminate = (projetId: number): boolean => {
  const projet = props.projetsGlobaux.find(p => p.id === projetId)
  if (!projet?.sous_projets) return false
  
  const allFpackIds = getAllFpackIds(projet)
  const selectedCount = allFpackIds.filter(id => selectedFpacks.value.has(id)).length
  
  return selectedCount > 0 && selectedCount < allFpackIds.length
}

const toggleProjetSelection = (projetId: number) => {
  const projet = props.projetsGlobaux.find(p => p.id === projetId)
  if (!projet?.sous_projets) return
  
  const allFpackIds = getAllFpackIds(projet)
  const shouldSelect = !isProjetSelected(projetId)
  
  if (shouldSelect) {
    allFpackIds.forEach(id => selectedFpacks.value.add(id))
  } else {
    allFpackIds.forEach(id => selectedFpacks.value.delete(id))
  }
}

// Méthodes de sélection - Sous-projets
const isSousProjetSelected = (sousProjetId: number): boolean => {
  const sousProjet = findSousProjet(sousProjetId)
  if (!sousProjet?.fpacks) return false
  
  const fpackIds = sousProjet.fpacks.map(f => f.id)
  return fpackIds.length > 0 && fpackIds.every(id => selectedFpacks.value.has(id))
}

const isSousProjetIndeterminate = (sousProjetId: number): boolean => {
  const sousProjet = findSousProjet(sousProjetId)
  if (!sousProjet?.fpacks) return false
  
  const fpackIds = sousProjet.fpacks.map(f => f.id)
  const selectedCount = fpackIds.filter(id => selectedFpacks.value.has(id)).length
  
  return selectedCount > 0 && selectedCount < fpackIds.length
}

const toggleSousProjetSelection = (sousProjetId: number) => {
  const sousProjet = findSousProjet(sousProjetId)
  if (!sousProjet?.fpacks) return
  
  const fpackIds = sousProjet.fpacks.map(f => f.id)
  const shouldSelect = !isSousProjetSelected(sousProjetId)
  
  if (shouldSelect) {
    fpackIds.forEach(id => selectedFpacks.value.add(id))
  } else {
    fpackIds.forEach(id => selectedFpacks.value.delete(id))
  }
}

// Méthodes de sélection - F-Packs
const toggleFpackSelection = (fpackId: number) => {
  if (selectedFpacks.value.has(fpackId)) {
    selectedFpacks.value.delete(fpackId)
  } else {
    selectedFpacks.value.add(fpackId)
  }
}

// Méthodes d'expansion/contraction
const toggleProjet = (projetId: number) => {
  if (expandedProjets.value.has(projetId)) {
    expandedProjets.value.delete(projetId)
  } else {
    expandedProjets.value.add(projetId)
  }
}

const toggleSousProjet = (sousProjetId: number) => {
  if (expandedSousProjets.value.has(sousProjetId)) {
    expandedSousProjets.value.delete(sousProjetId)
  } else {
    expandedSousProjets.value.add(sousProjetId)
  }
}

// Méthodes de contrôle globales
const selectAll = () => {
  const allFpackIds = getAllFpackIdsFromProjets(filteredProjets.value)
  allFpackIds.forEach(id => selectedFpacks.value.add(id))
}

const deselectAll = () => {
  selectedFpacks.value.clear()
  exportValidation.value = null
}

// Méthodes utilitaires
const getAllFpackIds = (projet: ProjetGlobal): number[] => {
  const ids: number[] = []
  projet.sous_projets?.forEach(sp => {
    sp.fpacks?.forEach(f => ids.push(f.id))
  })
  return ids
}

const getAllFpackIdsFromProjets = (projets: ProjetGlobal[]): number[] => {
  const ids: number[] = []
  projets.forEach(projet => {
    ids.push(...getAllFpackIds(projet))
  })
  return ids
}

const findSousProjet = (sousProjetId: number): SousProjet | undefined => {
  for (const projet of props.projetsGlobaux) {
    const sousProjet = projet.sous_projets?.find(sp => sp.id === sousProjetId)
    if (sousProjet) return sousProjet
  }
  return undefined
}

const getSelectedProjetsCount = (): number => {
  const selectedProjetIds = new Set<number>()
  
  for (const fpackId of selectedFpacks.value) {
    const projet = findProjetByFpackId(fpackId)
    if (projet) {
      selectedProjetIds.add(projet.id)
    }
  }
  
  return selectedProjetIds.size || 0
}

const findProjetByFpackId = (fpackId: number): ProjetGlobal | undefined => {
  for (const projet of props.projetsGlobaux) {
    for (const sousProjet of projet.sous_projets || []) {
      if (sousProjet.fpacks?.some(f => f.id === fpackId)) {
        return projet
      }
    }
  }
  return undefined
}

// Nouvelles méthodes pour l'intégration backend
const validateExportRequest = async (): Promise<boolean> => {
  if (selectedFpacks.value.size === 0) {
    emit('add-notification', 'warning', 'Aucun F-Pack sélectionné pour la validation')
    return false
  }
  
  isValidating.value = true
  try {
    const response = await axios.post(`${API_BASE_URL}/export/fpack-matrix/validate`, {
      fpack_ids: Array.from(selectedFpacks.value)
    })
    
    exportValidation.value = response.data
    
    // Affichage des messages de validation
    if (response.data.errors.length > 0) {
      response.data.errors.forEach((error: string) => {
        emit('add-notification', 'error', error)
      })
      return false
    }
    
    if (response.data.warnings.length > 0) {
      response.data.warnings.forEach((warning: string) => {
        emit('add-notification', 'warning', warning)
      })
    }
    
    if (response.data.valid) {
      emit('add-notification', 'info', 
        `Validation réussie: ${response.data.summary.fpacks_with_data} F-Packs prêts pour l'export`
      )
    }
    
    return response.data.valid
    
  } catch (error: any) {
    console.error('Erreur lors de la validation:', error)
    const errorMessage = error.response?.data?.detail || 'Erreur lors de la validation'
    emit('add-notification', 'error', errorMessage)
    exportValidation.value = null
    return false
  } finally {
    isValidating.value = false
  }
}

// Export avec validation intégrée
const executeExport = async () => {
  if (selectedFpacks.value.size === 0) {
    emit('add-notification', 'warning', 'Aucun F-Pack sélectionné pour l\'export')
    return
  }
  
  // Validation avant export si pas déjà fait
  if (!exportValidation.value) {
    const isValid = await validateExportRequest()
    if (!isValid) {
      return
    }
  }
  
  isExporting.value = true
  try {
    const response = await axios.post(`${API_BASE_URL}/export/fpack-matrix`, {
      fpack_ids: Array.from(selectedFpacks.value)
    }, {
      responseType: 'blob',
      timeout: 300000 // 5 minutes timeout pour les gros exports
    })
    
    // Extraction du nom de fichier depuis les en-têtes si disponible
    const contentDisposition = response.headers['content-disposition']
    let filename = `fpack-matrix-export-${new Date().toISOString().slice(0, 10)}.xlsx`
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename=([^;]+)/)
      if (filenameMatch) {
        filename = filenameMatch[1].replace(/['"]/g, '')
      }
    }
    
    // Téléchargement du fichier
    const blob = new Blob([response.data], { 
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
    })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
    // Message de succès avec détails
    const validationSummary = exportValidation.value?.summary
    const successMessage = validationSummary 
      ? `Export réalisé avec succès: ${validationSummary.fpacks_with_data} F-Packs exportés`
      : `Export réalisé avec succès pour ${selectedFpacks.value.size} F-Packs`
    
    emit('add-notification', 'success', successMessage)
    
  } catch (error: any) {
    console.error('Erreur lors de l\'export:', error)
    
    let errorMessage = 'Erreur lors de l\'export'
    if (error.response?.data) {
      try {
        // Tentative de lecture du message d'erreur depuis le blob
        const errorText = await error.response.data.text()
        const errorData = JSON.parse(errorText)
        errorMessage = errorData.detail || errorMessage
      } catch {
        errorMessage = error.response?.statusText || errorMessage
      }
    }
    
    emit('add-notification', 'error', errorMessage)
  } finally {
    isExporting.value = false
  }
}

// Méthode pour prévisualiser les données d'un F-Pack
const previewFpackData = async (fpackId: number) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/export/fpack-matrix/preview/${fpackId}`)
    return response.data
  } catch (error: any) {
    console.error('Erreur lors de l\'aperçu:', error)
    emit('add-notification', 'error', 'Erreur lors de la génération de l\'aperçu')
    return null
  }
}

// Méthode pour récupérer les statistiques d'export
const loadExportStats = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/export/fpack-matrix/stats`)
    return response.data.stats
  } catch (error: any) {
    console.error('Erreur lors du chargement des statistiques:', error)
    return null
  }
}

// Surveillance des changements avec réinitialisation de la validation
watch(selectedClientFilter, () => {
  selectedFpacks.value.clear()
  exportValidation.value = null
})

watch(selectedFpacks, () => {
  // Réinitialiser la validation si la sélection change
  exportValidation.value = null
}, { deep: true })

// Gestion des erreurs d'axios globales
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.code === 'ECONNABORTED') {
      emit('add-notification', 'error', 'Timeout: L\'opération a pris trop de temps')
    } else if (error.response?.status === 413) {
      emit('add-notification', 'error', 'Erreur: Trop de données sélectionnées')
    }
    return Promise.reject(error)
  }
)
</script>

<template>
  <div class="export-container">
    <!-- En-tête avec titre et statistiques -->
    <div class="export-header">
      <div class="header-content">
        <div class="title-section">
          <h2 class="export-title">
            <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7,10 12,15 17,10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Export F-Pack Matrix
          </h2>
          <p class="export-subtitle">Sélectionnez les éléments à exporter au format Excel</p>
        </div>
        
        <div class="stats-overview">
          <div class="stat-card">
            <div class="stat-number">{{ totalSelectedFpacks }}</div>
            <div class="stat-label">F-Packs sélectionnés</div>
          </div>
          <div class="stat-card validation" v-if="exportValidation">
            <div class="stat-number">{{ exportValidation.summary.fpacks_with_data }}</div>
            <div class="stat-label">Avec données</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Contrôles de sélection -->
    <div class="selection-controls">
      <div class="control-group">
        <button 
          class="control-btn primary"
          @click="selectAll"
          :disabled="isExporting || isValidating"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <polyline points="9,11 12,14 22,4"/>
            <path d="M21,12v7a2,2 0 0,1 -2,2H5a2,2 0 0,1 -2,-2V5a2,2 0 0,1 2,-2h11"/>
          </svg>
          Tout sélectionner
        </button>
        
        <button 
          class="control-btn secondary"
          @click="deselectAll"
          :disabled="isExporting || isValidating"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
          </svg>
          Tout désélectionner
        </button>

        <button 
          class="control-btn info"
          @click="validateExportRequest"
          :disabled="isExporting || isValidating || totalSelectedFpacks === 0"
          v-if="totalSelectedFpacks > 0 && !exportValidation"
        >
          <div v-if="isValidating" class="loading-content">
            <div class="loading-spinner small"></div>
            <span>Validation...</span>
          </div>
          <div v-else class="button-content">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <polyline points="9,11 12,14 22,4"/>
            </svg>
            Valider la sélection
          </div>
        </button>
      </div>

      <!-- Filtre par client -->
      <div class="filter-section">
        <label class="filter-label">Filtrer par client :</label>
        <select 
          v-model="selectedClientFilter" 
          class="filter-select"
          :disabled="isExporting || isValidating"
        >
          <option value="">Tous les clients</option>
          <option 
            v-for="client in clients" 
            :key="client.id" 
            :value="client.id"
          >
            {{ client.nom }}
          </option>
        </select>
      </div>
    </div>

    <!-- Message de validation -->
    <div v-if="exportValidation && exportValidation.warnings.length > 0" class="validation-warnings">
      <div class="warning-header">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
          <path d="M12 9v4"/>
          <path d="m12 17 .01 0"/>
        </svg>
        <span>Avertissements de validation</span>
      </div>
      <ul class="warning-list">
        <li v-for="warning in exportValidation.warnings" :key="warning">
          {{ warning }}
        </li>
      </ul>
    </div>

    <!-- Arborescence des projets -->
    <div class="projects-tree" v-if="!loading">
      <div 
        v-for="projet in filteredProjets" 
        :key="projet.id" 
        class="project-node"
      >
        <!-- Projet Global -->
        <div class="tree-item project-item">
          <div class="item-content" @click="toggleProjet(projet.id)">
            <div class="expand-icon" :class="{ expanded: expandedProjets.has(projet.id) }">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <polyline points="9,18 15,12 9,6"/>
              </svg>
            </div>
            
            <div class="checkbox-wrapper">
              <input
                type="checkbox"
                :checked="isProjetSelected(projet.id)"
                :indeterminate.prop="isProjetIndeterminate(projet.id)"
                @change="toggleProjetSelection(projet.id)"
                @click.stop
                :disabled="isExporting || isValidating"
              />
            </div>
            
            <div class="item-info">
              <div class="item-icon project-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                  <polyline points="9,22 9,12 15,12 15,22"/>
                </svg>
              </div>
              <div class="item-details">
                <h4 class="item-title">{{ projet.projet }}</h4>
                <p class="item-subtitle">Client: {{ getClientName(projet.client) }}</p>
              </div>
            </div>
            
            <div class="item-stats">
              <span class="stat-badge">
                {{ projet.sous_projets?.length || 0 }} sous-projets
              </span>
              <span class="stat-badge">
                {{ getTotalFpacksForProjet(projet) }} F-Packs
              </span>
            </div>
          </div>
          
          <!-- Sous-projets -->
          <div v-if="expandedProjets.has(projet.id)" class="tree-children">
            <div
              v-for="sousProjet in projet.sous_projets"
              :key="sousProjet.id"
              class="tree-item sous-project-item"
            >
              <div class="item-content" @click="toggleSousProjet(sousProjet.id)">
                <div class="expand-icon" :class="{ expanded: expandedSousProjets.has(sousProjet.id) }">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <polyline points="9,18 15,12 9,6"/>
                  </svg>
                </div>
                
                <div class="checkbox-wrapper">
                  <input
                    type="checkbox"
                    :checked="isSousProjetSelected(sousProjet.id)"
                    :indeterminate.prop="isSousProjetIndeterminate(sousProjet.id)"
                    @change="toggleSousProjetSelection(sousProjet.id)"
                    @click.stop
                    :disabled="isExporting || isValidating"
                  />
                </div>
                
                <div class="item-info">
                  <div class="item-icon sous-project-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                      <line x1="16" y1="2" x2="16" y2="6"/>
                      <line x1="8" y1="2" x2="8" y2="6"/>
                      <line x1="3" y1="10" x2="21" y2="10"/>
                    </svg>
                  </div>
                  <div class="item-details">
                    <h5 class="item-title">{{ sousProjet.nom }}</h5>
                    <p class="item-subtitle">{{ sousProjet.fpacks?.length || 0 }} F-Packs</p>
                  </div>
                </div>
              </div>
              
              <!-- F-Packs -->
              <div v-if="expandedSousProjets.has(sousProjet.id)" class="tree-children">
                <div
                  v-for="fpack in sousProjet.fpacks"
                  :key="fpack.id"
                  class="tree-item fpack-item"
                >
                  <div class="item-content">
                    <div class="checkbox-wrapper">
                      <input
                        type="checkbox"
                        :checked="selectedFpacks.has(fpack.id)"
                        @change="toggleFpackSelection(fpack.id)"
                        @click.stop
                        :disabled="isExporting || isValidating"
                      />
                    </div>
                    
                    <div class="item-info">
                      <div class="item-icon fpack-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <rect x="3" y="3" width="18" height="18" rx="2"/>
                          <rect x="7" y="8" width="10" height="8" rx="1"/>
                          <path d="M10 6v2"/>
                          <path d="M14 6v2"/>
                        </svg>
                      </div>
                      <div class="item-details">
                        <h6 class="item-title">{{ fpack.FPack_number || 'F-Pack sans numéro' }}</h6>
                        <p class="item-subtitle">
                          {{ fpack.Robot_Location_Code || 'Emplacement non défini' }}
                          <span v-if="fpack.contractor" class="contractor-info">
                            • {{ fpack.contractor }}
                          </span>
                        </p>
                      </div>
                    </div>
                    
                    <div class="item-actions">
                      <span 
                        class="selection-badge"
                        :class="{ selected: selectedFpacks.has(fpack.id) }"
                        v-if="fpack.selections?.length"
                      >
                        {{ fpack.selections.length }} sélections
                      </span>
                      <button
                        v-if="selectedFpacks.has(fpack.id)"
                        class="preview-btn"
                        @click="previewFpackData(fpack.id)"
                        title="Aperçu des données"
                      >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                          <circle cx="12" cy="12" r="3"/>
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- État de chargement -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Chargement des projets...</p>
    </div>

    <!-- État vide -->
    <div v-if="!loading && filteredProjets.length === 0" class="empty-state">
      <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <circle cx="12" cy="12" r="10"/>
        <path d="M16 16s-1.5-2-4-2-4 2-4 2"/>
        <line x1="9" y1="9" x2="9.01" y2="9"/>
        <line x1="15" y1="9" x2="15.01" y2="9"/>
      </svg>
      <h3>Aucun projet trouvé</h3>
      <p>Aucun projet ne correspond aux critères de filtrage actuels.</p>
    </div>

    <!-- Actions d'export -->
    <div class="export-actions" v-if="totalSelectedFpacks > 0">
      <div class="export-summary">
        <h4>Résumé de l'export</h4>
        <div class="summary-details">
          <div class="detail-item">
            <span class="detail-label">F-Packs sélectionnés :</span>
            <span class="detail-value">{{ totalSelectedFpacks }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Projets concernés :</span>
            <span class="detail-value">{{ getSelectedProjetsCount() }}</span>
          </div>
          <div class="detail-item" v-if="exportValidation">
            <span class="detail-label">F-Packs avec données :</span>
            <span class="detail-value">{{ exportValidation.summary.fpacks_with_data }}</span>
          </div>
        </div>
        
        <!-- Affichage des avertissements de validation -->
        <div v-if="exportValidation && exportValidation.summary.missing_fpacks > 0" class="validation-info">
          <div class="info-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 16v-4"/>
              <path d="m12 8 .01 0"/>
            </svg>
            <span>{{ exportValidation.summary.missing_fpacks }} F-Packs non trouvés dans la base</span>
          </div>
        </div>
      </div>
      
      <button
        class="export-btn"
        @click="executeExport"
        :disabled="!!(isExporting || isValidating || totalSelectedFpacks === 0 || (exportValidation && !exportValidation.valid))"
      >
        <div v-if="isExporting" class="export-loading">
          <div class="loading-spinner small"></div>
          <span>Export en cours...</span>
        </div>
        <div v-else class="export-content">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7,10 12,15 17,10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          <span>Exporter vers Excel</span>
        </div>
      </button>
    </div>
  </div>
</template>

<style scoped>
.export-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  overflow: hidden;
}

.export-header {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-bottom: 1px solid #e9ecef;
  padding: 32px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
}

.title-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.export-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.title-icon {
  width: 32px;
  height: 32px;
  stroke-width: 2.5;
  color: #3498db;
}

.export-subtitle {
  margin: 0;
  color: #6c757d;
  font-size: 1.1rem;
  font-weight: 500;
}

.stats-overview {
  display: flex;
  gap: 16px;
}

.stat-card {
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
  color: white;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
}

.stat-card.validation {
  background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
  box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);
}

.stat-number {
  font-size: 1.8rem;
  font-weight: 800;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.9;
  font-weight: 500;
}

.selection-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 32px;
  background: white;
  border-bottom: 1px solid #e9ecef;
}

.control-group {
  display: flex;
  gap: 12px;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  font-size: 0.95rem;
}

.control-btn svg {
  width: 18px;
  height: 18px;
  stroke-width: 2;
}

.control-btn.primary {
  background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(39, 174, 96, 0.3);
}

.control-btn.primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(39, 174, 96, 0.4);
}

.control-btn.secondary {
  background: white;
  color: #6c757d;
  border: 1px solid #dee2e6;
}

.control-btn.secondary:hover:not(:disabled) {
  background: #f8f9fa;
  border-color: #adb5bd;
}

.control-btn.info {
  background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(23, 162, 184, 0.3);
}

.control-btn.info:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(23, 162, 184, 0.4);
}

.control-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.loading-content, .button-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-label {
  font-weight: 600;
  color: #495057;
  font-size: 0.95rem;
}

.filter-select {
  padding: 10px 16px;
  border: 1px solid #ced4da;
  color: #000;
  border-radius: 6px;
  font-size: 0.95rem;
  background: white;
  cursor: pointer;
  min-width: 200px;
}

.filter-select:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.filter-select:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
  opacity: 0.6;
}

.validation-warnings {
  background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
  border: 1px solid #ffc107;
  margin: 16px 32px;
  border-radius: 8px;
  padding: 16px;
}

.warning-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #856404;
  margin-bottom: 8px;
}

.warning-header svg {
  width: 20px;
  height: 20px;
  color: #ffc107;
}

.warning-list {
  margin: 0;
  padding-left: 20px;
  color: #856404;
}

.warning-list li {
  margin-bottom: 4px;
  font-size: 0.9rem;
}

.projects-tree {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
}

.project-node {
  margin-bottom: 16px;
}

.tree-item {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  border: 1px solid #e9ecef;
}

.tree-item:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.item-content {
  display: flex;
  align-items: center;
  padding: 20px;
  cursor: pointer;
  gap: 16px;
}

.expand-icon {
  width: 20px;
  height: 20px;
  color: #6c757d;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.expand-icon svg {
  width: 100%;
  height: 100%;
}

.checkbox-wrapper input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: #3498db;
  cursor: pointer;
}

.checkbox-wrapper input[type="checkbox"]:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.item-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.item-icon {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.project-icon {
  color: #e74c3c;
}

.sous-project-icon {
  color: #f39c12;
}

.fpack-icon {
  color: #3498db;
}

.item-details {
  flex: 1;
  min-width: 0;
}

.item-title {
  margin: 0 0 4px 0;
  font-weight: 600;
  color: #2c3e50;
  font-size: 1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-subtitle {
  margin: 0;
  color: #6c757d;
  font-size: 0.85rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.contractor-info {
  font-weight: 500;
}

.item-stats {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.stat-badge {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  color: #495057;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 0.8rem;
  font-weight: 600;
  border: 1px solid #e9ecef;
}

.item-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selection-badge {
  background: #f8f9fa;
  color: #6c757d;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.selection-badge.selected {
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
  color: white;
}

.preview-btn {
  background: none;
  border: 1px solid #dee2e6;
  color: #6c757d;
  padding: 6px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-btn:hover {
  border-color: #3498db;
  color: #3498db;
}

.preview-btn svg {
  width: 16px;
  height: 16px;
}

.tree-children {
  padding-left: 60px;
  padding-right: 20px;
  padding-bottom: 12px;
}

.tree-children .tree-item {
  margin-bottom: 8px;
  border-left: 2px solid #e9ecef;
  margin-left: 20px;
  border-radius: 0 12px 12px 0;
}

.sous-project-item {
  background: linear-gradient(135deg, #fff9e6 0%, #ffffff 100%);
}

.fpack-item {
  background: linear-gradient(135deg, #f0f8ff 0%, #ffffff 100%);
}

.fpack-item .item-content {
  padding: 16px 20px;
}

.fpack-item .item-title {
  font-size: 0.9rem;
}

.fpack-item .item-subtitle {
  font-size: 0.8rem;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: #6c757d;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

.loading-spinner.small {
  width: 20px;
  height: 20px;
  border-width: 2px;
  margin: 0;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-icon {
  width: 64px;
  height: 64px;
  color: #adb5bd;
  margin-bottom: 16px;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  color: #495057;
  font-size: 1.2rem;
}

.empty-state p {
  margin: 0;
  color: #6c757d;
}

.export-actions {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-top: 1px solid #e9ecef;
  padding: 24px 32px;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.05);
}

.export-summary {
  margin-bottom: 20px;
}

.export-summary h4 {
  margin: 0 0 12px 0;
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
}

.summary-details {
  display: flex;
  gap: 24px;
  margin-bottom: 12px;
}

.detail-item {
  display: flex;
  gap: 8px;
}

.detail-label {
  color: #6c757d;
  font-weight: 500;
}

.detail-value {
  color: #2c3e50;
  font-weight: 700;
}

.validation-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #856404;
  font-size: 0.9rem;
}

.info-item svg {
  width: 16px;
  height: 16px;
  color: #ffc107;
}

.export-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px 32px;
  background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
  width: auto;
  min-width: 200px;
}

.export-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(231, 76, 60, 0.4);
}

.export-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.export-loading,
.export-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.export-content svg {
  width: 20px;
  height: 20px;
  stroke-width: 2;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .export-container {
    padding: 0 16px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 20px;
    align-items: flex-start;
  }
  
  .projects-tree {
    padding: 16px 0;
  }
  
  .tree-children {
    padding-left: 40px;
  }
}

@media (max-width: 768px) {
  .export-title {
    font-size: 1.5rem;
  }
  
  .title-icon {
    width: 24px;
    height: 24px;
  }
  
  .selection-controls {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .control-group {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .filter-section {
    justify-content: center;
  }
  
  .filter-select {
    min-width: auto;
    width: 100%;
    max-width: 300px;
  }
  
  .summary-details {
    flex-direction: column;
    gap: 8px;
  }
  
  .item-stats {
    flex-direction: column;
    gap: 4px;
  }
  
  .tree-children {
    padding-left: 20px;
  }
  
  .validation-warnings {
    margin: 16px;
  }
}

/* Scrollbar personnalisée */
.projects-tree::-webkit-scrollbar {
  width: 8px;
}

.projects-tree::-webkit-scrollbar-track {
  background: rgba(233, 236, 239, 0.3);
  border-radius: 4px;
}

.projects-tree::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #3498db, #2980b9);
  border-radius: 4px;
}

.projects-tree::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #2980b9, #1c5aa0);
}

/* Animations d'entrée */
.project-node {
  animation: slideInUp 0.3s ease-out;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.tree-children {
  animation: slideInLeft 0.2s ease-out;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* États focus et accessibilité */
.control-btn:focus,
.filter-select:focus,
.export-btn:focus,
.preview-btn:focus {
  outline: 2px solid #3498db;
  outline-offset: 2px;
}

.checkbox-wrapper input[type="checkbox"]:focus {
  outline: 2px solid #3498db;
  outline-offset: 2px;
}

/* Indicateurs de sélection */
.tree-item.selected {
  border-left-color: #27ae60;
  border-left-width: 4px;
}

.item-content:focus-within {
  background: rgba(52, 152, 219, 0.05);
}

/* États de désactivation pour préserver l'UX */
.export-container.loading * {
  pointer-events: none;
}

.export-container.loading .loading-state {
  pointer-events: all;
}
</style>