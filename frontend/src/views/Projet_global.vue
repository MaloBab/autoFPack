<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useProjets } from '../composables/useProjets'
import PageHeader from '../components/Interaction/PageHeader.vue'
import ProjetGlobalCard from '../components/Projets/ProjetGlobalCard.vue'
import TextSearch from '../components/Searching/TextSearch.vue'
import { showToast } from '../composables/useToast'
import { useLoading } from '../composables/useLoading'
import axios from 'axios'

interface SousProjet {
  id: number
  nom: string
  description?: string
  id_global: number
}

const { startLoading, stopLoading } = useLoading()
const router = useRouter()

const {
  projetsGlobaux,
  loading,
  globalStats,
  fetchProjetsGlobaux,
  createProjetGlobal,
  createProjet,
  deleteProjetGlobal,
  deleteProjet,
  searchProjetsGlobaux,
  updateProjetGlobal
} = useProjets()

async function createSousProjet(sousProjetData: { nom: string; description: string; id_global?: number | null }) {
  try {
    const response = await axios.post('http://localhost:8000/sous_projets', sousProjetData)
    showToast('Sous-projet créé avec succès', '#10b981')
    await fetchProjetsGlobaux(true)
    return response.data
  } catch (error: any) {
    throw error
  }
}

async function deleteSousProjet(sousProjetId: number) {
  try {
    await axios.delete(`http://localhost:8000/sous_projets/${sousProjetId}`)
    showToast('Sous-projet supprimé avec succès', '#10b981')
    await fetchProjetsGlobaux(true)
  } catch (error: any) {
    throw error
  }
}

async function updateSousProjet(sousProjetId: number, updateData: { nom: string; description?: string }) {
  try {
    const response = await axios.put(`http://localhost:8000/sous_projets/${sousProjetId}`, updateData)
    showToast('Sous-projet modifié avec succès', '#10b981')
    await fetchProjetsGlobaux(true)
    return response.data
  } catch (error: any) {
    throw error
  }
}

const searchTerm = ref('')
const showAddGlobalModal = ref(false)
const showAddProjetModal = ref(false)
const showAddSousProjetModal = ref(false)
const showDeleteConfirmModal = ref(false)
const selectedGlobalId = ref<number | null>(null)
const selectedSousProjetId = ref<number | null>(null)
const itemToDelete = ref<{ type: 'global' | 'projet' | 'sous-projet', id: number, nom: string } | null>(null)
const allCardsExpanded = ref(true)

const newGlobal = ref({
  projet: '',
  sous_projet: '',
  client: null as number | null
})

const newProjet = ref({
  nom: '',
  fpack_id: null as number | null,
  id_global: null as number | null,
  id_sous_projet: null as number | null
})

const newSousProjet = ref({
  nom: '',
  description: '',
  id_global: null as number | null
})

const globalErrors = ref<Record<string, string>>({})
const projetErrors = ref<Record<string, string>>({})
const sousProjetErrors = ref<Record<string, string>>({})

const clients = ref<Array<{ id: number, nom: string }>>([])
const fpacks = ref<Array<{ id: number, nom: string, client: number }>>([])

const filteredProjetsTree = computed(() => {
  return searchProjetsGlobaux(searchTerm.value)
})

const fpacksForProjet = computed(() => {
  if (!selectedGlobalId.value) return []
  const pg = projetsGlobaux.value.find(pg => pg.id === selectedGlobalId.value)
  return pg ? fpacks.value.filter(f => f.client === pg.client) : []
})

const validateGlobalForm = (): boolean => {
  globalErrors.value = {}
  
  if (!newGlobal.value.projet.trim()) {
    globalErrors.value.projet = 'Le nom du projet est requis'
  }
  
  if (!newGlobal.value.client) {
    globalErrors.value.client = 'Le client est requis'
  }
  
  return Object.keys(globalErrors.value).length === 0
}

const validateProjetForm = (): boolean => {
  projetErrors.value = {}
  
  if (!newProjet.value.nom.trim()) {
    projetErrors.value.nom = 'Le nom du F-Pack est requis'
  }
  
  if (!newProjet.value.fpack_id) {
    projetErrors.value.fpack_id = 'Le FPack est requis'
  }
  
  return Object.keys(projetErrors.value).length === 0
}

const validateSousProjetForm = (): boolean => {
  sousProjetErrors.value = {}
  
  if (!newSousProjet.value.nom.trim()) {
    sousProjetErrors.value.nom = 'Le nom du sous-projet est requis'
  }
  
  return Object.keys(sousProjetErrors.value).length === 0
}

async function fetchData() {
  startLoading()
  try {
    const [clientsRes, fpacksRes] = await Promise.all([
      axios.get('http://localhost:8000/clients'),
      axios.get('http://localhost:8000/fpacks')
    ])
    
    clients.value = clientsRes.data
    fpacks.value = fpacksRes.data
    
    await fetchProjetsGlobaux(true)
  } catch (error) {
    console.error('Erreur lors du chargement:', error)
    showToast('Erreur lors du chargement des données', '#e71717ff')
  }
  finally {
    stopLoading()
  }
}

async function handleCreateProjetGlobal() {
  if (!validateGlobalForm()) return
  
  try {
    await createProjetGlobal(newGlobal.value)
    closeGlobalModal()
  } catch (error: any) {
    const message = error.response?.data?.detail || 'Erreur lors de la création'
    showToast(message, '#e71717ff')
  }
}

async function handleCreateProjet() {
  if (!validateProjetForm()) return
  
  try {
    await createProjet(newProjet.value)
    closeProjetModal()
  } catch (error: any) {
    const message = error.response?.data?.detail || 'Erreur lors de la création'
    showToast(message, '#e71717ff')
  }
}

async function handleCreateSousProjet() {
  if (!validateSousProjetForm()) return
  
  try {
    await createSousProjet(newSousProjet.value)
    closeSousProjetModal()
  } catch (error: any) {
    const message = error.response?.data?.detail || 'Erreur lors de la création'
    showToast(message, '#e71717ff')
  }
}

function onDeleteItem(type: 'global' | 'projet' | 'sous-projet', id: number, nom: string) {
  itemToDelete.value = { type, id, nom }
  showDeleteConfirmModal.value = true
}

async function confirmDelete() {
  if (!itemToDelete.value) return
  
  try {
    if (itemToDelete.value.type === 'global') {
      await deleteProjetGlobal(itemToDelete.value.id)
    } else if (itemToDelete.value.type === 'projet') {
      await deleteProjet(itemToDelete.value.id)
    } else if (itemToDelete.value.type === 'sous-projet') {
      await deleteSousProjet(itemToDelete.value.id)
    }
    showDeleteConfirmModal.value = false
    itemToDelete.value = null
  } catch (error: any) {
    const message = error.response?.data?.detail || 'Erreur lors de la suppression'
    showToast(message, '#e71717ff')
  }
}

function toggleAllCards() {
  allCardsExpanded.value = !allCardsExpanded.value
}

function openAddGlobalModal() {
  resetGlobalForm()
  showAddGlobalModal.value = true
}

function openAddProjetModal(globalId: number, sousProjetId?: number) {
  selectedGlobalId.value = globalId
  selectedSousProjetId.value = sousProjetId || null
  resetProjetForm()
  newProjet.value.id_global = globalId
  newProjet.value.id_sous_projet = sousProjetId || null
  
  const availableFpacks = fpacksForProjet.value
  if (availableFpacks.length > 0) {
    newProjet.value.fpack_id = availableFpacks[0].id
  }
  
  showAddProjetModal.value = true
}

function openAddSousProjetModal(globalId: number) {
  selectedGlobalId.value = globalId
  resetSousProjetForm()
  newSousProjet.value.id_global = globalId
  showAddSousProjetModal.value = true
}

function closeGlobalModal() {
  showAddGlobalModal.value = false
  resetGlobalForm()
}

function closeProjetModal() {
  showAddProjetModal.value = false
  resetProjetForm()
  selectedGlobalId.value = null
  selectedSousProjetId.value = null
}

function closeSousProjetModal() {
  showAddSousProjetModal.value = false
  resetSousProjetForm()
  selectedGlobalId.value = null
}

function resetGlobalForm() {
  newGlobal.value = { projet: '', sous_projet: '', client: null }
  globalErrors.value = {}
}

function resetProjetForm() {
  newProjet.value = { nom: '', fpack_id: null, id_global: null, id_sous_projet: null }
  projetErrors.value = {}
}

function resetSousProjetForm() {
  newSousProjet.value = { nom: '', description: '', id_global: null }
  sousProjetErrors.value = {}
}

function navigateToComplete(projetId: number) {
  console.log(`/complete/projets/${projetId}`)
  router.push(`/complete/projets/${projetId}`)
}

function navigateToFacture(projetId: number) {
  router.push(`/facture/${projetId}`)
}

function navigateToDetails(projetId: number) {
  router.push(`/projets/${projetId}/details`)
}

const showEditGlobalModal = ref(false)
const showEditSousProjetModal = ref(false)
const editingGlobal = ref({
  id: null as number | null,
  projet: '',
  sous_projet: '',
  client: null as number | null
})
const editingSousProjet = ref({
  id: null as number | null,
  nom: '',
  description: ''
})

function openEditGlobalModal(globalId: number) {
  const projetGlobal = projetsGlobaux.value.find(pg => pg.id === globalId)
  if (projetGlobal) {
    editingGlobal.value = {
      id: projetGlobal.id,
      projet: projetGlobal.projet,
      sous_projet: projetGlobal.sous_projet || '',
      client: projetGlobal.client
    }
    showEditGlobalModal.value = true
  }
}

function openEditSousProjetModal(sousProjetId: number) {
  let targetSousProjet: SousProjet | null = null
  for (const pg of projetsGlobaux.value) {
    const sousProjet = pg.projets?.find((sp: SousProjet) => sp.id === sousProjetId)
    if (sousProjet) {
      targetSousProjet = sousProjet
      break
    }
  }
  
  if (targetSousProjet) {
    editingSousProjet.value = {
      id: targetSousProjet.id,
      nom: targetSousProjet.nom,
      description: targetSousProjet.description || ''
    }
    showEditSousProjetModal.value = true
  }
}

function closeEditModal() {
  showEditGlobalModal.value = false
  editingGlobal.value = { id: null, projet: '', sous_projet: '', client: null }
}

function closeEditSousProjetModal() {
  showEditSousProjetModal.value = false
  editingSousProjet.value = { id: null, nom: '', description: '' }
}

async function handleUpdateProjetGlobal() {
  if (!editingGlobal.value.id) return
  
  try {
    await updateProjetGlobal(editingGlobal.value.id, {
      projet: editingGlobal.value.projet,
      sous_projet: editingGlobal.value.sous_projet,
      client: editingGlobal.value.client
    })
    closeEditModal()
    showToast('Projet modifié avec succès', '#10b981')
  } catch (error: any) {
    const message = error.response?.data?.detail || 'Erreur lors de la modification'
    showToast(message, '#e71717ff')
  }
}

async function handleUpdateSousProjet() {
  if (!editingSousProjet.value.id) return
  
  try {
    await updateSousProjet(editingSousProjet.value.id, {
      nom: editingSousProjet.value.nom,
      description: editingSousProjet.value.description
    })
    closeEditSousProjetModal()
    showToast('Sous-projet modifié avec succès', '#10b981')
  } catch (error: any) {
    const message = error.response?.data?.detail || 'Erreur lors de la modification'
    showToast(message, '#e71717ff')
  }
}

watch(
  () => router.currentRoute.value.path,
  async (newPath, oldPath) => {
    if (newPath === '/projet_global') {
      if (oldPath && oldPath.includes('/complete/projets/')) {
        await fetchData()
      } else if (oldPath !== newPath) {
        await fetchData()
      }
    }
  },
  { immediate: false }
)

watch(() => newGlobal.value.projet, () => {
  if (globalErrors.value.projet) delete globalErrors.value.projet
})

watch(() => newGlobal.value.client, () => {
  if (globalErrors.value.client) delete globalErrors.value.client
})

watch(() => newProjet.value.nom, () => {
  if (projetErrors.value.nom) delete projetErrors.value.nom
})

watch(() => newProjet.value.fpack_id, () => {
  if (projetErrors.value.fpack_id) delete projetErrors.value.fpack_id
})

watch(() => newSousProjet.value.nom, () => {
  if (sousProjetErrors.value.nom) delete sousProjetErrors.value.nom
})

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="main-header">
    <PageHeader titre="Projets" @ajouter="openAddGlobalModal" />
    <button class="toggle-all" @click="toggleAllCards">
      {{ allCardsExpanded ? 'Replier' : 'Déplier' }}
    </button>
  </div>
  
  <div class="projets-page">
    <div class="page-header-enhanced">
      
      
      <div class="stats-dashboard" v-if="globalStats">
        <div class="stat-card">
          <div class="stat-icon">📊</div>
          <div class="stat-content">
            <div class="stat-number">{{ globalStats.nb_projets_globaux }}</div>
            <div class="stat-label">Projets</div>
          </div>
        </div>
        
        <div class="stat-card fpack">
          <div class="stat-icon">🎯</div>
          <div class="stat-content">
            <div class="stat-number">{{ globalStats.nb_projets_total }}</div>
            <div class="stat-label">F-packs</div>
          </div>
        </div>
        
        <div class="stat-card success">
          <div class="stat-icon">✅</div>
          <div class="stat-content">
            <div class="stat-number">{{ globalStats.nb_projets_complets }}</div>
            <div class="stat-label">F-Packs Complets</div>
          </div>
        </div>
      </div>
    </div>

    <div class="projets-container">
      <Transition name="fade" appear>
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <p>Chargement des projets...</p>
        </div>
      </Transition>

      <TransitionGroup name="list" tag="div" class="projets-grid" v-if="!loading">
        <ProjetGlobalCard
          v-for="projetGlobal in filteredProjetsTree"
          :key="projetGlobal.id"
          :projet-global="projetGlobal"
          :force-expanded="allCardsExpanded"
          @add-projet="openAddProjetModal"
          @add-sous-projet="openAddSousProjetModal"
          @edit-global="openEditGlobalModal"
          @edit-sous-projet="openEditSousProjetModal"
          @delete-global="(id, nom) => onDeleteItem('global', id, nom)"
          @delete-sous-projet="(id, nom) => onDeleteItem('sous-projet', id, nom)"
          @delete-projet="(id, nom) => onDeleteItem('projet', id, nom)"
          @complete-projet="navigateToComplete"
          @view-facture="navigateToFacture"
          @view-details="navigateToDetails"
          class="projet-card-item"
        />
      </TransitionGroup>
      
      <div v-if="!loading && filteredProjetsTree.length === 0" class="empty-state">
        <div class="empty-icon">📋</div>
        <h3>{{ searchTerm ? 'Aucun résultat' : 'Aucun projet créé' }}</h3>
        <p>{{ searchTerm ? 'Essayez avec d\'autres termes de recherche' : 'Créer votre premier projet' }}</p>
        <button v-if="!searchTerm" @click="openAddGlobalModal" class="cta-button">
          ➕ Créer un projet
        </button>
      </div>
    </div>

    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showAddGlobalModal" class="modal-overlay" @click="closeGlobalModal">
          <div class="modal enhanced-modal" @click.stop>
            <div class="modal-header">
              <h3>✨ Nouveau Projet Global</h3>
              <button @click="closeGlobalModal" class="close-button">&times;</button>
            </div>
            
            <form @submit.prevent="handleCreateProjetGlobal" class="enhanced-form">
              <div class="form-group">
                <label>Nom du Projet</label>
                <input 
                  v-model="newGlobal.projet" 
                  :class="{ 'error': globalErrors.projet }"
                />
                <span v-if="globalErrors.projet" class="error-message">{{ globalErrors.projet }}</span>
              </div>
              
              <div class="form-group">
                <label>Client</label>
                <select 
                  v-model="newGlobal.client" 
                  :class="{ 'error': globalErrors.client }"
                >
                  <option value="">Sélectionner un client</option>
                  <option v-for="client in clients" :key="client.id" :value="client.id">
                    {{ client.nom }}
                  </option>
                </select>
                <span v-if="globalErrors.client" class="error-message">{{ globalErrors.client }}</span>
              </div>
              
              <div class="modal-actions">
                <button type="button" @click="closeGlobalModal" class="btn-cancel">
                  Annuler
                </button>
                <button type="submit" class="btn-primary">
                  ✨ Créer le projet
                </button>
              </div>
            </form>
          </div>
        </div>
      </Transition>
    </Teleport>

    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showEditGlobalModal" class="modal-overlay" @click="closeEditModal">
          <div class="modal enhanced-modal" @click.stop>
            <div class="modal-header">
              <h3>✏️ Modifier le Projet</h3>
              <button @click="closeEditModal" class="close-button">&times;</button>
            </div>
            
            <form @submit.prevent="handleUpdateProjetGlobal" class="enhanced-form">
              <div class="form-group">
                <label>Nom du Projet</label>
                <input 
                  v-model="editingGlobal.projet" 
                  required
                />
              </div>
              
              <div class="form-group">
                <label>Client</label>
                <select 
                  v-model="editingGlobal.client" 
                  required
                >
                  <option value="">Sélectionner un client</option>
                  <option v-for="client in clients" :key="client.id" :value="client.id">
                    {{ client.nom }}
                  </option>
                </select>
              </div>
              
              <div class="modal-actions">
                <button type="button" @click="closeEditModal" class="btn-cancel">
                  Annuler
                </button>
                <button type="submit" class="btn-primary">
                  💾 Sauvegarder
                </button>
              </div>
            </form>
          </div>
        </div>
      </Transition>
    </Teleport>

    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showAddSousProjetModal" class="modal-overlay" @click="closeSousProjetModal">
          <div class="modal enhanced-modal" @click.stop>
            <div class="modal-header">
              <h3>📁 Nouveau Sous-Projet</h3>
              <button @click="closeSousProjetModal" class="close-button">&times;</button>
            </div>
            
            <form @submit.prevent="handleCreateSousProjet" class="enhanced-form">
              <div class="form-group">
                <label>Nom du Sous-Projet</label>
                <input 
                  v-model="newSousProjet.nom" 
                  :class="{ 'error': sousProjetErrors.nom }"
                />
                <span v-if="sousProjetErrors.nom" class="error-message">{{ sousProjetErrors.nom }}</span>
              </div>
              
              <div class="form-group">
                <label>Description</label>
                <textarea 
                  v-model="newSousProjet.description"
                  rows="3"
                ></textarea>
              </div>
              
              <div class="modal-actions">
                <button type="button" @click="closeSousProjetModal" class="btn-cancel">
                  Annuler
                </button>
                <button type="submit" class="btn-primary">
                  📁 Créer le sous-projet
                </button>
              </div>
            </form>
          </div>
        </div>
      </Transition>
    </Teleport>

    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showEditSousProjetModal" class="modal-overlay" @click="closeEditSousProjetModal">
          <div class="modal enhanced-modal" @click.stop>
            <div class="modal-header">
              <h3>✏️ Modifier le Sous-Projet</h3>
              <button @click="closeEditSousProjetModal" class="close-button">&times;</button>
            </div>
            
            <form @submit.prevent="handleUpdateSousProjet" class="enhanced-form">
              <div class="form-group">
                <label>Nom du Sous-Projet</label>
                <input 
                  v-model="editingSousProjet.nom" 
                  required
                />
              </div>
              
              <div class="form-group">
                <label>Description</label>
                <textarea 
                  v-model="editingSousProjet.description"
                  rows="3"
                ></textarea>
              </div>
              
              <div class="modal-actions">
                <button type="button" @click="closeEditSousProjetModal" class="btn-cancel">
                  Annuler
                </button>
                <button type="submit" class="btn-primary">
                  💾 Sauvegarder
                </button>
              </div>
            </form>
          </div>
        </div>
      </Transition>
    </Teleport>

    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showAddProjetModal" class="modal-overlay" @click="closeProjetModal">
          <div class="modal enhanced-modal" @click.stop>
            <div class="modal-header">
              <h3>🎯 Nouveau F-Pack</h3>
              <button @click="closeProjetModal" class="close-button">&times;</button>
            </div>
            
            <form @submit.prevent="handleCreateProjet" class="enhanced-form">
              <div class="form-group">
                <label>Nom du F-Pack</label>
                <input 
                  v-model="newProjet.nom" 
                  :class="{ 'error': projetErrors.nom }"
                />
                <span v-if="projetErrors.nom" class="error-message">{{ projetErrors.nom }}</span>
              </div>
              
              <div class="form-group">
                <label>Template FPack</label>
                <select 
                  v-model="newProjet.fpack_id" 
                  :class="{ 'error': projetErrors.fpack_id }"
                >
                  <option value="">Sélectionner un FPack</option>
                  <option 
                    v-for="fpack in fpacksForProjet" 
                    :key="fpack.id" 
                    :value="fpack.id"
                  >
                    {{ fpack.nom }}
                  </option>
                </select>
                <span v-if="projetErrors.fpack_id" class="error-message">{{ projetErrors.fpack_id }}</span>
                <div v-if="fpacksForProjet.length === 0" class="info-message">
                  Aucun FPack disponible pour ce client
                </div>
              </div>
              
              <div class="modal-actions">
                <button type="button" @click="closeProjetModal" class="btn-cancel">
                  Annuler
                </button>
                <button 
                  type="submit" 
                  class="btn-primary"
                  :disabled="fpacksForProjet.length === 0"
                >
                  🎯 Créer le F-Pack
                </button>
              </div>
            </form>
          </div>
        </div>
      </Transition>
    </Teleport>

    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showDeleteConfirmModal" class="modal-overlay" @click="showDeleteConfirmModal = false">
          <div class="modal danger-modal" @click.stop>
            <div class="modal-header danger">
              <h3>🗑️ Confirmer la suppression</h3>
              <button @click="showDeleteConfirmModal = false" class="close-button">&times;</button>
            </div>
            
            <div class="modal-body">
              <div v-if="itemToDelete" class="item-to-delete">
                <p class="warning-text">
                  Êtes-vous sûr de vouloir supprimer 
                  <strong>{{ itemToDelete.type === 'global' ? 'le projet' : itemToDelete.type === 'sous-projet' ? 'le sous-projet' : 'le F-Pack' }}</strong>
                  "{{ itemToDelete.nom }}" ?
                </p>
                <p v-if="itemToDelete.type === 'global'" class="warning-text">
                  Cette action supprimera également tous les sous-projets et F-Packs associés.
                </p>
                <p v-else-if="itemToDelete.type === 'sous-projet'" class="warning-text">
                  Cette action supprimera également tous les F-Packs associés à ce sous-projet.
                </p>
              </div>
              
              <div class="modal-actions">
                <button @click="showDeleteConfirmModal = false" class="btn-cancel">
                  Annuler
                </button>
                <button @click="confirmDelete" class="btn-danger">
                  🗑️ Supprimer
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
  
  <div class="search-section">
    <TextSearch 
      v-model="searchTerm" 
      placeholder="Rechercher par nom de projet, client, FPack..." 
      class="enhanced-search"
    />
    <div v-if="searchTerm" class="search-results-info">
      {{ filteredProjetsTree.length }} résultat(s) trouvé(s)
    </div>
  </div>
</template>

<style scoped>
.projets-page {
  margin-left: 1%;
  max-width: 98%;
}

.toggle-all {
  background-color: #9b9b9c;
  margin-top: 72px;
  color: white;
  font-weight: 500;    
  font-size: 1.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 0.375rem;
  cursor: pointer;
  border: none;
  height: 50px ;
  align-self: center;
  transition: all 0.2s ease;
}

.toggle-all:hover {
  background-color: #6b6b6b;
}

.main-header {
  display: flex;
  align-items: center; 
  gap: 2rem;          
  margin-bottom: 0.75rem; 
  margin-left: 1%;
}

.page-header-enhanced {
  margin-bottom: 2rem;
}

.stats-dashboard {
  display: flex;
  justify-content: space-between;
  gap: 1.5rem;
  margin-top: 2rem;
  flex-wrap: nowrap;
  width: 100%;
}

.stat-card {
  flex: 1 1 0;
  min-width: 180px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  padding: 0.8rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.15);
}

.stat-card.success {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.stat-card.fpack {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon {
  font-size: 2rem;
  opacity: 0.9;
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.9;
  font-weight: 500;
}

.search-section {
  display: flex;
  gap: 1rem;
}

.search-results-info {
  margin-top: 25px;
  color: #6b7280;
  font-size: 0.9rem;
  text-align: center;
}

.projets-container {
  overflow-y: auto;
  position: relative;
  min-height: 200px;
  max-height: calc(100vh - 450px);
  padding-right: 1rem;
}

.projets-container::-webkit-scrollbar {
  width: 8px;
}

.projets-container::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.projets-container::-webkit-scrollbar-thumb {
  background: #94a3b8;
  border-radius: 4px;
  transition: background 0.2s;
}

.projets-container::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  color: #6b7280;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.projets-grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
}

.projet-card-item {
  transition: all 0.3s ease;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #6b7280;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state h3 {
  margin: 0 0 1rem 0;
  color: #374151;
}

.cta-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease;
  margin-top: 1rem;
}

.cta-button:hover {
  transform: translateY(-2px);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.enhanced-modal {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
}

.danger-modal {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  width: 90%;
  max-width: 400px;
}

.modal-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header.danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-button {
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  opacity: 0.8;
  transition: opacity 0.2s;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-button:hover {
  opacity: 1;
}

.enhanced-form {
  padding: 2rem;
}

.modal-body {
  padding: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
  margin-right: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #374151;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.875rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
  font-family: inherit;
  resize: vertical;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-group input.error,
.form-group select.error {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.error-message {
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 0.25rem;
  display: block;
}

.info-message {
  color: #6b7280;
  font-size: 0.875rem;
  margin-top: 0.25rem;
  font-style: italic;
}

.item-to-delete {
  background: #fef2f2;
  border: 1px solid #fecaca;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  text-align: center;
}

.warning-text {
  color: #ef4444;
  font-size: 0.9rem;
  font-weight: 500;
  margin: 0.5rem 0;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
}

.btn-cancel {
  padding: 0.875rem 1.5rem;
  border: 2px solid #e5e7eb;
  background: white;
  color: #6b7280;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  border-color: #d1d5db;
  background: #f9fafb;
}

.btn-primary {
  padding: 0.875rem 1.5rem;
  border: none;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.btn-danger {
  padding: 0.875rem 1.5rem;
  border: none;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-danger:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.list-move {
  transition: transform 0.3s ease;
}

.modal-enter-active {
  transition: all 0.3s ease;
}

.modal-leave-active {
  transition: all 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

</style>