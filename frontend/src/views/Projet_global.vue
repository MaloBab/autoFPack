<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
const router = useRouter()

const api = axios.create({
  baseURL: 'http://localhost:8000'
})

// État global
const activeTab = ref('stats')
const loading = ref(false)

// Données
const stats = ref(null)
const projetsGlobaux = ref([])
const clients = ref([])
const fpacks = ref([])
const sousProjets = ref([])

// Formulaires
const showProjetForm = ref(false)
const showSousProjetForm = ref(false)
const showFpackForm = ref(false)
const editingProjet = ref(null)
const editingSousProjet = ref(null)
const selectedProjetForSousProjet = ref(null)
const selectedSousProjetForFpack = ref(null)

// Données des formulaires
const projetFormData = ref({
  projet: '',
  client: ''
})

const sousProjetFormData = ref({
  nom: '',
  id_global: ''
})

const fpackFormData = ref({
  fpack_id: '',
  FPack_number: '',
  Robot_Location_Code: ''
})

// Computed
const filteredSousProjets = computed(() => {
  if (!selectedProjetForSousProjet.value) return []
  return sousProjets.value.filter(sp => sp.id_global === selectedProjetForSousProjet.value.id)
})

// Méthodes API
const fetchStats = async () => {
  try {
    loading.value = true
    const response = await api.get('/projets_globaux/stats')
    stats.value = response.data
    
  } catch (error) {
    console.error('Erreur lors du chargement des stats:', error)
  } finally {
    loading.value = false
  }
}

const fetchProjetsGlobaux = async () => {
  try {
    loading.value = true
    const response = await api.get('/projets_globaux')
    projetsGlobaux.value = response.data
  } catch (error) {
    console.error('Erreur lors du chargement des projets:', error)
  } finally {
    loading.value = false
  }
}

const fetchClients = async () => {
  try {
    const response = await api.get('/clients')
    clients.value = response.data
  } catch (error) {
    console.error('Erreur lors du chargement des clients:', error)
  }
}

const fetchFpacks = async () => {
  try {
    const response = await api.get('/fpacks')
    fpacks.value = response.data
  } catch (error) {
    console.error('Erreur lors du chargement des FPacks:', error)
  }
}

const fetchSousProjets = async () => {
  try {
    const response = await api.get('/sous_projets')
    sousProjets.value = response.data
    console.log('Sous-projets chargés:', sousProjets.value)
  } catch (error) {
    console.error('Erreur lors du chargement des sous-projets:', error)
  }
}

// Gestion des projets globaux
const handleProjetSubmit = async () => {
  try {
    if (editingProjet.value) {
      await api.put(`/projets_globaux/${editingProjet.value.id}`, projetFormData.value)
    } else {
      await api.post('/projets_globaux', projetFormData.value)
    }
    showProjetForm.value = false
    editingProjet.value = null
    projetFormData.value = { projet: '', client: '' }
    await fetchProjetsGlobaux()
  } catch (error) {
    console.error('Erreur lors de la sauvegarde:', error)
    alert('Erreur lors de la sauvegarde du projet')
  }
}

const editProjet = (projet) => {
  editingProjet.value = projet
  projetFormData.value = { projet: projet.projet, client: projet.client }
  showProjetForm.value = true
}

const deleteProjet = async (id) => {
  if (confirm('Êtes-vous sûr de vouloir supprimer ce projet ?')) {
    try {
      await api.delete(`/projets_globaux/${id}`)
      await fetchProjetsGlobaux()
    } catch (error) {
      console.error('Erreur lors de la suppression:', error)
      alert('Erreur lors de la suppression. Vérifiez s\'il n\'y a pas de sous-projets associés.')
    }
  }
}

// Gestion des sous-projets
const openSousProjetForm = (projet) => {
  selectedProjetForSousProjet.value = projet
  sousProjetFormData.value = { nom: '', id_global: projet.id }
  showSousProjetForm.value = true
}

const handleSousProjetSubmit = async () => {
  try {
    if (editingSousProjet.value) {
      await api.put(`/sous_projets/${editingSousProjet.value.id}`, sousProjetFormData.value)
    } else {
      await api.post('/sous_projets', sousProjetFormData.value)
    }
    showSousProjetForm.value = false
    editingSousProjet.value = null
    selectedProjetForSousProjet.value = null
    sousProjetFormData.value = { nom: '', id_global: '' }
    await fetchProjetsGlobaux()
    await fetchSousProjets()
  } catch (error) {
    console.error('Erreur lors de la sauvegarde:', error)
    alert('Erreur lors de la sauvegarde du sous-projet')
  }
}

const editSousProjet = (sousProjet) => {
  editingSousProjet.value = sousProjet
  sousProjetFormData.value = { nom: sousProjet.nom, id_global: sousProjet.id_global }
  showSousProjetForm.value = true
}

const deleteSousProjet = async (id) => {
  if (confirm('Êtes-vous sûr de vouloir supprimer ce sous-projet ?')) {
    try {
      await api.delete(`/sous_projets/${id}`)
      await fetchProjetsGlobaux()
      await fetchSousProjets()
    } catch (error) {
      console.error('Erreur lors de la suppression:', error)
      alert('Erreur lors de la suppression. Vérifiez s\'il n\'y a pas de FPacks associés.')
    }
  }
}

// Gestion des FPacks
const openFpackForm = (sousProjet) => {
  selectedSousProjetForFpack.value = sousProjet
  fpackFormData.value = { fpack_id: '', FPack_number: '', Robot_Location_Code: '' }
  showFpackForm.value = true
}

const handleFpackSubmit = async () => {
  try {
    await api.post(`/sous_projets/${selectedSousProjetForFpack.value.id}/fpacks`, fpackFormData.value)
    showFpackForm.value = false
    selectedSousProjetForFpack.value = null
    fpackFormData.value = { fpack_id: '', FPack_number: '', Robot_Location_Code: '' }
    await fetchProjetsGlobaux()
  } catch (error) {
    console.error('Erreur lors de l\'association du FPack:', error)
    alert('Erreur: ' + (error.response?.data?.detail || 'Erreur inconnue'))
  }
}

const removeFpackFromSousProjet = async (sousProjetId ) => {
  if (confirm('Êtes-vous sûr de vouloir retirer ce FPack ?')) {
    console.log(sousProjets.value.find(sp => sp.id === sousProjetId).fpack_id)
    try {
      await api.delete(`/sous_projets/${sousProjetId}/fpacks/${sousProjets.value.find(sp => sp.id === sousProjetId).fpack_id}`)
      await fetchProjetsGlobaux()
    } catch (error) {
      console.error('Erreur lors de la suppression:', error)
      alert('Erreur lors de la suppression. Vérifiez s\'il n\'y a pas de sélections associées.')
    }
  }
}

// Fonctions utilitaires
const cancelProjetForm = () => {
  showProjetForm.value = false
  editingProjet.value = null
  projetFormData.value = { projet: '', client: '' }
}

const cancelSousProjetForm = () => {
  showSousProjetForm.value = false
  editingSousProjet.value = null
  selectedProjetForSousProjet.value = null
  sousProjetFormData.value = { nom: '', id_global: '' }
}

const cancelFpackForm = () => {
  showFpackForm.value = false
  selectedSousProjetForFpack.value = null
  fpackFormData.value = { fpack_id: '', FPack_number: '', Robot_Location_Code: '' }
}

const getClientName = (clientId) => {
  const client = clients.value.find(c => c.id === clientId)
  return client ? client.nom : 'Client inconnu'
}

const getFpackName = (fpackId) => {
  const fpack = fpacks.value.find(f => f.id === fpackId)
  return fpack ? fpack.nom : 'FPack inconnu'
}

const remplirFpack = (sousProjetId, fpackId) => {
  router.push({ 
    name: 'CompleteProjet', 
    params: { 
      sous_projet_id: sousProjetId, 
      fpack_id: fpackId 
    } 
  })
}

// Initialisation
onMounted(async () => {
  await fetchClients()
  await fetchFpacks()
  await fetchStats()
  await fetchProjetsGlobaux()
  await fetchSousProjets()
})
</script>

<template>
  <div class="app-container">
    <!-- Navigation -->
    <nav class="nav-tabs">
      <button 
        :class="{ active: activeTab === 'stats' }"
        @click="activeTab = 'stats'"
      >
        Statistiques
      </button>
      <button 
        :class="{ active: activeTab === 'projets' }"
        @click="activeTab = 'projets'"
      >
        Projets Globaux
      </button>
    </nav>

    <!-- Contenu principal -->
    <main class="main-content">
      <div v-if="loading" class="loading">
        Chargement...
      </div>

      <!-- Onglet Statistiques -->
      <div v-if="activeTab === 'stats'" class="stats-section">
        <h2>Statistiques des Projets</h2>
        <div v-if="stats" class="stats-grid">
          <div class="stats-card">
            <h3>Vue d'ensemble</h3>
            <div class="stats-item">
              <span>Projets globaux:</span>
              <strong>{{ stats.nb_projets_globaux }}</strong>
            </div>
            <div class="stats-item">
              <span>Sous-projets:</span>
              <strong>{{ stats.nb_sous_projets }}</strong>
            </div>
            <div class="stats-item">
              <span>Sous-projets complets:</span>
              <strong>{{ stats.sous_projets_complets }}</strong>
            </div>
            <div class="stats-item">
              <span>Sous-projets incomplets:</span>
              <strong>{{ stats.sous_projets_incomplets }}</strong>
            </div>
          </div>
          <div class="stats-card">
            <h3>Projets par client</h3>
            <div v-for="item in stats.projets_par_client" :key="item.client" class="stats-item">
              <span>{{ item.client }}:</span>
              <strong>{{ item.count }}</strong>
            </div>
          </div>
        </div>
      </div>

      <!-- Onglet Projets Globaux -->
      <div v-if="activeTab === 'projets'" class="projets-section">
        <div class="section-header">
          <h2>Projets Globaux</h2>
          <button @click="showProjetForm = true" class="btn btn-primary">
            + Nouveau Projet
          </button>
        </div>

        <!-- Formulaire Projet Global -->
        <div v-if="showProjetForm" class="form-modal">
          <div class="form-container">
            <h3>{{ editingProjet ? 'Modifier' : 'Nouveau' }} Projet Global</h3>
            <form @submit.prevent="handleProjetSubmit">
              <div class="form-group">
                <label>Nom du projet:</label>
                <input
                  v-model="projetFormData.projet"
                  type="text"
                  required
                  class="form-input"
                >
              </div>
              <div class="form-group">
                <label>Client:</label>
                <select
                  v-model="projetFormData.client"
                  required
                  class="form-input"
                >
                  <option value="">Sélectionnez un client</option>
                  <option v-for="client in clients" :key="client.id" :value="client.id">
                    {{ client.nom }}
                  </option>
                </select>
              </div>
              <div class="form-actions">
                <button type="submit" class="btn btn-success">
                  {{ editingProjet ? 'Modifier' : 'Créer' }}
                </button>
                <button type="button" @click="cancelProjetForm" class="btn btn-secondary">
                  Annuler
                </button>
              </div>
            </form>
          </div>
        </div>

        <!-- Formulaire Sous-Projet -->
        <div v-if="showSousProjetForm" class="form-modal">
          <div class="form-container">
            <h3>{{ editingSousProjet ? 'Modifier' : 'Nouveau' }} Sous-Projet</h3>
            <form @submit.prevent="handleSousProjetSubmit">
              <div class="form-group">
                <label>Nom du sous-projet:</label>
                <input
                  v-model="sousProjetFormData.nom"
                  type="text"
                  required
                  class="form-input"
                >
              </div>
              <div class="form-actions">
                <button type="submit" class="btn btn-success">
                  {{ editingSousProjet ? 'Modifier' : 'Créer' }}
                </button>
                <button type="button" @click="cancelSousProjetForm" class="btn btn-secondary">
                  Annuler
                </button>
              </div>
            </form>
          </div>
        </div>

        <!-- Formulaire FPack -->
        <div v-if="showFpackForm" class="form-modal">
          <div class="form-container">
            <h3>Associer un FPack</h3>
            <form @submit.prevent="handleFpackSubmit">
              <div class="form-group">
                <label>FPack:</label>
                <select
                  v-model="fpackFormData.fpack_id"
                  required
                  class="form-input"
                >
                  <option value="">Sélectionnez un FPack</option>
                  <option v-for="fpack in fpacks" :key="fpack.id" :value="fpack.id">
                    {{ fpack.nom }}
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label>Numéro FPack:</label>
                <input
                  v-model="fpackFormData.FPack_number"
                  type="text"
                  class="form-input"
                >
              </div>
              <div class="form-group">
                <label>Code Location Robot:</label>
                <input
                  v-model="fpackFormData.Robot_Location_Code"
                  type="text"
                  class="form-input"
                >
              </div>
              <div class="form-actions">
                <button type="submit" class="btn btn-success">
                  Associer
                </button>
                <button type="button" @click="cancelFpackForm" class="btn btn-secondary">
                  Annuler
                </button>
              </div>
            </form>
          </div>
        </div>

        <!-- Liste des projets -->
        <div class="projets-list">
          <div v-for="projet in projetsGlobaux" :key="projet.id" class="projet-card">
            <div class="projet-header">
              <div class="projet-info">
                <h3>{{ projet.projet }}</h3>
                <p><strong>Client:</strong> {{ projet.client_nom }}</p>
                <p><strong>Sous-projets:</strong> {{ projet.sous_projets.length }}</p>
              </div>
              <div class="projet-actions">
                <button @click="editProjet(projet)" class="btn btn-warning">
                  Modifier
                </button>
                <button @click="openSousProjetForm(projet)" class="btn btn-info">
                  + Sous-projet
                </button>
                <button @click="deleteProjet(projet.id)" class="btn btn-danger">
                  Supprimer
                </button>
              </div>
            </div>

            <!-- Sous-projets -->
            <div v-if="projet.sous_projets.length > 0" class="sous-projets">
              <h4>Sous-projets:</h4>
              <div v-for="sousProjet in projet.sous_projets" :key="sousProjet.id" class="sous-projet-card">
                <div class="sous-projet-header">
                  <div class="sous-projet-info">
                    <strong>{{ sousProjet.nom }}</strong>
                    <span :class="{ 'status-complete': sousProjet.complet, 'status-incomplete': !sousProjet.complet }">
                      {{ sousProjet.complet ? 'Complet' : 'Incomplet' }}
                    </span>
                    <span class="selections-count">
                      ({{ sousProjet.nb_selections }}/{{ sousProjet.nb_groupes_attendus }} sélections)
                    </span>
                  </div>
                  <div class="sous-projet-actions">
                    <button @click="editSousProjet(sousProjet)" class="btn btn-sm btn-warning">
                      Modifier
                    </button>
                    <button @click="openFpackForm(sousProjet)" class="btn btn-sm btn-info">
                      + FPack
                    </button>
                    <button @click="deleteSousProjet(sousProjet.id)" class="btn btn-sm btn-danger">
                      Supprimer
                    </button>
                  </div>
                </div>

                <!-- FPack associé -->
                <div v-if="sousProjet.fpack_nom" class="fpack-info">
                  <p><strong>FPack:</strong> {{ sousProjet.fpack_nom }}</p>
                  <p v-if="sousProjet.FPack_number"><strong>Numéro:</strong> {{ sousProjet.FPack_number }}</p>
                  <p v-if="sousProjet.Robot_Location_Code"><strong>Code Location:</strong> {{ sousProjet.Robot_Location_Code }}</p>
                  <button @click="removeFpackFromSousProjet(sousProjet.id, sousProjet.fpack_id)" class="btn btn-sm btn-danger">
                    Retirer FPack
                  </button>
                  <button @click="remplirFpack(sousProjet.id, sousProjet.fpack_id)" class="btn btn-sm btn-success">
                    Remplir FPack
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

.nav-tabs {
  display: flex;
  border-bottom: 1px solid #ddd;
  margin-bottom: 20px;
}

.nav-tabs button {
  padding: 10px 20px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: 16px;
}

.nav-tabs button.active {
  border-bottom-color: #007bff;
  color: #007bff;
}

.nav-tabs button:hover {
  background-color: #f8f9fa;
}

.loading {
  text-align: center;
  padding: 40px;
  font-size: 18px;
}

.stats-section h2,
.projets-section h2 {
  margin-bottom: 20px;
  color: #333;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.stats-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  background: #f8f9fa;
}

.stats-card h3 {
  margin: 0 0 15px 0;
  color: #495057;
}

.stats-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  text-decoration: none;
  display: inline-block;
}

.btn-primary { background-color: #007bff; color: white; }
.btn-success { background-color: #28a745; color: white; }
.btn-warning { background-color: #ffc107; color: #212529; }
.btn-danger { background-color: #dc3545; color: white; }
.btn-info { background-color: #17a2b8; color: white; }
.btn-secondary { background-color: #6c757d; color: white; }

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}

.btn:hover {
  opacity: 0.8;
}

.form-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.form-container {
  background: white;
  padding: 30px;
  border-radius: 8px;
  min-width: 400px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
}

.form-container h3 {
  margin: 0 0 20px 0;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.projets-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.projet-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  background: #f8f9fa;
}

.projet-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.projet-info h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.projet-info p {
  margin: 5px 0;
  color: #666;
}

.projet-actions {
  display: flex;
  gap: 10px;
}

.sous-projets {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #ddd;
}

.sous-projets h4 {
  margin: 0 0 15px 0;
  color: #495057;
}

.sous-projet-card {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 10px;
}

.sous-projet-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.sous-projet-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.status-complete {
  color: #28a745;
  font-weight: bold;
}

.status-incomplete {
  color: #dc3545;
  font-weight: bold;
}

.selections-count {
  color: #666;
  font-size: 14px;
}

.sous-projet-actions {
  display: flex;
  gap: 5px;
}

.fpack-info {
  background: #e9ecef;
  padding: 10px;
  border-radius: 4px;
  margin-top: 10px;
}

.fpack-info p {
  margin: 5px 0;
  font-size: 14px;
}

@media (max-width: 768px) {
  .projet-header,
  .sous-projet-header {
    flex-direction: column;
    gap: 10px;
  }

  .projet-actions,
  .sous-projet-actions {
    align-self: stretch;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .form-container {
    min-width: 300px;
    margin: 20px;
  }
}
</style>