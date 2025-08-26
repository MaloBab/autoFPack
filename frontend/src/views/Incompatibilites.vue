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

const produits = ref<Produit[]>([])
const robots = ref<Robot[]>([])
const incompatibilitesProduits = ref<ProduitIncompatibilite[]>([])
const compatibilitesRobotProduit = ref<RobotProduitCompatibilite[]>([])

const activeTab = ref<'compatibilities' | 'incompatibilities'>('compatibilities')
const searchTerm = ref('')
const loading = ref(false)

const showCompatibilityModal = ref(false)
const showIncompatibilityModal = ref(false)
const selectedRobotDetail = ref<Robot | null>(null)
const selectedProductDetail = ref<Produit | null>(null)

const selectedRobotForCompatibility = ref<Robot | null>(null)
const selectedProductsForCompatibility = ref<Produit[]>([])
const selectedProductsForIncompatibility = ref<Produit[]>([])

const robotSearchTerm = ref('')
const productSearchTerm = ref('')
const incompatibilityProductSearchTerm = ref('')
const selectedProductForIncompatibility = ref<Produit | null>(null)
const selectedIncompatibleProducts = ref<Produit[]>([])
const incompatibilitySearchTerm = ref('')
const incompatibilityTargetSearchTerm = ref('')

const filteredProductsForSource = computed(() => {
  const term = incompatibilitySearchTerm.value.toLowerCase().trim()
  return availableProductsForIncompatibility.value.filter(product =>
    product.nom.toLowerCase().includes(term) ||
    product.reference.toLowerCase().includes(term) ||
    product.description?.toLowerCase().includes(term)
  )
})

const filteredProductsForTarget = computed(() => {
  const term = incompatibilityTargetSearchTerm.value.toLowerCase().trim()
  return availableProductsForIncompatibility.value.filter(product =>
    product.id !== selectedProductForIncompatibility.value?.id &&
    (
      product.nom.toLowerCase().includes(term) ||
      product.reference.toLowerCase().includes(term) ||
      product.description?.toLowerCase().includes(term)
    )
  )
})

function selectProductForIncompatibility(product:any) {
  selectedProductForIncompatibility.value = product
  incompatibilitySearchTerm.value = ''
  selectedIncompatibleProducts.value = []
}

function toggleIncompatibleProduct(product:any) {
  const index = selectedIncompatibleProducts.value.findIndex(p => p.id === product.id)
  if (index === -1) {
    selectedIncompatibleProducts.value.push(product)
  } else {
    selectedIncompatibleProducts.value.splice(index, 1)
  }
}


const animatedIncompatibility = ref<number | null>(null)

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

const filteredRobotsForModal = computed(() => {
  return robots.value.filter(robot => 
    robot.nom.toLowerCase().includes(robotSearchTerm.value.toLowerCase()) ||
    robot.generation.toLowerCase().includes(robotSearchTerm.value.toLowerCase()) ||
    robot.reference.toLowerCase().includes(robotSearchTerm.value.toLowerCase())
  )
})

const filteredProductsForModal = computed(() => {
  const term = productSearchTerm.value.trim().toLowerCase()
  return produits.value.filter(product =>
    product.nom.toLowerCase().includes(term) ||
    product.description?.toLowerCase().includes(term) ||
    product.reference.toLowerCase().includes(term)
  )
})

const filteredProductsForIncompatibilityModal = computed(() => {
  return produits.value.filter(product => 
    product.nom.toLowerCase().includes(incompatibilityProductSearchTerm.value.toLowerCase()) ||
    (product.description?.toLowerCase().includes(incompatibilityProductSearchTerm.value.toLowerCase())) ||
    product.reference.toLowerCase().includes(incompatibilityProductSearchTerm.value.toLowerCase())
  )
})

const availableProductsForCompatibility = computed(() => {
  if (!selectedRobotForCompatibility.value) return filteredProductsForModal.value
  
  const existingCompatibilities = compatibilitesRobotProduit.value
    .filter(comp => comp.robot_id === selectedRobotForCompatibility.value!.id)
    .map(comp => comp.produit_id)
  
  return filteredProductsForModal.value.filter(product => 
    !existingCompatibilities.includes(product.id)
  )
})

const availableProductsForIncompatibility = computed(() => {
  const selectedIds = selectedProductsForIncompatibility.value.map(p => p.id)
  const existingIncompatibilities = new Set<number>()
  
  selectedProductsForIncompatibility.value.forEach(selected => {
    incompatibilitesProduits.value.forEach(incomp => {
      if (incomp.produit_id_1 === selected.id) {
        existingIncompatibilities.add(incomp.produit_id_2)
      } else if (incomp.produit_id_2 === selected.id) {
        existingIncompatibilities.add(incomp.produit_id_1)
      }
    })
  })
  
  return filteredProductsForIncompatibilityModal.value.filter(product => 
    !selectedIds.includes(product.id) && !existingIncompatibilities.has(product.id)
  )
})

const filteredRobots = computed(() => {
  return robots.value.filter(robot => 
    robot.nom.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
    robot.generation.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
    robot.reference.toLowerCase().includes(searchTerm.value.toLowerCase())
  )
})

const productsWithIncompatibilities = computed(() => {
  const productsSet = new Set<number>()
  
  incompatibilitesProduits.value.forEach(incomp => {
    productsSet.add(incomp.produit_id_1)
    productsSet.add(incomp.produit_id_2)
  })
  
  return produits.value
    .filter(product => productsSet.has(product.id))
    .filter(product => {
      const search = searchTerm.value.toLowerCase()
      return product.nom.toLowerCase().includes(search) ||
        product.description?.toLowerCase().includes(search) ||
        product.reference.toLowerCase().includes(search)
    })
})

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

const getIncompatibleProducts = (productId: number) => {
  const incompatibleIds = new Set<number>()
  
  incompatibilitesProduits.value.forEach(incomp => {
    if (incomp.produit_id_1 === productId) {
      incompatibleIds.add(incomp.produit_id_2)
    } else if (incomp.produit_id_2 === productId) {
      incompatibleIds.add(incomp.produit_id_1)
    }
  })
  
  return produits.value.filter(produit => incompatibleIds.has(produit.id))
}

const getIncompatibilityCount = (productId: number) => {
  return getIncompatibleProducts(productId).length
}

const selectRobot = (robot: Robot) => {
  selectedRobotDetail.value = robot
}

const selectProduct = (product: Produit) => {
  selectedProductDetail.value = product
}

const toggleProductSelectionForCompatibility = (product: Produit) => {
  const index = selectedProductsForCompatibility.value.findIndex(p => p.id === product.id)
  if (index > -1) {
    selectedProductsForCompatibility.value.splice(index, 1)
  } else {
    selectedProductsForCompatibility.value.push(product)
  }
}


const addCompatibility = async () => {
  if (!selectedRobotForCompatibility.value || selectedProductsForCompatibility.value.length === 0) return

  try {
    const productIds = selectedProductsForCompatibility.value.map(p => p.id)
    await axios.post(`http://localhost:8000/robots/${selectedRobotForCompatibility.value.id}/batch-compatibilites`, productIds)
    
    await fetchData()
    closeCompatibilityModal()
  } catch (error) {
    console.error('Erreur lors de l\'ajout des compatibilités:', error)
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

const addIncompatibilities = async () => {
  if (!selectedProductForIncompatibility.value || selectedIncompatibleProducts.value.length === 0) return

  try {
    const source = selectedProductForIncompatibility.value
    const targets = selectedIncompatibleProducts.value
    const incompatibilities:any[] = []

    for (const target of targets) {
      const exists = incompatibilitesProduits.value.some(incomp =>
        (incomp.produit_id_1 === source.id && incomp.produit_id_2 === target.id) ||
        (incomp.produit_id_1 === target.id && incomp.produit_id_2 === source.id)
      )

      if (!exists) {
        incompatibilities.push({
          produit_id_1: source.id,
          produit_id_2: target.id
        })
      }
    }

    for (const incomp of incompatibilities) {
      await axios.post('http://localhost:8000/produit-incompatibilites', incomp)
    }

    await fetchData()

    const newIndex = incompatibilitesProduits.value.length - incompatibilities.length
    animatedIncompatibility.value = newIndex
    setTimeout(() => {
      animatedIncompatibility.value = null
    }, 2000)

    closeIncompatibilityModal()
  } catch (error) {
    console.error("Erreur lors de l'ajout des incompatibilités :", error)
  }
}

const removeIncompatibility = async (productId: number, incompatibleProductId: number) => {
  try {
    const incomp = incompatibilitesProduits.value.find(i => 
      (i.produit_id_1 === productId && i.produit_id_2 === incompatibleProductId) ||
      (i.produit_id_1 === incompatibleProductId && i.produit_id_2 === productId)
    )
    
    if (incomp) {
      await axios.delete('http://localhost:8000/produit-incompatibilites', { data: incomp })
      await fetchData()
    }
  } catch (error) {
    console.error('Erreur lors de la suppression de l\'incompatibilité:', error)
  }
}

const removeAllIncompatibilities = async (productId: number) => {
  try {
    const incompatibilitiesToRemove = incompatibilitesProduits.value.filter(incomp =>
      incomp.produit_id_1 === productId || incomp.produit_id_2 === productId
    )

    for (const incomp of incompatibilitiesToRemove) {
      await axios.delete('http://localhost:8000/produit-incompatibilites', { data: incomp })
    }
    
    await fetchData()
    selectedProductDetail.value = null
  } catch (error) {
    console.error('Erreur lors de la suppression des incompatibilités:', error)
  }
}


const closeCompatibilityModal = () => {
  showCompatibilityModal.value = false
  selectedRobotForCompatibility.value = null
  selectedProductsForCompatibility.value = []
  robotSearchTerm.value = ''
  productSearchTerm.value = ''
}

const closeIncompatibilityModal = () => {
  showIncompatibilityModal.value = false
  selectedProductForIncompatibility.value = null
  selectedIncompatibleProducts.value = []
  incompatibilitySearchTerm.value = ''
  incompatibilityTargetSearchTerm.value = ''
}

onMounted(fetchData)
</script>

<template>
  <div class="compatibility-manager">
    <div class="header-container">
      <div class="header-glass">
        <div class="header-content">
          <div class="logo-section">
            <div class="logo-icon">⚡</div>
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

    <div v-show="activeTab === 'compatibilities'" class="content-section">
      <div class="section-header">
        <h2>Compatibilités Robot-Produit</h2>
        <button @click="showCompatibilityModal = true" class="add-btn primary">
          <span class="btn-icon">➕</span>
          <span class="btn-text">Ajouter des compatibilités</span>
        </button>
      </div>

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

    <div v-show="activeTab === 'incompatibilities'" class="content-section">
      <div class="section-header">
        <h2>Incompatibilités Produit-Produit</h2>
        <button @click="showIncompatibilityModal = true" class="add-btn danger">
          <span class="btn-icon">⚡</span>
          <span class="btn-text">Ajouter des incompatibilités</span>
        </button>
      </div>

      <div class="products-grid">
        <div 
          v-for="product in productsWithIncompatibilities" 
          :key="product.id" 
          class="product-card"
          @click="selectProduct(product)"
        >
          <div class="card-header">
            <div class="product-info">
              <div class="product-icon">📦</div>
              <div>
                <h3 class="product-name">{{ product.nom }}</h3>
                <p class="product-subtitle">Ref : <span class="product-subtitle-value">{{ product.reference }}</span></p>
                <p class="product-subtitle" v-if="product.description">{{ product.description }}</p>
              </div>
            </div>
            <div class="incompatibility-badge">
              {{ getIncompatibilityCount(product.id) }}
            </div>
          </div>

          <div class="incompatible-products">
            <div 
              v-for="produit in getIncompatibleProducts(product.id).slice(0, 3)" 
              :key="produit.id"
              class="product-chip incompatible"
            >
              {{ produit.nom }}
            </div>
            <div 
              v-if="getIncompatibleProducts(product.id).length > 3"
              class="product-chip more incompatible"
            >
              +{{ getIncompatibleProducts(product.id).length - 3 }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showCompatibilityModal" class="modal-overlay" @click="closeCompatibilityModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Ajouter des compatibilités</h3>
          <button @click="closeCompatibilityModal" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Robot</label>
            <div class="search-select-container">
              <input 
                v-model="robotSearchTerm" 
                type="text" 
                placeholder="🔍 Rechercher un robot..."
                class="search-input-modal"
                :disabled="selectedRobotForCompatibility !== null"
              >
              <div class="select-dropdown" v-if="robotSearchTerm || !selectedRobotForCompatibility">
                <div 
                  v-for="robot in filteredRobotsForModal" 
                  :key="robot.id"
                  class="select-option"
                  @click="selectedRobotForCompatibility = robot; robotSearchTerm = ''"
                >
                  <span class="option-main">{{ robot.nom }} {{ robot.generation }}</span>
                  <span class="option-sub">{{ robot.reference }}</span>
                </div>
              </div>
              <div v-if="selectedRobotForCompatibility && !robotSearchTerm" class="selected-item">
                <span>{{ selectedRobotForCompatibility.nom }} {{ selectedRobotForCompatibility.generation }}</span>
                <button @click="selectedRobotForCompatibility = null" class="remove-selected">✕</button>
              </div>
            </div>
          </div>

          <div class="form-group" v-if="selectedRobotForCompatibility">
            <label>Produits compatibles ({{ selectedProductsForCompatibility.length }} sélectionnés)</label>
            
            <div v-if="selectedProductsForCompatibility.length > 0" class="selected-products">
              <div 
                v-for="product in selectedProductsForCompatibility" 
                :key="product.id"
                class="selected-product-chip"
              >
                <span>{{ product.nom }}</span>
                <button @click="toggleProductSelectionForCompatibility(product)" class="remove-chip">✕</button>
              </div>
            </div>

            <div class="search-select-container">
              <input 
                v-model="productSearchTerm" 
                type="text" 
                placeholder="🔍 Rechercher des produits..."
                class="search-input-modal"
              >
              <div class="select-dropdown multi-select">
                <div 
                  v-for="product in availableProductsForCompatibility" 
                  :key="product.id"
                  class="select-option"
                  :class="{ 'selected': selectedProductsForCompatibility.some(p => p.id === product.id) }"
                  @click="toggleProductSelectionForCompatibility(product)"
                >
                  <div class="checkbox-container">
                    <div class="custom-checkbox" :class="{ 'checked': selectedProductsForCompatibility.some(p => p.id === product.id) }">
                      ✓
                    </div>
                  </div>
                  <div class="option-content">
                    <span class="option-main">{{ product.nom }}</span>
                    <span class="option-sub">{{ product.reference }} - {{ product.description }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeCompatibilityModal" class="btn secondary">Annuler</button>
          <button 
            @click="addCompatibility" 
            class="btn primary"
            :disabled="!selectedRobotForCompatibility || selectedProductsForCompatibility.length === 0"
          >
            Ajouter ({{ selectedProductsForCompatibility.length }})
          </button>
        </div>
      </div>
    </div>

    <div v-if="showIncompatibilityModal" class="modal-overlay" @click="closeIncompatibilityModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Ajouter des incompatibilités</h3>
          <button @click="closeIncompatibilityModal" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Produit source</label>
            <div class="search-select-container">
              <input 
                v-model="incompatibilitySearchTerm" 
                type="text" 
                placeholder="🔍 Rechercher un produit..."
                class="search-input-modal"
                :disabled="selectedProductForIncompatibility!==null"
              />
              <div class="select-dropdown" v-if="incompatibilitySearchTerm || !selectedProductForIncompatibility">
                <div 
                  v-for="product in filteredProductsForSource" 
                  :key="product.id"
                  class="select-option"
                  @click="selectProductForIncompatibility(product)"
                >
                  <span class="option-main">{{ product.nom }}</span>
                  <span class="option-sub">{{ product.reference }} - {{ product.description }}</span>
                </div>
              </div>
              <div v-if="selectedProductForIncompatibility && !incompatibilitySearchTerm" class="selected-item">
                <span>{{ selectedProductForIncompatibility.nom }}</span>
                <button @click="selectedProductForIncompatibility = null" class="remove-selected">✕</button>
              </div>
            </div>
          </div>

          <div class="form-group" v-if="selectedProductForIncompatibility">
            <label>Produits incompatibles ({{ selectedIncompatibleProducts.length }} sélectionnés)</label>
            
            <div v-if="selectedIncompatibleProducts.length > 0" class="selected-products">
              <div 
                v-for="product in selectedIncompatibleProducts" 
                :key="product.id"
                class="selected-product-chip"
              >
                <span>{{ product.nom }}</span>
                <button @click="toggleIncompatibleProduct(product)" class="remove-chip">✕</button>
              </div>
            </div>

            <div class="search-select-container">
              <input 
                v-model="incompatibilityTargetSearchTerm" 
                type="text" 
                placeholder="🔍 Rechercher des produits incompatibles..."
                class="search-input-modal"
              >
              <div class="select-dropdown multi-select">
                <div 
                  v-for="product in filteredProductsForTarget" 
                  :key="product.id"
                  class="select-option"
                  :class="{ 'selected': selectedIncompatibleProducts.some(p => p.id === product.id) }"
                  @click="toggleIncompatibleProduct(product)"
                >
                  <div class="checkbox-container">
                    <div class="custom-checkbox" :class="{ 'checked': selectedIncompatibleProducts.some(p => p.id === product.id) }">✓</div>
                  </div>
                  <div class="option-content">
                    <span class="option-main">{{ product.nom }}</span>
                    <span class="option-sub">{{ product.reference }} - {{ product.description }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeIncompatibilityModal" class="btn secondary">Annuler</button>
            <button 
              @click="addIncompatibilities" 
              class="btn danger"
              :disabled="!selectedProductForIncompatibility || selectedIncompatibleProducts.length === 0"
            >
              Ajouter ({{ selectedIncompatibleProducts.length }})
            </button>
        </div>
      </div>
    </div>

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

    <div v-if="selectedProductDetail" class="modal-overlay" @click="selectedProductDetail = null">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>{{ selectedProductDetail.nom }}</h3>
          <button @click="selectedProductDetail = null" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="product-details">
            <div class="product-info-detail">
              <p><strong>Référence :</strong> {{ selectedProductDetail.reference }}</p>
              <p v-if="selectedProductDetail.description"><strong>Description :</strong> {{ selectedProductDetail.description }}</p>
            </div>
            
            <div class="incompatibilities-section">
              <div class="section-title">
                <h4>Produits incompatibles ({{ getIncompatibleProducts(selectedProductDetail.id).length }})</h4>
                <button 
                  @click="removeAllIncompatibilities(selectedProductDetail.id)"
                  class="btn danger small"
                  v-if="getIncompatibleProducts(selectedProductDetail.id).length > 0"
                >
                  Supprimer tout
                </button>
              </div>
              
              <div class="incompatibilities-list">
                <div 
                  v-for="produit in getIncompatibleProducts(selectedProductDetail.id)" 
                  :key="produit.id"
                  class="incompatibility-detail-item"
                >
                  <div class="incompatible-product-info">
                    <span class="product-icon">📦</span>
                    <div class="product-text">
                      <span class="product-name">{{ produit.nom }}</span>
                      <span class="product-desc">{{ produit.reference }} - {{ produit.description }}</span>
                    </div>
                  </div>
                  <button 
                    @click="removeIncompatibility(selectedProductDetail.id, produit.id)"
                    class="remove-btn"
                  >
                    ✕
                  </button>
                </div>
              </div>
              
              <div v-if="getIncompatibleProducts(selectedProductDetail.id).length === 0" class="no-incompatibilities">
                <p>Aucune incompatibilité trouvée pour ce produit.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

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
  background: linear-gradient(135deg, #070707, #781212);
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
  color: #797979;
}

.stat-label {
  color: #666;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

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
  box-shadow: 0 10px 25px rgba(102, 234, 111, 0.3);
}

.incompatibility-btn.active {
  background: linear-gradient(135deg, #000000, #ec0606);
  box-shadow: 0 10px 25px rgba(234, 102, 102, 0.3);
}

.tab-btn.active {
  color: white;
  transform: translateY(-2px);
}

.tab-btn:hover:not(.active) {
  background: rgba(102, 126, 234, 0.1);
}

.tab-icon {
  font-size: 16px;
}

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

.search-input-modal:disabled {
  background-color: #e0e0e0;
  color: #888;
  cursor: not-allowed;
  border: 1px solid #ccc;
}

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
  background: linear-gradient(135deg, #2a2929, #04f610);
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
  background: #9ee7bc;
  border: 1px solid #1c8040;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.7rem;
  color: #64748b;
}

.product-chip.more {
  background: #038603;
  color: white;
  border-color: #038603;
}

.product-chip.incompatible {
  background: #fef2f2;
  border-color: #ef4444;
  color: #dc2626;
}

.product-chip.more.incompatible {
  background: #ef4444;
  color: white;
  border-color: #ef4444;
}

.products-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  overflow-y: auto;
  padding: 5px;
}

.product-card {
  background: white;
  border-radius: 15px;
  padding: 20px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
  border: 2px solid transparent;
  height: fit-content;
}

.product-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  border-color: #ef4444;
}

.product-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.product-icon {
  font-size: 24px;
}

.product-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: #333;
  margin: 0;
}

.product-subtitle {
  color: #666;
  margin: 3px 0 0 0;
  font-size: 0.8rem;
}

.product-subtitle-value {
  color: #000;
  font-size: 0.8rem;
}

.incompatibility-badge {
  background: linear-gradient(135deg, #7a0606, #ec0606);
  color: white;
  padding: 6px 10px;
  border-radius: 15px;
  font-size: 0.75rem;
  font-weight: 600;
}

.incompatible-products {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 15px;
}

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

.modal-overlay {
  position: fixed;
  inset: 0; 
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
  padding: 1rem;
  box-sizing: border-box;
}

.modal-content {
  background: white;
  border-radius: 20px;
  width: 100%;
  max-width: 600px;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
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
  display: flex;
  flex-direction: column;
  padding: 25px;
  height: 80%;
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

.form-help {
  color: #64748b;
  font-size: 0.8rem;
  margin: 5px 0 10px 0;
  font-style: italic;
}

.search-select-container {
  position: relative;
}

.search-input-modal {
  width: 100%;
  padding: 12px 16px;
  color: #000000;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 14px;
  background: white;
  outline: none;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.search-input-modal:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.select-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  border: 1px solid #e2e8f0;
  border-radius: 30px;
  flex: 1 1 auto ;
  overflow-y: auto;
  z-index: 10;
  margin-top: 5px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
}

.select-option {
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid #f8fafc;
  display: flex;
  align-items: center;
  gap: 10px;
}

.select-option:hover {
  background: #f8fafc;
}

.select-option:last-child {
  border-bottom: none;
}

.select-option.selected {
  background: #eff6ff;
  border-color: #dbeafe;
}

.checkbox-container {
  flex-shrink: 0;
}

.custom-checkbox {
  width: 18px;
  height: 18px;
  border: 2px solid #d1d5db;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: white;
  transition: all 0.2s ease;
}

.custom-checkbox.checked {
  background: #667eea;
  border-color: #667eea;
}

.option-content {
  flex: 1;
  min-width: 0;
}

.option-main {
  display: block;
  font-weight: 600;
  color: #333;
  font-size: 0.9rem;
}

.option-sub {
  display: block;
  color: #64748b;
  font-size: 0.8rem;
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #eff6ff;
  border: 2px solid #3b82f6;
  border-radius: 10px;
  font-size: 14px;
  color: #1e40af;
  font-weight: 600;
}

.remove-selected {
  background: #ef4444;
  color: white;
  border: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.remove-selected:hover {
  background: #dc2626;
  transform: scale(1.1);
}

.selected-products {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 15px;
  padding: 10px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  min-height: 45px;
  align-items: center;
}

.selected-product-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #667eea;
  color: white;
  padding: 6px 10px;
  border-radius: 15px;
  font-size: 0.8rem;
  font-weight: 500;
}

.remove-chip {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.remove-chip:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
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

.btn.small {
  padding: 6px 12px;
  font-size: 12px;
}

.btn.primary {
  background: linear-gradient(135deg, #5f6f5f, #1db62f);
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

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.robot-details h4 {
  font-size: 1.1rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 15px;
}

.products-list {
  display: grid;
  gap: 12px;
  height: 100%;
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

.product-details {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.product-info-detail {
  background: #f8fafc;
  border-radius: 10px;
  padding: 15px;
  margin-bottom: 20px;
  border: 1px solid #e2e8f0;
}

.product-info-detail p {
  margin: 8px 0;
  font-size: 0.9rem;
}

.product-info-detail strong {
  color: #374151;
}

.incompatibilities-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #f1f5f9;
}

.section-title h4 {
  font-size: 1.1rem;
  font-weight: 700;
  color: #333;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title h4::before {
  content: "⚡";
  font-size: 16px;
}

.incompatibilities-list {
  display: grid;
  gap: 2%;
  max-height: 500px;
  overflow-y: auto;
  padding-right: 5px;
  padding-top: 1%;
}

.incompatibility-detail-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 3rem;
  background: linear-gradient(135deg, #fef7f7, #fef2f2);
  border-radius: 15px;
  border: 2px solid #fee2e2;
  gap: 10px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.incompatibility-detail-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  border-radius: 0 2px 2px 0;
}

.incompatibility-detail-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(239, 68, 68, 0.15);
  border-color: #fecaca;
  background: linear-gradient(135deg, #fef2f2, #fef7f7);
}

.incompatible-product-info {
  display: flex;
  align-items: center;
  gap: 15px;
  flex: 1;
  min-width: 0;
}

.incompatible-product-info .product-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #fee2e2, #fecaca);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  border: 2px solid #fed7d7;
}

.incompatible-product-info .product-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.incompatible-product-info .product-name {
  font-weight: 700;
  color: #dc2626;
  font-size: 1rem;
  line-height: 1.2;
}

.incompatible-product-info .product-desc {
  color: #7f1d1d;
  font-size: 0.85rem;
  opacity: 0.8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.3;
}

.no-incompatibilities {
  text-align: center;
  padding: 40px 20px;
  background: linear-gradient(135deg, #f0fdf4, #f7fee7);
  border-radius: 20px;
  border: 2px dashed #d9f99d;
  margin-top: 20px;
}

.no-incompatibilities p {
  color: #16a34a;
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.no-incompatibilities p::before {
  content: "✅";
  font-size: 20px;
}

.modal-content.large {
  max-width: 800px;
  max-height: 90vh;
}

.modal-content.large .modal-body {
  padding: 30px;
}

.incompatibilities-list::-webkit-scrollbar,
.products-list::-webkit-scrollbar {
  width: 6px;
}

.incompatibilities-list::-webkit-scrollbar-track,
.products-list::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 10px;
}

.incompatibilities-list::-webkit-scrollbar-thumb,
.products-list::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  border-radius: 10px;
}

.incompatibilities-list::-webkit-scrollbar-thumb:hover,
.products-list::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #dc2626, #b91c1c);
}

.incompatibility-detail-item {
  animation: slideInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
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

.modal-header {
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  border-bottom: 2px solid #e2e8f0;
  position: relative;
}

.modal-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 25px;
  right: 25px;
  height: 2px;
  background: linear-gradient(90deg, transparent, #667eea, transparent);
}

.remove-btn {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.remove-btn:hover {
  background: linear-gradient(135deg, #dc2626, #b91c1c);
  transform: scale(1.1) rotate(90deg);
  box-shadow: 0 6px 16px rgba(239, 68, 68, 0.4);
}

.btn.danger.small {
  background: linear-gradient(135deg, #f50606, #ea580c);
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
}


.btn.danger.small:hover {
  background: linear-gradient(135deg, #ea580c, #dc2626);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(234, 88, 12, 0.3);
}

</style>