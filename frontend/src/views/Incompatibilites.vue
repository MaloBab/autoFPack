<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

interface Produit {
  id: number
  reference: string
  nom: string
  description?: string
}

interface Robot {
  id: number
  reference: string
  nom: string
  generation: string
}

interface ProduitIncompatibilite {
  produit_id_1: number
  produit_id_2: number
}

interface RobotProduitCompatibilite {
  robot_id: number
  produit_id: number
}

// Reactive data
const produits = ref<Produit[]>([])
const robots = ref<Robot[]>([])
const incompatibilitesProduits = ref<ProduitIncompatibilite[]>([])
const compatibilitesRobotProduit = ref<RobotProduitCompatibilite[]>([])

const activeTab = ref<'compatibilities' | 'incompatibilities'>('compatibilities')
const searchTerm = ref('')
const loading = ref(false)

// Modal states
const showCompatibilityModal = ref(false)
const showIncompatibilityModal = ref(false)
const selectedRobotDetail = ref<Robot | null>(null)

// Form states
const selectedRobotForCompatibility = ref<Robot | null>(null)
const selectedProductForCompatibility = ref<Produit | null>(null)
const selectedProduct1 = ref<Produit | null>(null)
const selectedProduct2 = ref<Produit | null>(null)

// Animation
const animatedIncompatibility = ref<number | null>(null)

// API calls
const fetchData = async () => {
  loading.value = true
  try {
    const [produitsRes, robotsRes, incompRes, compatRes] = await Promise.all([
      axios.get('http://localhost:8000/produits'),
      axios.get('http://localhost:8000/robots'),
      axios.get('http://localhost:8000/produit-incompatibilites'),
      axios.get('http://localhost:8000/robot-produit-compatibilites')
    ])

    produits.value = produitsRes.data.sort((a: Produit, b: Produit) => a.nom.localeCompare(b.nom))
    robots.value = robotsRes.data.sort((a: Robot, b: Robot) => a.nom.localeCompare(b.nom))
    incompatibilitesProduits.value = incompRes.data
    compatibilitesRobotProduit.value = compatRes.data
  } catch (error) {
    console.error('Erreur lors du chargement des données:', error)
  } finally {
    loading.value = false
  }
}

// Computed properties
const filteredRobots = computed(() => {
  return robots.value.filter(robot => 
    robot.nom.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
    robot.generation.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
    robot.reference.toLowerCase().includes(searchTerm.value.toLowerCase())
  )
})

const filteredIncompatibilities = computed(() => {
  return incompatibilitesProduits.value.filter(incomp => {
    const prod1 = produits.value.find(prod => prod.id === incomp.produit_id_1)
    const prod2 = produits.value.find(prod => prod.id === incomp.produit_id_2)
    const search = searchTerm.value.toLowerCase()
    return (prod1?.nom.toLowerCase().includes(search) || prod2?.nom.toLowerCase().includes(search)) ||
      (prod1?.description?.toLowerCase().includes(search) || prod2?.description?.toLowerCase().includes(search)) ||
      (prod1?.reference.toLowerCase().includes(search) || prod2?.reference.toLowerCase().includes(search))
  })
})

// Utility functions
const formatProduit = (id: number): string => {
  const p = produits.value.find(prod => prod.id === id)
  return p ? `${p.reference} | ${p.nom}${p.description ? ` - ${p.description.slice(0, 10)}${p.description.length > 10 ? '...' : ''}` : ''}` : `Produit ${id}`;
}

const getCompatibleProducts = (robotId: number) => {
  const compatibleIds = compatibilitesRobotProduit.value
    .filter(comp => comp.robot_id === robotId)
    .map(comp => comp.produit_id)
  
  return produits.value.filter(produit => compatibleIds.includes(produit.id))
}

const getCompatibilityPercentage = (robotId: number) => {
  const compatible = getCompatibleProducts(robotId).length
  const total = produits.value.length
  return total > 0 ? Math.round((compatible / total) * 100) : 0
}

// Actions
const selectRobot = (robot: Robot) => {
  selectedRobotDetail.value = robot
}

const addCompatibility = async () => {
  if (!selectedRobotForCompatibility.value || !selectedProductForCompatibility.value) return

  const exists = compatibilitesRobotProduit.value.some(comp =>
    comp.robot_id === selectedRobotForCompatibility.value!.id &&
    comp.produit_id === selectedProductForCompatibility.value!.id
  )

  if (exists) return

  try {
    await axios.post('http://localhost:8000/robot-produit-compatibilites', {
      robot_id: selectedRobotForCompatibility.value.id,
      produit_id: selectedProductForCompatibility.value.id
    })
    
    await fetchData()
    closeCompatibilityModal()
  } catch (error) {
    console.error('Erreur lors de l\'ajout de la compatibilité:', error)
  }
}

const removeCompatibility = async (robotId: number, produitId: number) => {
  try {
    await axios.delete('http://localhost:8000/robot-produit-compatibilites', {
      data: { robot_id: robotId, produit_id: produitId }
    })
    
    await fetchData()
  } catch (error) {
    console.error('Erreur lors de la suppression de la compatibilité:', error)
  }
}

const addIncompatibility = async () => {
  if (!selectedProduct1.value || !selectedProduct2.value || selectedProduct1.value === selectedProduct2.value) return

  const exists = incompatibilitesProduits.value.some(incomp =>
    (incomp.produit_id_1 === selectedProduct1.value!.id && incomp.produit_id_2 === selectedProduct2.value!.id) ||
    (incomp.produit_id_1 === selectedProduct2.value!.id && incomp.produit_id_2 === selectedProduct1.value!.id)
  )

  if (exists) return

  try {
    await axios.post('http://localhost:8000/produit-incompatibilites', {
      produit_id_1: selectedProduct1.value.id,
      produit_id_2: selectedProduct2.value.id
    })
    
    await fetchData()
    

    const newIndex = incompatibilitesProduits.value.length - 1
    animatedIncompatibility.value = newIndex
    setTimeout(() => {
      animatedIncompatibility.value = null
    }, 2000)
    
    closeIncompatibilityModal()
  } catch (error) {
    console.error('Erreur lors de l\'ajout de l\'incompatibilité:', error)
  }
}

const deleteIncompatibility = async (incomp: ProduitIncompatibilite) => {
  try {
    await axios.delete('http://localhost:8000/produit-incompatibilites', { data: incomp })
    incompatibilitesProduits.value = incompatibilitesProduits.value.filter(
      i => !(i.produit_id_1 === incomp.produit_id_1 && i.produit_id_2 === incomp.produit_id_2)
    )
  } catch (error) {
    console.error('Erreur lors de la suppression de l\'incompatibilité:', error)
  }
}

const closeCompatibilityModal = () => {
  showCompatibilityModal.value = false
  selectedRobotForCompatibility.value = null
  selectedProductForCompatibility.value = null
}

const closeIncompatibilityModal = () => {
  showIncompatibilityModal.value = false
  selectedProduct1.value = null
  selectedProduct2.value = null
}


onMounted(fetchData)
</script>

<template>
  <div class="compatibility-manager">
    <!-- Header Section -->
    <div class="header-container">
      <div class="header-glass">
        <div class="header-content">
          <div class="logo-section">
            <div class="logo-icon">⛔</div>
            <div>
              <h1 class="main-title">Gestionnaire de Compatibilités</h1>
            </div>
          </div>
          <div class="stats-mini">
            <div class="stat-item">
              <span class="stat-number">{{ robots.length }}</span>
              <span class="stat-label">Robots</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">{{ produits.length }}</span>
              <span class="stat-label">Produits</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="tabs-container">
      <div class="tabs-wrapper">
        <button 
          :class="['tab-btn', 'compatibility-btn', { active: activeTab === 'compatibilities' }]"
          @click="activeTab = 'compatibilities'"
        >
          <span class="tab-icon">✅</span>
          <span class="tab-text">Compatibilités Robot-Produit</span>
        </button>
        <button 
          :class="['tab-btn', 'incompatibility-btn', { active: activeTab === 'incompatibilities' }]"
          @click="activeTab = 'incompatibilities'"
        >
          <span class="tab-icon">❌</span>
          <span class="tab-text">Incompatibilités Produit-Produit</span>
        </button>
      </div>
    </div>

    <div class="search-section">
      <div class="search-container">
        <input 
          v-model="searchTerm" 
          type="text" 
          placeholder="🔍 Rechercher robots, produits..."
          class="search-input"
        >
      </div>
    </div>

    <!-- Compatibilities Tab -->
    <div v-show="activeTab === 'compatibilities'" class="content-section">
      <div class="section-header">
        <h2>Compatibilités Robot-Produit</h2>
        <button @click="showCompatibilityModal = true" class="add-btn primary">
          <span class="btn-icon">➕</span>
          <span class="btn-text">Ajouter une compatibilité</span>
        </button>
      </div>

      <!-- Robot Cards Grid -->
      <div class="robots-grid">
        <div 
          v-for="robot in filteredRobots" 
          :key="robot.id" 
          class="robot-card"
          @click="selectRobot(robot)"
        >
          <div class="card-header">
            <div class="robot-info">
              <div class="robot-icon">🤖</div>
              <div>
                <h3 class="robot-name">{{ robot.nom }}</h3>
                <p class="robot-subtitle">Ref : <span class="robot-subtitle-value">{{ robot.reference }}</span></p>
                <p class="robot-subtitle">Génération : <span class="robot-subtitle-value">{{ robot.generation }}</span></p>
              </div>
            </div>
            <div class="compatibility-badge">
              {{ getCompatibleProducts(robot.id).length }} / {{ produits.length }}
            </div>
          </div>

          <div class="compatibility-bar">
            <div 
              class="compatibility-fill" 
              :style="{ width: getCompatibilityPercentage(robot.id) + '%' }"
              
            ></div>
          </div>

          <div class="compatible-products">
            <div 
              v-for="produit in getCompatibleProducts(robot.id).slice(0, 3)" 
              :key="produit.id"
              class="product-chip"
            >
              {{ produit.nom }}
            </div>
            <div 
              v-if="getCompatibleProducts(robot.id).length > 3"
              class="product-chip more"
            >
              +{{ getCompatibleProducts(robot.id).length - 3 }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Incompatibilities Tab -->
    <div v-show="activeTab === 'incompatibilities'" class="content-section">
      <div class="section-header">
        <h2>Incompatibilités Produit-Produit</h2>
        <button @click="showIncompatibilityModal = true" class="add-btn danger">
          <span class="btn-icon">⚠️</span>
          <span class="btn-text">Ajouter une incompatibilité</span>
        </button>
      </div>

      <!-- Incompatibilities List -->
      <div class="incompatibilities-grid">
        <div 
          v-for="(incomp, index) in filteredIncompatibilities" 
          :key="`${incomp.produit_id_1}-${incomp.produit_id_2}`"
          class="incompatibility-card"
          :class="{ 'highlight': animatedIncompatibility === index }"
        >
          <div class="incomp-content">
            <div class="product-item">
              <span class="product-icon">📦</span>
              <span class="product-name">{{ formatProduit(incomp.produit_id_1) }}</span>
            </div>
            <div class="incomp-separator">⚡</div>
            <div class="product-item">
              <span class="product-icon">📦</span>
              <span class="product-name">{{ formatProduit(incomp.produit_id_2) }}</span>
            </div>
          </div>
          <button 
            @click="deleteIncompatibility(incomp)"
            class="delete-btn"
          >
            🗑️
          </button>
        </div>
      </div>
    </div>

    <!-- Compatibility Modal -->
    <div v-if="showCompatibilityModal" class="modal-overlay" @click="closeCompatibilityModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Ajouter une compatibilité</h3>
          <button @click="closeCompatibilityModal" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Robot</label>
            <select v-model="selectedRobotForCompatibility" class="custom-select">
              <option value="">Sélectionner un robot</option>
              <option v-for="robot in robots" :key="robot.id" :value="robot">
                {{ robot.nom }} {{ robot.generation }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>Produit</label>
            <select v-model="selectedProductForCompatibility" class="custom-select">
              <option value="">Sélectionner un produit</option>
              <option v-for="produit in produits" :key="produit.id" :value="produit">
                {{ produit.nom }} - {{ produit.description || '' }}
              </option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeCompatibilityModal" class="btn secondary">Annuler</button>
          <button @click="addCompatibility" class="btn primary">Ajouter</button>
        </div>
      </div>
    </div>

    <!-- Incompatibility Modal -->
    <div v-if="showIncompatibilityModal" class="modal-overlay" @click="closeIncompatibilityModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Ajouter une incompatibilité</h3>
          <button @click="closeIncompatibilityModal" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Premier produit</label>
            <select v-model="selectedProduct1" class="custom-select">
              <option value="">Sélectionner un produit</option>
              <option v-for="produit in produits" :key="produit.id" :value="produit">
                {{ produit.nom }} - {{ produit.description || '' }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>Deuxième produit</label>
            <select v-model="selectedProduct2" class="custom-select">
              <option value="">Sélectionner un produit</option>
              <option v-for="produit in produits" :key="produit.id" :value="produit">
                {{ produit.nom }} - {{ produit.description || '' }}
              </option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeIncompatibilityModal" class="btn secondary">Annuler</button>
          <button @click="addIncompatibility" class="btn danger">Ajouter</button>
        </div>
      </div>
    </div>

    <!-- Robot Detail Modal -->
    <div v-if="selectedRobotDetail" class="modal-overlay" @click="selectedRobotDetail = null">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>{{ selectedRobotDetail.nom }} {{ selectedRobotDetail.generation }}</h3>
          <button @click="selectedRobotDetail = null" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="robot-details">
            <h4>Produits compatibles ({{ getCompatibleProducts(selectedRobotDetail.id).length }})</h4>
            <div class="products-list">
              <div 
                v-for="produit in getCompatibleProducts(selectedRobotDetail.id)" 
                :key="produit.id"
                class="product-detail-item"
              >
                <span class="product-name">{{ produit.nom }}</span>
                <span class="product-desc">{{ produit.description }}</span>
                <button 
                  @click="removeCompatibility(selectedRobotDetail.id, produit.id)"
                  class="remove-btn"
                >
                  ✕
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading Overlay -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner">⚡</div>
    </div>
  </div>
</template>

<style scoped>
.compatibility-manager {
  height: 86vh;
  background: #f7f7f7;
  padding: 15px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header-container {
  flex-shrink: 0;
  margin-bottom: 15px;
}

.header-glass {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 15px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

.logo-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #dcdcdc, #6f6f6f);
  border-radius: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.main-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0;
}

.stats-mini {
  display: flex;
  gap: 30px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 1.8rem;
  font-weight: 700;
  color: #667eea;
}

.stat-label {
  color: #666;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Tabs */
.tabs-container {
  flex-shrink: 0;
  margin-bottom: 15px;
}

.tabs-wrapper {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 15px;
  padding: 8px;
  display: flex;
  gap: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.tab-btn {
  flex: 1;
  padding: 12px 20px;
  border: none;
  background: transparent;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.compatibility-btn.active {
  background: linear-gradient(135deg, #000000, #04f610);
}

.incompatibility-btn.active {
  background: linear-gradient(135deg, #000000, #ec0606);
}

.tab-btn.active {
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
}

.tab-btn:hover:not(.active) {
  background: rgba(102, 126, 234, 0.1);
}

.tab-icon {
  font-size: 16px;
}

/* Search */
.search-section {
  flex-shrink: 0;
  margin-bottom: 15px;
}

.search-container {
  display: flex;
  justify-content: center;
}

.search-input {
  width: 100%;
  padding: 15px 20px;
  font-size: 16px;
  border: none;
  border-radius: 15px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  outline: none;
  transition: all 0.3s ease;
}

.search-input:focus {
  transform: translateY(-2px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

/* Content Section */
.content-section {
  flex: 1;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.section-header {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.section-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #333;
  margin: 0;
}

/* Buttons */
.add-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.add-btn.primary {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
}

.add-btn.danger {
  background: linear-gradient(135deg, #7a0606, #ec0606);
  color: white;
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.btn-icon {
  font-size: 14px;
}

.robots-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  overflow-y: auto;
  padding: 5px;
}

.robot-card {
  background: white;
  border-radius: 15px;
  padding: 20px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
  border: 2px solid transparent;
  height: fit-content;
}

.robot-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  border-color: #667eea;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.robot-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.robot-icon {
  font-size: 24px;
}

.robot-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: #333;
  margin: 0;
}

.robot-subtitle {
  color: #666;
  margin: 3px 0 0 0;
  font-size: 0.8rem;
}

.robot-subtitle-value {
  color: #000;
  font-size: 0.8rem;
}

.compatibility-badge {
  background: linear-gradient(135deg, #254a2c, #0af043);
  color: white;
  padding: 6px 10px;
  border-radius: 15px;
  font-size: 0.75rem;
  font-weight: 600;
}

.compatibility-bar {
  width: 100%;
  height: 6px;
  background: #f1f5f9;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 15px;
}

.compatibility-fill {
  height: 100%;
  background: linear-gradient(135deg, #10b981, #059669);
  transition: width 0.3s ease;
}

.compatible-products {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.product-chip {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.7rem;
  color: #64748b;
}

.product-chip.more {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

/* Incompatibilities Grid */
.incompatibilities-grid {
  flex: 1;
  display: grid;
  gap: 15px;
  overflow-y: auto;
  padding: 5px;
}

.incompatibility-card {
  background: white;
  border-radius: 15px;
  padding: 20px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.3s ease;
  height: fit-content;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  min-width: 0;
}

.incompatibility-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
}

.incompatibility-card.highlight {
  animation: glow 2s ease-in-out;
}

@keyframes glow {
  0% { background: #fef2f2; border-color: #ef4444; }
  100% { background: white; border-color: transparent; }
}

.incomp-content {
  display: flex;
  align-items: center;
  gap: 15px;
  flex: 1;
  min-width: 0;
}

.product-item {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.product-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.product-name {
  font-weight: 600;
  color: #333;
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.incomp-separator {
  font-size: 16px;
  color: #ef4444;
  flex-shrink: 0;
}

.delete-btn {
  background: linear-gradient(135deg, #7a0606, #ec0606);
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  flex-shrink: 0;
}

.delete-btn:hover {
  background: linear-gradient(135deg, #530404, #a40505);
  transform: scale(1.05);
}

/* Modals */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.modal-content {
  background: white;
  border-radius: 20px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
}

.modal-content.large {
  max-width: 700px;
}

.modal-header {
  padding: 20px 25px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.modal-header h3 {
  font-size: 1.3rem;
  font-weight: 700;
  color: #333;
  margin: 0;
}

.close-btn {
  background: #f1f5f9;
  border: none;
  width: 35px;
  height: 35px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: #64748b;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: #e2e8f0;
  color: #374151;
}

.modal-body {
  padding: 25px;
  flex: 1;
  overflow-y: auto;
}

.modal-footer {
  padding: 15px 25px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  flex-shrink: 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-weight: 600;
  color: #374151;
  margin-bottom: 6px;
  font-size: 0.9rem;
}

.custom-select {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 14px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
  appearance: none;
  background-position: right 12px center;
  background-repeat: no-repeat;
  background-size: 16px;
  padding-right: 45px;
}

.custom-select:focus {
  border-color: #667eea;
  outline: none;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 13px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.btn.primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.btn.secondary {
  background: #f8fafc;
  color: #64748b;
  border: 1px solid #e2e8f0;
}

.btn.danger {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Robot Details */
.robot-details h4 {
  font-size: 1.1rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 15px;
}

.products-list {
  display: grid;
  gap: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.product-detail-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  gap: 10px;
  min-width: 0;
}

.product-detail-item .product-name {
  font-weight: 600;
  color: #333;
  font-size: 0.9rem;
}

.product-detail-item .product-desc {
  color: #64748b;
  font-size: 0.8rem;
  margin-left: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-btn {
  background: #ef4444;
  color: white;
  border: none;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.remove-btn:hover {
  background: #dc2626;
  transform: scale(1.1);
}

/* Loading */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(10px);
}

.loading-spinner {
  font-size: 3rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}


</style>