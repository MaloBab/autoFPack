<script setup>
import { ref, onMounted, computed, reactive } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

// Composants
import ProjetHeader from '../components/Projets/ProjetHeader.vue'
import NavigationTabs from '../components/Projets/NavigationTabs.vue'
import StatsView from '../components/Projets/StatsView.vue'
import ProjectsView from '../components/Projets/ProjectsView.vue'
import ProjectModal from '../components/Projets/ProjectModal.vue'
import SubprojectModal from '../components/Projets/SubProjectModal.vue'
import FpackModal from '../components/Projets/FpackModal.vue'
import NotificationToast from '../components/Projets/NotificationToast.vue'
import LoadingOverlay from '../components/Projets/LoadingOverlay.vue'

const router = useRouter()

const api = axios.create({
  baseURL: 'http://localhost:8000'
})

// États réactifs
const activeTab = ref('stats')
const loading = reactive({
  stats: false,
  projects: false,
  saving: false
})

// Données
const stats = ref(null)
const projetsGlobaux = ref([])
const clients = ref([])
const fpacks = ref([])

// États des modals
const showProjectModal = ref(false)
const showSubprojectModal = ref(false)
const showFpackModal = ref(false)
const editingProject = ref(null)
const editingSubproject = ref(null)
const selectedProjectForSubproject = ref(null)
const selectedSubprojectForFpack = ref(null)

// Système de notifications
const notifications = ref([])

// Computed
const availableFpacks = computed(() => {
  if (!selectedSubprojectForFpack.value || !fpacks.value.length) return []
  
  const project = projetsGlobaux.value.find(p => 
    p.sous_projets.some(sp => sp.id === selectedSubprojectForFpack.value.id)
  )
  
  if (!project) return []
  
  return fpacks.value.filter(fpack => fpack.client === project.client)
})

const clientForAvailableFpacks = computed(() => {
  if (!availableFpacks.value.length) return '';
  return clients.value.find(c => c.id === availableFpacks.value[0].client)?.nom || 'Non spécifié';
   
});

// Méthodes API
const fetchStats = async () => {
  try {
    loading.stats = true
    const response = await api.get('/projets_globaux/stats')
    stats.value = response.data
  } catch (error) {
    showNotification('Erreur lors du chargement des statistiques', 'error')
  } finally {
    loading.stats = false
  }
}

const fetchProjetsGlobaux = async () => {
  try {
    loading.projects = true
    const response = await api.get('/projets_globaux')
    projetsGlobaux.value = response.data
  } catch (error) {
    showNotification('Erreur lors du chargement des projets', 'error')
  } finally {
    loading.projects = false
  }
}

const fetchClients = async () => {
  try {
    const response = await api.get('/clients')
    clients.value = response.data
  } catch (error) {
    showNotification('Erreur lors du chargement des clients', 'error')
  }
}

const fetchFpacks = async () => {
  try {
    const response = await api.get('/fpacks')
    fpacks.value = response.data
  } catch (error) {
    showNotification('Erreur lors du chargement des FPacks', 'error')
  }
}

// Gestionnaires d'événements
const handleCreateProject = () => {
  editingProject.value = null
  showProjectModal.value = true
}

const handleEditProject = (project) => {
  editingProject.value = project
  showProjectModal.value = true
}

const handleDeleteProject = async (id) => {
  try {
    await api.delete(`/projets_globaux/${id}`)
    await fetchProjetsGlobaux()
    await fetchStats()
    showNotification('Projet supprimé avec succès', 'success')
  } catch (error) {
    showNotification('Erreur lors de la suppression. Vérifiez s\'il n\'y a pas de sous-projets associés.', 'error')
  }
}

const handleCreateSubproject = (project) => {
  selectedProjectForSubproject.value = project
  editingSubproject.value = null
  showSubprojectModal.value = true
}

const handleEditSubproject = (subproject) => {
  editingSubproject.value = subproject
  showSubprojectModal.value = true
}

const handleDeleteSubproject = async (id) => {
  try {
    await api.delete(`/sous_projets/${id}`)
    await fetchProjetsGlobaux()
    await fetchStats()
    showNotification('Sous-projet supprimé avec succès', 'success')
  } catch (error) {
    showNotification('Erreur lors de la suppression. Vérifiez s\'il n\'y a pas de FPacks associés.', 'error')
  }
}

const handleAssociateFpack = (subproject) => {
  selectedSubprojectForFpack.value = subproject
  showFpackModal.value = true
  console.log(clientForAvailableFpacks.value);
}

const handleRemoveFpack = async (subprojectId) => {
  try {
    const subproject = projetsGlobaux.value
      .flatMap(p => p.sous_projets)
      .find(sp => sp.id === subprojectId)
    
    if (subproject && subproject.fpack_id) {
      await api.delete(`/sous_projets/${subprojectId}/fpacks/${subproject.fpack_id}`)
      await fetchProjetsGlobaux()
      showNotification('FPack retiré avec succès', 'success')
    }
  } catch (error) {
    showNotification('Erreur lors de la suppression du FPack', 'error')
  }
}

const handleProjectSubmit = async (projectData) => {
  try {
    loading.saving = true
    if (editingProject.value) {
      await api.put(`/projets_globaux/${editingProject.value.id}`, projectData)
      showNotification('Projet modifié avec succès', 'success')
    } else {
      await api.post('/projets_globaux', projectData)
      showNotification('Projet créé avec succès', 'success')
    }
    closeProjectModal()
    await fetchProjetsGlobaux()
    await fetchStats()
  } catch (error) {
    showNotification('Erreur lors de la sauvegarde du projet', 'error')
  } finally {
    loading.saving = false
  }
}

const handleSubprojectSubmit = async (subprojectData) => {
  try {
    loading.saving = true
    if (editingSubproject.value) {
      await api.put(`/sous_projets/${editingSubproject.value.id}`, subprojectData)
      showNotification('Sous-projet modifié avec succès', 'success')
    } else {
      await api.post('/sous_projets', subprojectData)
      showNotification('Sous-projet créé avec succès', 'success')
    }
    closeSubprojectModal()
    await fetchProjetsGlobaux()
    await fetchStats()
  } catch (error) {
    showNotification('Erreur lors de la sauvegarde du sous-projet', 'error')
  } finally {
    loading.saving = false
  }
}

const handleFpackSubmit = async (fpackData) => {
  try {
    loading.saving = true
    await api.post(`/sous_projets/${selectedSubprojectForFpack.value.id}/fpacks`, fpackData)
    closeFpackModal()
    await fetchProjetsGlobaux()
    showNotification('FPack associé avec succès', 'success')
  } catch (error) {
    showNotification(`Erreur: ${error.response?.data?.detail || 'Erreur inconnue'}`, 'error')
  } finally {
    loading.saving = false
  }
}

const remplirFpack = (sousProjetId, fpackId) => {

  // Validation des paramètres
  if (!sousProjetId) {
    showNotification('ID du sous-projet manquant', 'error')
    return
  }
  
  if (!fpackId) {
    showNotification('ID du FPack manquant', 'error')
    return
  }
  
  router.push({ 
    name: 'CompleteProjet', 
    params: { 
      sous_projet_id: sousProjetId,
      fpack_id: fpackId
    } 
  })
}

// Gestion des modals
const closeProjectModal = () => {
  showProjectModal.value = false
  editingProject.value = null
}

const closeSubprojectModal = () => {
  showSubprojectModal.value = false
  editingSubproject.value = null
  selectedProjectForSubproject.value = null
}

const closeFpackModal = () => {
  showFpackModal.value = false
  selectedSubprojectForFpack.value = null
}

// Système de notifications
const showNotification = (message, type = 'info') => {
  const id = Date.now()
  notifications.value.push({ id, message, type })
  setTimeout(() => removeNotification(id), 5000)
}

const removeNotification = (id) => {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index > -1) notifications.value.splice(index, 1)
}

// Initialisation
onMounted(async () => {
  await Promise.all([
    fetchClients(),
    fetchFpacks(),
    fetchStats(),
    fetchProjetsGlobaux()
  ])
})
</script>

<template>
  <div class="project-manager">
    <!-- Header dynamique avec particules -->
    <ProjetHeader 
      :stats="stats" 
      :loading="loading.stats" 
      @refresh="fetchStats"
    />

    <!-- Navigation fluide -->
    <NavigationTabs 
      :active-tab="activeTab" 
      @tab-change="activeTab = $event"
    />

    <main class="main-content">
      <Transition name="slide-fade" mode="out-in">
        <StatsView 
          v-if="activeTab === 'stats'"
          key="stats"
          :stats="stats"
          :loading="loading.stats"
          :projets="projetsGlobaux"
        />

        <ProjectsView
          v-else-if="activeTab === 'projets'"
          key="projects"
          :projets="projetsGlobaux"
          :clients="clients"
          :fpacks="fpacks"
          :loading="loading.projects"
          @create-project="handleCreateProject"
          @edit-project="handleEditProject"
          @delete-project="handleDeleteProject"
          @create-subproject="handleCreateSubproject"
          @edit-subproject="handleEditSubproject"
          @delete-subproject="handleDeleteSubproject"
          @associate-fpack="handleAssociateFpack"
          @remove-fpack="handleRemoveFpack"
          @complete-fpack="remplirFpack"
        />
      </Transition>
    </main>

    <!-- Modals avec animations -->
    <ProjectModal
      :show="showProjectModal"
      :project="editingProject"
      :clients="clients"
      :loading="loading.saving"
      @save="handleProjectSubmit"
      @close="closeProjectModal"
    />

    <SubprojectModal
      :show="showSubprojectModal"
      :subproject="editingSubproject"
      :project="selectedProjectForSubproject"
      :loading="loading.saving"
      @save="handleSubprojectSubmit"
      @close="closeSubprojectModal"
    />

    <FpackModal
      :show="showFpackModal"
      :subproject="selectedSubprojectForFpack"
      :available-fpacks="availableFpacks"
      :clientName="clientForAvailableFpacks"
      :loading="loading.saving"
      @save="handleFpackSubmit"
      @close="closeFpackModal"
    />

    <!-- Toast notifications -->
    <NotificationToast
      :notifications="notifications"
    />

    <!-- Loading overlay global -->
    <LoadingOverlay :show="Object.values(loading).some(Boolean)" />
  </div>
</template>


<style scoped>
.project-manager {
  height: 85vh;
  background: linear-gradient(135deg, #1a253c 0%, #374151 100%);
  padding: 20px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.main-content {
  flex: 1;
  position: relative;
  min-height: 0;
}

/* Transitions */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.slide-fade-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

</style>