<script setup lang="ts">
import { ref, type Ref, onMounted, computed, watch, nextTick } from 'vue'
import axios from 'axios'

const props = defineProps<{
  isOpen: boolean
  tableName: string 
}>()
const emit = defineEmits(['close', 'created'])

const form: Ref<Record<string, any>> = ref({})
const columns: Ref<string[]> = ref([])
const tabs: Ref<string[]> = ref(['Informations'])
const activeTab: Ref<string> = ref('Informations')
const isLoading = ref(false)
const isSaving = ref(false)
const errors: Ref<Record<string, string>> = ref({})
const showSuccess = ref(false)

// Animation states
const modalVisible = ref(false)
const contentVisible = ref(false)

const filteredColumns = computed(() => columns.value.filter(col => col !== 'id'))

const produitsList: Ref<any[]> = ref([])
const robotsList: Ref<any[]> = ref([])
const clientsList: Ref<any[]> = ref([])

const incompatibilitesProduits: Ref<any[]> = ref([])
const compatibilitesRobots: Ref<any[]> = ref([])
const compatibilitesProduits: Ref<any[]> = ref([])

const prix: Ref<Record<number, any>> = ref({})
const prixRobot: Ref<any> = ref({
  prix_robot: 0,
  prix_transport: 0,
  commentaire: ''
})

// Progress indicator
const currentStep = computed(() => {
  const stepIndex = tabs.value.indexOf(activeTab.value)
  return ((stepIndex + 1) / tabs.value.length) * 100
})

// Watch for modal opening
watch(() => props.isOpen, async (newValue) => {
  if (newValue) {
    modalVisible.value = true
    await nextTick()
    setTimeout(() => {
      contentVisible.value = true
    }, 50)
    loadData()
  } else {
    contentVisible.value = false
    setTimeout(() => {
      modalVisible.value = false
    }, 300)
  }
})

async function loadData() {
  isLoading.value = true
  try {
    const colsRes = await axios.get(`http://localhost:8000/table-columns/${props.tableName}`)
    
    const columnsData = colsRes.data
    if (Array.isArray(columnsData)) {
      columns.value = columnsData
    } else {
      columns.value = Object.values(columnsData)
    }
    
    columns.value.forEach(col => form.value[col] = '')

    if (['produits', 'robots'].includes(props.tableName)) {
      tabs.value = ['Informations', 'Relations', 'Tarification']
      
      const [produitsRes, robotsRes, clientsRes] = await Promise.all([
        axios.get('http://localhost:8000/produits'),
        axios.get('http://localhost:8000/robots'),
        axios.get('http://localhost:8000/clients')
      ])
      
      produitsList.value = produitsRes.data
      robotsList.value = robotsRes.data
      clientsList.value = clientsRes.data
      
      if (props.tableName === 'produits') {
        clientsList.value.forEach(c => {
          prix.value[c.id] = { prix_produit: 0, prix_transport: 0, commentaire: '' }
        })
      } else if (props.tableName === 'robots') {
        prixRobot.value = { prix_robot: 0, prix_transport: 0, commentaire: '' }
      }
    }
  } catch (error) {
    console.error('Erreur lors du chargement:', error)
  } finally {
    isLoading.value = false
  }
}

function validateForm() {
  errors.value = {}
  let isValid = true

  filteredColumns.value.forEach(col => {
    if (!form.value[col] || form.value[col].toString().trim() === '') {
      errors.value[col] = 'Ce champ est requis'
      isValid = false
    }
  })

  return isValid
}

function toggleAll(list: any[], target: Ref<any[]>) {
  const isAllSelected = target.value.length === list.length
  target.value = isAllSelected ? [] : list.map(i => i.id)
}

function toggleAllIncompatibilites() {
  toggleAll(produitsList.value, incompatibilitesProduits)
}

function toggleAllCompatibilitesRobots() {
  toggleAll(robotsList.value, compatibilitesRobots)
}

function toggleAllCompatibilitesProduits() {
  toggleAll(produitsList.value, compatibilitesProduits)
}

function switchTab(tab: string) {
  activeTab.value = tab
}

function nextTab() {
  const currentIndex = tabs.value.indexOf(activeTab.value)
  if (currentIndex < tabs.value.length - 1) {
    activeTab.value = tabs.value[currentIndex + 1]
  }
}

function prevTab() {
  const currentIndex = tabs.value.indexOf(activeTab.value)
  if (currentIndex > 0) {
    activeTab.value = tabs.value[currentIndex - 1]
  }
}

async function save() {
  if (!validateForm()) return

  isSaving.value = true
  try {
    const { data: newItem } = await axios.post(`http://localhost:8000/${props.tableName}`, form.value)

    if (props.tableName === 'produits') {
      // Sauvegarde des incompatibilités produits
      for (const pid of incompatibilitesProduits.value) {
        await axios.post('http://localhost:8000/produit-incompatibilites', {
          produit_id_1: newItem.id,
          produit_id_2: pid
        })
      }

      // Sauvegarde des compatibilités robots
      for (const rid of compatibilitesRobots.value) {
        await axios.post('http://localhost:8000/robot-produit-compatibilites', {
          robot_id: rid,
          produit_id: newItem.id
        })
      }

      // Sauvegarde des prix produits
      for (const cid in prix.value) {
        await axios.post('http://localhost:8000/prix', {
          produit_id: newItem.id,
          client_id: parseInt(cid),
          prix_produit: prix.value[cid].prix_produit,
          prix_transport: prix.value[cid].prix_transport,
          commentaire: prix.value[cid].commentaire
        })
      }
    }

    if (props.tableName === 'robots') {
      if (compatibilitesProduits.value.length) {
        await axios.post(`http://localhost:8000/robots/${newItem.id}/batch-compatibilites`, compatibilitesProduits.value)
      }

      await axios.post('http://localhost:8000/prix_robot', {
        id: newItem.id,
        reference: newItem.reference,
        prix_robot: prixRobot.value.prix_robot,
        prix_transport: prixRobot.value.prix_transport,
        commentaire: prixRobot.value.commentaire
      })
    }

    showSuccess.value = true
    setTimeout(() => {
      emit('created', newItem)
      closeModal()
    }, 1500)

  } catch (error) {
    console.error('Erreur lors de la sauvegarde:', error)
  } finally {
    isSaving.value = false
  }
}

function closeModal() {
  emit('close')
  // Reset form
  setTimeout(() => {
    form.value = {}
    activeTab.value = 'Informations'
    showSuccess.value = false
    errors.value = {}
  }, 300)
}

onMounted(async () => {
  if (props.isOpen) {
    await loadData()
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal-backdrop">
      <div v-if="modalVisible" class="modal-overlay">
        <Transition name="modal-content">
          <div v-if="contentVisible" class="modal-container">
            <!-- Header with progress -->
            <div class="modal-header">
              <div class="header-content">
                <h2 class="modal-title">
                  <span class="title-icon">✨</span>
                  Ajouter {{ tableName }}
                </h2>
                <button @click="closeModal" class="close-btn">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </button>
              </div>
              <div class="progress-container">
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: currentStep + '%' }"></div>
                </div>
                <div class="step-indicators">
                  <span 
                    v-for="(tab, index) in tabs" 
                    :key="tab" 
                    class="step-indicator"
                    :class="{ active: activeTab === tab, completed: tabs.indexOf(activeTab) > index }"
                  >
                    {{ index + 1 }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Loading State -->
            <div v-if="isLoading" class="loading-container">
              <div class="loading-spinner"></div>
              <p>Chargement des données...</p>
            </div>

            <!-- Success State -->
            <Transition name="success">
              <div v-if="showSuccess" class="success-overlay">
                <div class="success-content">
                  <div class="success-icon">✅</div>
                  <h3>Créé avec succès !</h3>
                  <p>L'élément a été ajouté à la base de données.</p>
                </div>
              </div>
            </Transition>

            <!-- Main Content -->
            <div v-if="!isLoading && !showSuccess" class="modal-body">
              <!-- Tabs Navigation -->
              <nav class="tabs-nav">
                <button 
                  v-for="tab in tabs" 
                  :key="tab"
                  @click="switchTab(tab)"
                  class="tab-button"
                  :class="{ active: activeTab === tab }"
                >
                  <span class="tab-icon">
                    <template v-if="tab === 'Informations'">📝</template>
                    <template v-else-if="tab === 'Relations' || tab === 'Incompatibilités'">🔗</template>
                    <template v-else-if="tab === 'Tarification' || tab === 'Prix'">💰</template>
                  </span>
                  {{ tab }}
                </button>
              </nav>

              <!-- Tab Content -->
              <div class="tab-content">
                <!-- Informations Tab -->
                <Transition name="fade" mode="out-in">
                  <div v-if="activeTab === 'Informations'" class="info-section">
                    <div class="form-grid">
                      <div v-for="col in filteredColumns" :key="col" class="form-group">
                        <label class="form-label">
                          {{ col.charAt(0).toUpperCase() + col.slice(1) }}
                          <span class="required">*</span>
                        </label>
                        <div class="input-container">
                          <input 
                            v-model="form[col]" 
                            class="form-input"
                            :class="{ error: errors[col] }"
                            :placeholder="`Entrez ${col}...`"
                            @input="errors[col] = ''"
                          />
                          <Transition name="error">
                            <span v-if="errors[col]" class="error-message">
                              {{ errors[col] }}
                            </span>
                          </Transition>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Relations Tab -->
                  <div v-else-if="activeTab === 'Relations' || activeTab === 'Incompatibilités'" class="relations-section">
                    <div v-if="tableName === 'produits'" class="relations-content">
                      <!-- Incompatibilités produits -->
                      <div class="relation-group">
                        <div class="relation-header">
                          <h3 class="relation-title">
                            <span class="relation-icon">⚠️</span>
                            Produits incompatibles
                          </h3>
                          <button @click="toggleAllIncompatibilites" class="toggle-all-btn">
                            {{ incompatibilitesProduits.length === produitsList.length ? 'Désélectionner tout' : 'Sélectionner tout' }}
                          </button>
                        </div>
                        <div class="checkbox-grid">
                          <label v-for="p in produitsList" :key="p.id" class="checkbox-item">
                            <input 
                              type="checkbox" 
                              v-model="incompatibilitesProduits" 
                              :value="p.id"
                              class="checkbox-input"
                            />
                            <span class="checkbox-custom"></span>
                            <span class="checkbox-label">{{ p.nom }}</span>
                          </label>
                        </div>
                      </div>

                      <!-- Compatibilités robots -->
                      <div class="relation-group">
                        <div class="relation-header">
                          <h3 class="relation-title">
                            <span class="relation-icon">🤖</span>
                            Robots compatibles
                          </h3>
                          <button @click="toggleAllCompatibilitesRobots" class="toggle-all-btn">
                            {{ compatibilitesRobots.length === robotsList.length ? 'Désélectionner tout' : 'Sélectionner tout' }}
                          </button>
                        </div>
                        <div class="checkbox-grid">
                          <label v-for="r in robotsList" :key="r.id" class="checkbox-item">
                            <input 
                              type="checkbox" 
                              v-model="compatibilitesRobots" 
                              :value="r.id"
                              class="checkbox-input"
                            />
                            <span class="checkbox-custom"></span>
                            <span class="checkbox-label">{{ r.nom }}</span>
                          </label>
                        </div>
                      </div>
                    </div>

                    <div v-else-if="tableName === 'robots'" class="relations-content">
                      <div class="relation-group">
                        <div class="relation-header">
                          <h3 class="relation-title">
                            <span class="relation-icon">📦</span>
                            Produits compatibles
                          </h3>
                          <button @click="toggleAllCompatibilitesProduits" class="toggle-all-btn">
                            {{ compatibilitesProduits.length === produitsList.length ? 'Désélectionner tout' : 'Sélectionner tout' }}
                          </button>
                        </div>
                        <div class="checkbox-grid">
                          <label v-for="p in produitsList" :key="p.id" class="checkbox-item">
                            <input 
                              type="checkbox" 
                              v-model="compatibilitesProduits" 
                              :value="p.id"
                              class="checkbox-input"
                            />
                            <span class="checkbox-custom"></span>
                            <span class="checkbox-label">{{ p.nom }}</span>
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Pricing Tab -->
                  <div v-else-if="activeTab === 'Tarification' || activeTab === 'Prix'" class="pricing-section">
                    <!-- Produit pricing -->
                    <div v-if="tableName === 'produits'" class="pricing-content">
                      <div v-for="client in clientsList" :key="client.id" class="client-pricing">
                        <div class="client-header">
                          <h3 class="client-name">
                            <span class="client-icon">🏢</span>
                            {{ client.nom }}
                          </h3>
                        </div>
                        <div class="pricing-grid">
                          <div class="pricing-field">
                            <label>Prix produit (€)</label>
                            <input 
                              type="number" 
                              v-model="prix[client.id].prix_produit" 
                              class="pricing-input"
                              placeholder="0.00"
                              step="0.01"
                            />
                          </div>
                          <div class="pricing-field">
                            <label>Prix transport (€)</label>
                            <input 
                              type="number" 
                              v-model="prix[client.id].prix_transport" 
                              class="pricing-input"
                              placeholder="0.00"
                              step="0.01"
                            />
                          </div>
                          <div class="pricing-field full-width">
                            <label>Commentaire</label>
                            <textarea 
                              v-model="prix[client.id].commentaire" 
                              class="pricing-textarea"
                              placeholder="Commentaire optionnel..."
                              rows="2"
                            ></textarea>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div v-else-if="tableName === 'robots'" class="pricing-content">
                      <div class="robot-pricing">
                        <h3 class="pricing-title">
                          <span class="pricing-icon">💰</span>
                          Tarification du robot
                        </h3>
                        <div class="pricing-grid">
                          <div class="pricing-field">
                            <label>Prix robot (€)</label>
                            <input 
                              type="number" 
                              v-model="prixRobot.prix_robot" 
                              class="pricing-input"
                              placeholder="0.00"
                              step="0.01"
                            />
                          </div>
                          <div class="pricing-field">
                            <label>Prix transport (€)</label>
                            <input 
                              type="number" 
                              v-model="prixRobot.prix_transport" 
                              class="pricing-input"
                              placeholder="0.00"
                              step="0.01"
                            />
                          </div>
                          <div class="pricing-field full-width">
                            <label>Commentaire</label>
                            <textarea 
                              v-model="prixRobot.commentaire" 
                              class="pricing-textarea"
                              placeholder="Commentaire optionnel..."
                              rows="3"
                            ></textarea>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </Transition>
              </div>
            </div>

            <!-- Footer -->
            <div v-if="!isLoading && !showSuccess" class="modal-footer">
              <div class="navigation-buttons">
                <button 
                  @click="prevTab" 
                  class="nav-btn prev"
                  :disabled="tabs.indexOf(activeTab) === 0"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M15 18L9 12L15 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  Précédent
                </button>
                
                <button 
                  @click="nextTab" 
                  class="nav-btn next"
                  v-if="tabs.indexOf(activeTab) < tabs.length - 1"
                >
                  Suivant
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M9 18L15 12L9 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
              </div>

              <div class="action-buttons">
                <button @click="closeModal" class="cancel-btn">
                  Annuler
                </button>
                <button @click="save" class="save-btn" :disabled="isSaving">
                  <span v-if="isSaving" class="save-spinner"></span>
                  {{ isSaving ? 'Enregistrement...' : 'Enregistrer' }}
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* Base Styles */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-container {
  background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 24px;
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 20px 40px -20px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
}

/* Header */
.modal-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 24px 32px 16px;
  position: relative;
  overflow: hidden;
}

.modal-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Ccircle cx='30' cy='30' r='4'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E") repeat;
  pointer-events: none;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
}

.modal-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 32px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-8px); }
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 12px;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}

/* Progress */
.progress-container {
  margin-top: 20px;
  position: relative;
  z-index: 1;
}

.progress-bar {
  background: rgba(255, 255, 255, 0.2);
  height: 6px;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 16px;
}

.progress-fill {
  background: linear-gradient(90deg, #fff 0%, #f1c40f 100%);
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 10px rgba(241, 196, 15, 0.5);
}

.step-indicators {
  display: flex;
  justify-content: space-between;
}

.step-indicator {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
}

.step-indicator.active {
  background: #fff;
  color: #667eea;
  transform: scale(1.1);
}

.step-indicator.completed {
  background: #27ae60;
  color: white;
}

/* Loading */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 40px;
  color: #64748b;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #e2e8f0;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Success */
.success-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.success-content {
  text-align: center;
  padding: 40px;
}

.success-icon {
  font-size: 64px;
  margin-bottom: 20px;
  animation: bounce 0.6s ease;
}

@keyframes bounce {
  0%, 20%, 53%, 80%, 100% { transform: translate3d(0,0,0); }
  40%, 43% { transform: translate3d(0,-20px,0); }
  70% { transform: translate3d(0,-10px,0); }
  90% { transform: translate3d(0,-4px,0); }
}

.success-content h3 {
  color: #22c55e;
  font-size: 24px;
  margin-bottom: 10px;
}

.success-content p {
  color: #64748b;
  font-size: 16px;
}

/* Modal Body */
.modal-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Tabs Navigation */
.tabs-nav {
  display: flex;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  padding: 0 32px;
}

.tab-button {
  background: none;
  border: none;
  padding: 16px 24px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  color: #64748b;
  border-bottom: 3px solid transparent;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tab-button:hover {
  color: #334155;
  background: rgba(102, 126, 234, 0.05);
}

.tab-button.active {
  color: #667eea;
  border-bottom-color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

.tab-icon {
  font-size: 20px;
}

/* Tab Content */
.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
}

/* Info Section */
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-label {
  font-weight: 600;
  color: #334155;
  margin-bottom: 8px;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.required {
  color: #ef4444;
  margin-left: 4px;
}

.input-container {
  position: relative;
}

.form-input {
  width: 100%;
  padding: 16px 20px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 16px;
  transition: all 0.3s ease;
  background: #fff;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  transform: translateY(-2px);
}

.form-input.error {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.error-message {
  color: #ef4444;
  font-size: 12px;
  margin-top: 6px;
  display: block;
}

/* Relations Section */
.relations-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.relation-group {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.relation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.relation-title {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.relation-icon {
  font-size: 24px;
}

.toggle-all-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.toggle-all-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px -8px rgba(102, 126, 234, 0.5);
}

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 12px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.checkbox-item:hover {
  background: #f1f5f9;
  border-color: #e2e8f0;
}

.checkbox-input {
  display: none;
}

.checkbox-custom {
  width: 20px;
  height: 20px;
  border: 2px solid #cbd5e1;
  border-radius: 6px;
  position: relative;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.checkbox-input:checked + .checkbox-custom {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: #667eea;
}

.checkbox-input:checked + .checkbox-custom::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.checkbox-label {
  font-size: 15px;
  color: #334155;
  font-weight: 500;
}

/* Pricing Section */
.pricing-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.client-pricing, .robot-pricing {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.client-header {
  margin-bottom: 20px;
}

.client-name, .pricing-title {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.client-icon, .pricing-icon {
  font-size: 24px;
}

.pricing-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.pricing-field {
  display: flex;
  flex-direction: column;
}

.pricing-field.full-width {
  grid-column: 1 / -1;
}

.pricing-field label {
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
  font-size: 14px;
}

.pricing-input, .pricing-textarea {
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 16px;
  transition: all 0.3s ease;
  background: #fff;
}

.pricing-input:focus, .pricing-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.pricing-textarea {
  resize: vertical;
  min-height: 80px;
  font-family: inherit;
}

/* Footer */
.modal-footer {
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  padding: 20px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.navigation-buttons, .action-buttons {
  display: flex;
  gap: 12px;
}

.nav-btn {
  background: #fff;
  border: 2px solid #e2e8f0;
  color: #64748b;
  padding: 12px 20px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-btn:hover:not(:disabled) {
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-2px);
}

.nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cancel-btn {
  background: #fff;
  border: 2px solid #e5e7eb;
  color: #6b7280;
  padding: 14px 24px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cancel-btn:hover {
  border-color: #d1d5db;
  color: #374151;
}

.save-btn {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  border: none;
  color: white;
  padding: 14px 28px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 140px;
  justify-content: center;
}

.save-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -5px rgba(34, 197, 94, 0.4);
}

.save-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.save-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* Transitions */
.modal-backdrop-enter-active, .modal-backdrop-leave-active {
  transition: all 0.3s ease;
}

.modal-backdrop-enter-from, .modal-backdrop-leave-to {
  opacity: 0;
}

.modal-content-enter-active, .modal-content-leave-active {
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-content-enter-from, .modal-content-leave-to {
  opacity: 0;
  transform: scale(0.8) translateY(50px);
}

.fade-enter-active, .fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.success-enter-active, .success-leave-active {
  transition: all 0.4s ease;
}

.success-enter-from, .success-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

.error-enter-active, .error-leave-active {
  transition: all 0.3s ease;
}

.error-enter-from, .error-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Responsive Design */
@media (max-width: 768px) {
  .modal-container {
    margin: 10px;
    width: calc(100% - 20px);
    max-height: calc(100vh - 20px);
  }
  
  .modal-header {
    padding: 20px 24px 16px;
  }
  
  .modal-title {
    font-size: 24px;
  }
  
  .tab-content {
    padding: 24px 20px;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .checkbox-grid {
    grid-template-columns: 1fr;
  }
  
  .pricing-grid {
    grid-template-columns: 1fr;
  }
  
  .modal-footer {
    flex-direction: column;
    gap: 16px;
    padding: 16px 20px;
  }
  
  .navigation-buttons, .action-buttons {
    width: 100%;
    justify-content: center;
  }
  
  .tabs-nav {
    overflow-x: auto;
    padding: 0 20px;
  }
  
  .tab-button {
    white-space: nowrap;
    padding: 16px 20px;
  }
}

/* Dark theme support */
@media (prefers-color-scheme: dark) {
  .modal-container {
    background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
    color: #e2e8f0;
  }
  
  .tabs-nav {
    background: #334155;
    border-bottom-color: #475569;
  }
  
  .tab-button {
    color: #94a3b8;
  }
  
  .tab-button:hover {
    color: #e2e8f0;
    background: rgba(102, 126, 234, 0.1);
  }
  
  .form-input, .pricing-input, .pricing-textarea {
    background: #334155;
    border-color: #475569;
    color: #e2e8f0;
  }
  
  .form-input:focus, .pricing-input:focus, .pricing-textarea:focus {
    background: #3f4b5b;
  }
  
  .relation-group, .client-pricing, .robot-pricing {
    background: #334155;
    border-color: #475569;
  }
  
  .modal-footer {
    background: #334155;
    border-top-color: #475569;
  }
  
  .nav-btn, .cancel-btn {
    background: #475569;
    border-color: #64748b;
    color: #e2e8f0;
  }
}

/* Custom scrollbar */
.tab-content::-webkit-scrollbar {
  width: 8px;
}

.tab-content::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.tab-content::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
}

.tab-content::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6b4190 100%);
}

/* Animations for enhanced UX */
.checkbox-item {
  animation: fadeInUp 0.3s ease forwards;
  animation-delay: calc(var(--index, 0) * 0.05s);
  opacity: 0;
  transform: translateY(20px);
}

@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.form-group {
  animation: slideInLeft 0.4s ease forwards;
  animation-delay: calc(var(--index, 0) * 0.1s);
  opacity: 0;
  transform: translateX(-30px);
}

@keyframes slideInLeft {
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Focus management for accessibility */
.modal-container:focus-within .form-input:focus,
.modal-container:focus-within .pricing-input:focus,
.modal-container:focus-within .pricing-textarea:focus {
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

</style>