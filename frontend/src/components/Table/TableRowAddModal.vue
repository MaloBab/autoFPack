<script setup lang="ts">
import { ref, type Ref, onMounted, computed, watch, nextTick } from 'vue'
import axios from 'axios'

const props = defineProps<{
  isOpen: boolean
  tableName: string 
}>()
const emit = defineEmits(['close', 'added'])

const form: Ref<Record<string, any>> = ref({})
const columns: Ref<string[]> = ref([])
const tabs: Ref<string[]> = ref(['Informations'])
const activeTab: Ref<string> = ref('Informations')
const isLoading = ref(false)
const isSaving = ref(false)
const errors: Ref<Record<string, string>> = ref({})
const showSuccess = ref(false)

const modalVisible = ref(false)
const contentVisible = ref(false)

const filteredColumns = computed(() => {
  let cols = columns.value.filter(col => col !== 'id')
  
  if (props.tableName === 'prix_robot') {
    cols = cols.filter(col => col !== 'robot')
    const refIndex = cols.findIndex(col => col.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '') === 'reference')
    if (refIndex !== -1) {
      cols.splice(refIndex + 1, 0, 'robot')
    }
  }
  
  // Trier les colonnes pour mettre "reference" en premier (insensible à la casse et accents)
  return cols.sort((a, b) => {
    const normalize = (s: string) => s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')

    const aNorm = normalize(a)
    const bNorm = normalize(b)

    // Priorités : reference > robot > reste
    const priority = (col: string) => {
      if (col === 'reference') return 2
      if (col === 'robot') return 1
      return 0
    }

    const aPriority = priority(aNorm)
    const bPriority = priority(bNorm)

    return bPriority - aPriority // tri décroissant : 2 (reference) en premier, puis 1 (robot)
  })
})

const produitsList: Ref<any[]> = ref([])
const robotsList: Ref<any[]> = ref([])
const clientsList: Ref<any[]> = ref([])
const fournisseursList: Ref<any[]> = ref([])
const fpacksList: Ref<any[]> = ref([])

const incompatibilitesProduits: Ref<any[]> = ref([])
const compatibilitesRobots: Ref<any[]> = ref([])
const compatibilitesProduits: Ref<any[]> = ref([])

const prix: Ref<Record<number, any>> = ref({})
const prixRobot: Ref<any> = ref({
  prix_robot: null,
  prix_transport: null,
  commentaire: ''
})

// États pour les filtres des selects
const searchTerms: Ref<Record<string, string>> = ref({})
const showDropdowns: Ref<Record<string, boolean>> = ref({})

// États pour les barres de recherche des relations
const searchIncompatibilites = ref('')
const searchCompatibilitesRobots = ref('')
const searchCompatibilitesProduits = ref('')

const currentStep = computed(() => {
  const stepIndex = tabs.value.indexOf(activeTab.value)
  return ((stepIndex + 1) / tabs.value.length) * 100
})

// Fonction pour nettoyer les noms des colonnes
const cleanColumnName = (columnName: string) => {
  // Pour la colonne virtuelle 'robot'
  if (columnName === 'robot') {
    return 'Robot'
  }
  
  // Enlever "_id" à la fin
  let cleaned = columnName.replace(/_id$/i, '')
  
  // Enlever "id" au début ou à la fin (case insensitive)
  cleaned = cleaned.replace(/^id_?/i, '').replace(/_?id$/i, '')
  
  // Si après nettoyage il ne reste rien, garder le nom original
  if (!cleaned.trim()) {
    cleaned = columnName
  }
  
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1)
}

// Fonction pour déterminer si un champ est une clé étrangère ou un select spécial
const isForeignKey = (columnName: string) => {
  const foreignKeys = [
    'fournisseur_id', 'client_id', 'client', 'produit_id', 'fpack_id'
  ]
  
  // Pour prix_robot, 'reference' et 'robot' sont des selects spéciaux
  if (props.tableName === 'prix_robot' && (columnName === 'reference' || columnName === 'robot')) {
    return true
  }
  
  return foreignKeys.includes(columnName)
}

// Fonction pour obtenir les options d'un select
const getSelectOptions = (columnName: string) => {
  switch (columnName) {
    case 'fournisseur_id':
      return fournisseursList.value
    case 'client_id':
    case 'client':
      return clientsList.value
    case 'produit_id':
      return produitsList.value
    case 'fpack_id':
      return fpacksList.value
    default:
      // Pour prix_robot, 'reference' et 'robot' utilisent la liste des robots
      if (props.tableName === 'prix_robot' && (columnName === 'reference' || columnName === 'robot')) {
        return robotsList.value
      }
      return []
  }
}

// Fonction pour filtrer les options
const getFilteredOptions = (columnName: string) => {
  const options = getSelectOptions(columnName)
  const searchTerm = searchTerms.value[columnName]?.toLowerCase() || ''
  
  if (!searchTerm) return options
  
  return options.filter(option => {
    if (props.tableName === 'prix_robot' && columnName === 'reference') {
      return option.reference?.toLowerCase().includes(searchTerm)
    } else if (props.tableName === 'prix_robot' && columnName === 'robot') {
      return option.nom?.toLowerCase().includes(searchTerm)
    }
    
    return option.nom?.toLowerCase().includes(searchTerm) ||
           option.reference?.toLowerCase().includes(searchTerm)
  })
}

// Fonctions pour filtrer les listes dans les relations
const filteredProduitsList = computed(() => {
  if (!searchIncompatibilites.value) return produitsList.value
  return produitsList.value.filter(produit => 
    produit.nom?.toLowerCase().includes(searchIncompatibilites.value.toLowerCase()) ||
    produit.reference?.toLowerCase().includes(searchIncompatibilites.value.toLowerCase())
  )
})

const filteredRobotsList = computed(() => {
  if (!searchCompatibilitesRobots.value) return robotsList.value
  return robotsList.value.filter(robot => 
    robot.nom?.toLowerCase().includes(searchCompatibilitesRobots.value.toLowerCase()) ||
    robot.reference?.toLowerCase().includes(searchCompatibilitesRobots.value.toLowerCase())
  )
})

const filteredProduitsForRobots = computed(() => {
  if (!searchCompatibilitesProduits.value) return produitsList.value
  return produitsList.value.filter(produit => 
    produit.nom?.toLowerCase().includes(searchCompatibilitesProduits.value.toLowerCase()) ||
    produit.reference?.toLowerCase().includes(searchCompatibilitesProduits.value.toLowerCase())
  )
})

// Fonction pour obtenir le label d'une option
const getOptionLabel = (option: any, columnName: string) => {
  if (props.tableName === 'prix_robot') {
    if (columnName === 'reference') {
      return option.reference || ''
    } else if (columnName === 'robot') {
      return option.nom || ''
    }
  }
  return option.nom || option.reference || option.id
}

// Fonction pour toggle le dropdown
const toggleDropdown = (columnName: string) => {
  showDropdowns.value[columnName] = !showDropdowns.value[columnName]
}

// Fonction pour sélectionner une option avec synchronisation pour prix_robot
const selectOption = (columnName: string, option: any) => {
  if (props.tableName === 'prix_robot') {
    if (columnName === 'reference') {
      // Sélection par référence -> synchroniser avec robot
      form.value['reference'] = option.reference
      form.value['robot'] = option.nom
      form.value['id'] = option.id // Stocker l'ID du robot
      
      searchTerms.value['reference'] = option.reference
      searchTerms.value['robot'] = option.nom
    } else if (columnName === 'robot') {
      // Sélection par nom de robot -> synchroniser avec référence
      form.value['robot'] = option.nom
      form.value['reference'] = option.reference
      form.value['id'] = option.id // Stocker l'ID du robot
      
      searchTerms.value['robot'] = option.nom
      searchTerms.value['reference'] = option.reference
    }
  } else {
    // Logique normale pour les autres tables
    form.value[columnName] = option.id
    searchTerms.value[columnName] = getOptionLabel(option, columnName)
  }
  
  showDropdowns.value[columnName] = false
}

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
    
    // Initialiser le formulaire
    columns.value.forEach(col => {
      form.value[col] = ''
      searchTerms.value[col] = ''
      showDropdowns.value[col] = false
    })

    // Pour prix_robot, initialiser aussi les champs virtuels
    if (props.tableName === 'prix_robot') {
      searchTerms.value['robot'] = ''
      showDropdowns.value['robot'] = false
    }

    // Charger toutes les données de référence
    const [produitsRes, robotsRes, clientsRes, fournisseursRes, fpacksRes] = await Promise.all([
      axios.get('http://localhost:8000/produits'),
      axios.get('http://localhost:8000/robots'),
      axios.get('http://localhost:8000/clients'),
      axios.get('http://localhost:8000/fournisseurs'),
      axios.get('http://localhost:8000/fpacks')
    ])
    
    produitsList.value = produitsRes.data
    robotsList.value = robotsRes.data
    clientsList.value = clientsRes.data
    fournisseursList.value = fournisseursRes.data
    fpacksList.value = fpacksRes.data

    if (['produits', 'robots'].includes(props.tableName)) {
      tabs.value = ['Informations', 'Relations', 'Tarification']
      
      if (props.tableName === 'produits') {
        clientsList.value.forEach(c => {
          prix.value[c.id] = { prix_produit: null, prix_transport: null, commentaire: '' }
        })
      } else if (props.tableName === 'robots') {
        prixRobot.value = { prix_robot: null, prix_transport: null, commentaire: '' }
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
    if (col === 'commentaire') return
    
    // Pour prix_robot, on vérifie que l'ID du robot est bien défini
    if (props.tableName === 'prix_robot' && (col === 'reference' || col === 'robot')) {
      if (!form.value['id']) {
        errors.value[col] = 'Ce champ est requis'
        isValid = false
      }
      return
    }
    
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
  toggleAll(filteredProduitsList.value, incompatibilitesProduits)
}

function toggleAllCompatibilitesRobots() {
  toggleAll(filteredRobotsList.value, compatibilitesRobots)
}

function toggleAllCompatibilitesProduits() {
  toggleAll(filteredProduitsForRobots.value, compatibilitesProduits)
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
      for (const pid of incompatibilitesProduits.value) {
        await axios.post('http://localhost:8000/produit-incompatibilites', {
          produit_id_1: newItem.id,
          produit_id_2: pid
        })
      }

      for (const rid of compatibilitesRobots.value) {
        await axios.post('http://localhost:8000/robot-produit-compatibilites', {
          robot_id: rid,
          produit_id: newItem.id
        })
      }

      for (const cid in prix.value) {
        if (!prix.value[cid].prix_produit && !prix.value[cid].prix_transport) continue
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

      if (prixRobot.value.prix_robot || prixRobot.value.prix_transport) {
      await axios.post('http://localhost:8000/prix_robot', {
        id: newItem.id,
        reference: newItem.reference,
        prix_robot: prixRobot.value.prix_robot,
        prix_transport: prixRobot.value.prix_transport,
        commentaire: prixRobot.value.commentaire
      })
    }
    }

    showSuccess.value = true
    setTimeout(() => {
      emit('added', newItem)
      closeModal()
    }, 1500)

  } catch (error) {
    console.error('Erreur lors de la sauvegarde:', error)
  } finally {
    isSaving.value = false
  }
}

const hideDropdown = (col: string, time: number) => {
  setTimeout(() => {
    showDropdowns.value[col] = false
  }, time)
}

function closeModal() {
  emit('close')
  setTimeout(() => {
    form.value = {}
    searchTerms.value = {}
    showDropdowns.value = {}
    activeTab.value = 'Informations'
    showSuccess.value = false
    errors.value = {}
    // Réinitialiser les barres de recherche des relations
    searchIncompatibilites.value = ''
    searchCompatibilitesRobots.value = ''
    searchCompatibilitesProduits.value = ''
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
            <div class="modal-header">
              <div class="header-content">
                <h2 class="modal-title">
                  <span class="title-icon">➕</span>
                  Ajouter {{ tableName }}
                </h2>
                <button @click="closeModal" class="close-btn">X</button>
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

            <div v-if="isLoading" class="loading-container">
              <div class="loading-spinner"></div>
              <p>Chargement des données...</p>
            </div>

            <Transition name="success">
              <div v-if="showSuccess" class="success-overlay">
                <div class="success-content">
                  <div class="success-icon">✅</div>
                  <h3>Créé avec succès !</h3>
                </div>
              </div>
            </Transition>

            <div v-if="!isLoading && !showSuccess" class="modal-body">
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

              <div class="tab-content">
                <Transition name="fade" mode="out-in">
                  <div v-if="activeTab === 'Informations'" class="info-section">
                    <div class="form-grid">
                      <div v-for="col in filteredColumns" :key="col" class="form-group" :class="{ 'dropdown-open': showDropdowns[col] }">
                        <label class="form-label">
                          {{ cleanColumnName(col) }}
                          <span v-if="col!=='commentaire'" class="required">*</span>
                        </label>
                        <div class="input-container">
                          <input 
                            v-if="!isForeignKey(col)"
                            v-model="form[col]" 
                            class="form-input"
                            :class="{ error: errors[col] }"
                            :placeholder="`${cleanColumnName(col)}`"
                            @input="errors[col] = ''"
                          />
                          
                          <div v-else class="custom-select" :class="{ error: errors[col] }">
                            <input
                              v-model="searchTerms[col]"
                              class="form-input select-input"
                              :placeholder="props.tableName === 'prix_robot' && col === 'reference' ? 'Rechercher par référence...' : 
                                           props.tableName === 'prix_robot' && col === 'robot' ? 'Rechercher par nom de robot...' :
                                           `Rechercher ${cleanColumnName(col)}...`"
                              @click="toggleDropdown(col)"

                              @blur="hideDropdown(col,200) "
                              
                            />
                            
                            <Transition name="dropdown">
                              <div 
                                v-if="showDropdowns[col]" 
                                class="select-dropdown"
                                @click.stop
                              >
                                <div 
                                  v-for="option in getFilteredOptions(col)" 
                                  :key="option.id"
                                  class="select-option"
                                  @click="selectOption(col, option)"
                                >
                                  {{ getOptionLabel(option, col) }}
                                </div>
                                <div v-if="getFilteredOptions(col).length === 0" class="select-option disabled">
                                  Aucun résultat trouvé
                                </div>
                              </div>
                            </Transition>
                          </div>
                          
                          <Transition name="error">
                            <span v-if="errors[col]" class="error-message">
                              {{ errors[col] }}
                            </span>
                          </Transition>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-else-if="activeTab === 'Relations' || activeTab === 'Incompatibilités'" class="relations-section">
                    <div v-if="tableName === 'produits'" class="relations-content">
  
                      <div class="relation-group">
                        <div class="relation-header">
                          <h3 class="relation-title">
                            <span class="relation-icon">⚠️</span>
                            Produits incompatibles
                          </h3>
                          <button @click="toggleAllIncompatibilites" class="toggle-all-btn">
                            {{ incompatibilitesProduits.length === filteredProduitsList.length ? 'Désélectionner tout' : 'Sélectionner tout' }}
                          </button>
                        </div>
                        
                        <!-- Barre de recherche pour les incompatibilités -->
                        <div class="search-container">
                          <div class="search-input-wrapper">
                            <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                              <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2"/>
                              <path d="m21 21-4.35-4.35" stroke="currentColor" stroke-width="2"/>
                            </svg>
                            <input
                              v-model="searchIncompatibilites"
                              type="text"
                              class="search-input"
                              placeholder="Rechercher des produits..."
                            />
                            <button
                              v-if="searchIncompatibilites"
                              @click="searchIncompatibilites = ''"
                              class="clear-search"
                            >
                              ✕
                            </button>
                          </div>
                        </div>
                        
                        <div class="checkbox-grid">
                          <label v-for="p in filteredProduitsList" :key="p.id" class="checkbox-item">
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
                        
                        <div v-if="filteredProduitsList.length === 0" class="no-results">
                          Aucun produit trouvé pour "{{ searchIncompatibilites }}"
                        </div>
                      </div>

                      <div class="relation-group">
                        <div class="relation-header">
                          <h3 class="relation-title">
                            <span class="relation-icon">🤖</span>
                            Robots compatibles
                          </h3>
                          <button @click="toggleAllCompatibilitesRobots" class="toggle-all-btn">
                            {{ compatibilitesRobots.length === filteredRobotsList.length ? 'Désélectionner tout' : 'Sélectionner tout' }}
                          </button>
                        </div>
                        
                        <!-- Barre de recherche pour les robots compatibles -->
                        <div class="search-container">
                          <div class="search-input-wrapper">
                            <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                              <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2"/>
                              <path d="m21 21-4.35-4.35" stroke="currentColor" stroke-width="2"/>
                            </svg>
                            <input
                              v-model="searchCompatibilitesRobots"
                              type="text"
                              class="search-input"
                              placeholder="Rechercher des robots..."
                            />
                            <button
                              v-if="searchCompatibilitesRobots"
                              @click="searchCompatibilitesRobots = ''"
                              class="clear-search"
                            >
                              ✕
                            </button>
                          </div>
                        </div>
                        
                        <div class="checkbox-grid">
                          <label v-for="r in filteredRobotsList" :key="r.id" class="checkbox-item">
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
                        
                        <div v-if="filteredRobotsList.length === 0" class="no-results">
                          Aucun robot trouvé pour "{{ searchCompatibilitesRobots }}"
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
                            {{ compatibilitesProduits.length === filteredProduitsForRobots.length ? 'Désélectionner tout' : 'Sélectionner tout' }}
                          </button>
                        </div>
                        
                        <!-- Barre de recherche pour les produits compatibles -->
                        <div class="search-container">
                          <div class="search-input-wrapper">
                            <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                              <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2"/>
                              <path d="m21 21-4.35-4.35" stroke="currentColor" stroke-width="2"/>
                            </svg>
                            <input
                              v-model="searchCompatibilitesProduits"
                              type="text"
                              class="search-input"
                              placeholder="Rechercher des produits..."
                            />
                            <button
                              v-if="searchCompatibilitesProduits"
                              @click="searchCompatibilitesProduits = ''"
                              class="clear-search"
                            >
                              ✕
                            </button>
                          </div>
                        </div>
                        
                        <div class="checkbox-grid">
                          <label v-for="p in filteredProduitsForRobots" :key="p.id" class="checkbox-item">
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
                        
                        <div v-if="filteredProduitsForRobots.length === 0" class="no-results">
                          Aucun produit trouvé pour "{{ searchCompatibilitesProduits }}"
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-else-if="activeTab === 'Tarification' || activeTab === 'Prix'" class="pricing-section">
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

/* Header - HAUTEUR FIXE */
.modal-header {
  background: linear-gradient(135deg, #5a94e4 0%, #430c7a 90%);
  color: white;
  padding: 24px 32px 16px;
  position: relative;
  overflow: hidden;
  min-height: 140px; 
  flex-shrink: 0; 
}

.modal-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
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

.success-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.9);
  padding: 20%;
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
  flex-shrink: 0;
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
  width: 80%;
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
}

.form-input.error {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

/* Custom Select */
.custom-select {
  position: relative;
  width: 90%;
}

.custom-select.error {
  .select-input {
    border-color: #ef4444;
    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
  }
}

.select-input {
  padding-right: 45px !important;
  cursor: pointer;
}

.form-group.dropdown-open {
  z-index: 2000; 
  position: relative; 
}

.select-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: rgb(255, 255, 255);
  border: 2px solid #e2e8f0;
  border-top: none;
  border-radius: 0 0 12px 12px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 99999; /* Z-INDEX TRÈS ÉLEVÉ */
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
}



.select-option {
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid #f1f5f9;
}

.select-option:hover:not(.disabled) {
  background: #f8fafc;
  color: #667eea;
}

.select-option.disabled {
  color: #94a3b8;
  cursor: not-allowed;
  font-style: italic;
}

.select-option:last-child {
  border-bottom: none;
}

.error-message {
  color: #ef4444;
  font-size: 12px;
  margin-top: 6px;
  display: block;
}

/* Search Container - NOUVEAU */
.search-container {
  margin-bottom: 20px;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  background: #fff;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 16px;
  transition: all 0.3s ease;
}

.search-input-wrapper:focus-within {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.search-icon {
  color: #64748b;
  margin-right: 12px;
  flex-shrink: 0;
}

.search-input {
  border: none;
  outline: none;
  background: transparent;
  font-size: 16px;
  flex: 1;
  color: #334155;
}

.search-input::placeholder {
  color: #94a3b8;
}

.clear-search {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s ease;
  margin-left: 8px;
  flex-shrink: 0;
}

.clear-search:hover {
  background: #f1f5f9;
  color: #64748b;
}

/* No Results Message - NOUVEAU */
.no-results {
  text-align: center;
  padding: 40px 20px;
  color: #64748b;
  font-style: italic;
  background: #f8fafc;
  border-radius: 12px;
  border: 2px dashed #e2e8f0;
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
  flex-shrink: 0;
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

.dropdown-enter-active, .dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from, .dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Custom scrollbar */
.tab-content::-webkit-scrollbar,
.select-dropdown::-webkit-scrollbar {
  width: 8px;
}

.tab-content::-webkit-scrollbar-track,
.select-dropdown::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.tab-content::-webkit-scrollbar-thumb,
.select-dropdown::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
}

.tab-content::-webkit-scrollbar-thumb:hover,
.select-dropdown::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6b4190 100%);
}

/* Animations pour enhanced UX */
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
  position: relative;
  animation: slideInLeft 0.4s ease forwards;
  animation-delay: calc(var(--index, 0) * 0.1s);
  opacity: 0;
}

@keyframes slideInLeft {
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>