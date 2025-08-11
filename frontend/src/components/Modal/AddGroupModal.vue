<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { showToast } from '../../composables/useToast'
import Draggable from 'vuedraggable'

const props = defineProps<{
  initialGroup?: {
    display_name: string
    group_items: {
      type: 'produit' | 'equipement' | 'robot'
      ref_id: number
      label: string
      statut?: 'standard' | 'optionnel'
    }[]
  }
  fpackClient: number
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'created', group: {
    type: 'group'
    ref_id: null
    display_name: string
    group_items: {
      type: 'produit' | 'equipement' | 'robot'
      ref_id: number
      label: string
    }[]
  }): void
}>()

type SelectedItem = {
  type: 'produit' | 'equipement' | 'robot'
  reference?: string
  ref_id: number
  label: string
  statut: 'optionnel' | 'standard'
  description?: string
  generation?: string
}

const nomGroupe = ref(props.initialGroup?.display_name ?? '')
const selectedItems = ref<SelectedItem[]>(
  props.initialGroup?.group_items
    ? props.initialGroup.group_items.map(item => ({
        ...item,
        statut: item.statut ?? 'optionnel'
      }))
    : []
)

const produits = ref<any[]>([])
const equipements = ref<any[]>([])
const robots = ref<any[]>([])
const fournisseur = ref<any[]>([])
const clients = ref<any[]>([])
const iscreating = ref(false)

// État des onglets
const activeTab = ref<'produit' | 'equipement' | 'robot' | 'selection'>('selection')

// États de recherche pour chaque onglet
const searchProduit = ref('')
const searchEquipement = ref('')
const searchRobot = ref('')

// Éléments sélectionnés temporaires pour chaque type
const tempSelectedProduits = ref<Set<number>>(new Set())
const tempSelectedEquipements = ref<Set<number>>(new Set())
const tempSelectedRobots = ref<Set<number>>(new Set())

async function loadData() {
  const [prodRes, eqRes, robRes,fRes,cliRes] = await Promise.all([
    axios.get('http://localhost:8000/produits'),
    axios.get('http://localhost:8000/equipements'),
    axios.get('http://localhost:8000/robots'),
    axios.get('http://localhost:8000/fournisseurs'),
    axios.get('http://localhost:8000/clients')
  ])

  produits.value = prodRes.data
  equipements.value = eqRes.data
  robots.value = robRes.data
  fournisseur.value = fRes.data
  clients.value = cliRes.data


  if (props.initialGroup) {
    props.initialGroup.group_items.forEach(item => {
      if (item.type === 'produit') {
        tempSelectedProduits.value.add(item.ref_id)
      } else if (item.type === 'equipement') {
        tempSelectedEquipements.value.add(item.ref_id)
      } else if (item.type === 'robot') {
        tempSelectedRobots.value.add(item.ref_id)
      }
    })
  }
}

onMounted(loadData)

// Produits filtrés par recherche
const filteredProduits = computed(() => {
  if (!searchProduit.value) return produits.value
  return produits.value.filter(p => 
    p.nom.toLowerCase().includes(searchProduit.value.toLowerCase()) ||
    (p.description && p.description.toLowerCase().includes(searchProduit.value.toLowerCase())) ||
    (p.reference && p.reference.toLowerCase().includes(searchProduit.value.toLowerCase())) ||
    (p.fournisseur_id && fournisseur.value.find(f => f.id === p.fournisseur_id)?.nom.toLowerCase().includes(searchProduit.value.toLowerCase()))
  )
})

const filteredEquipements = computed(() => {
  if (!searchEquipement.value) return equipements.value
  return equipements.value.filter(e => 
    e.nom.toLowerCase().includes(searchEquipement.value.toLowerCase()) ||
    (e.reference && e.reference.toLowerCase().includes(searchEquipement.value.toLowerCase()))
  )
})

const filteredRobots = computed(() => {
  const robotsClient = robots.value.filter(r => r.client === props.fpackClient)
  if (!searchRobot.value) return robotsClient
  return robotsClient.filter(r => 
    r.nom.toLowerCase().includes(searchRobot.value.toLowerCase()) ||
    (r.generation && r.generation.toLowerCase().includes(searchRobot.value.toLowerCase())) ||
    (r.reference && r.reference.toLowerCase().includes(searchRobot.value.toLowerCase())) ||
    (r.client && clients.value.find(c => c.id === r.client)?.nom.toLowerCase().includes(searchRobot.value.toLowerCase()))
  )
})

const selectedProduitsCount = computed(() => tempSelectedProduits.value.size)
const selectedEquipementsCount = computed(() => tempSelectedEquipements.value.size)
const selectedRobotsCount = computed(() => tempSelectedRobots.value.size)

function toggleSelection(type: 'produit' | 'equipement' | 'robot', id: number) {
  if (type === 'produit') {
    if (tempSelectedProduits.value.has(id)) {
      tempSelectedProduits.value.delete(id)
    } else {
      tempSelectedProduits.value.add(id)
    }
  } else if (type === 'equipement') {
    if (tempSelectedEquipements.value.has(id)) {
      tempSelectedEquipements.value.delete(id)
    } else {
      tempSelectedEquipements.value.add(id)
    }
  } else if (type === 'robot') {
    if (tempSelectedRobots.value.has(id)) {
      tempSelectedRobots.value.delete(id)
    } else {
      tempSelectedRobots.value.add(id)
    }
  }
}


function isSelected(type: 'produit' | 'equipement' | 'robot', id: number): boolean {
  if (type === 'produit') return tempSelectedProduits.value.has(id)
  if (type === 'equipement') return tempSelectedEquipements.value.has(id)
  if (type === 'robot') return tempSelectedRobots.value.has(id)
  return false
}

function mapFournisseur(id: number): string {
  const fournisseurItem = fournisseur.value.find(f => f.id === id)
  return fournisseurItem ? fournisseurItem.nom : 'Inconnu'
}

function mapClient(id: number): string {
  const clientItem = clients.value.find(c => c.id === id)
  return clientItem ? clientItem.nom : 'Inconnu'
}

function applySelections() {
  selectedItems.value = []
  
  // Ajouter les produits sélectionnés
  tempSelectedProduits.value.forEach(id => {
    const produit = produits.value.find(p => p.id === id)
    if (produit) {
      selectedItems.value.push({
        type: 'produit',
        ref_id: id,
        label: produit.nom,
        statut: 'optionnel',
        description: produit.description
      })
    }
  })

  tempSelectedEquipements.value.forEach(id => {
    const equipement = equipements.value.find(e => e.id === id)
    if (equipement) {
      selectedItems.value.push({
        type: 'equipement',
        ref_id: id,
        label: equipement.nom,
        statut: 'optionnel'
      })
    }
  })

  // Ajouter les robots sélectionnés
  tempSelectedRobots.value.forEach(id => {
    const robot = robots.value.find(r => r.id === id)
    if (robot) {
      selectedItems.value.push({
        type: 'robot',
        ref_id: id,
        label: robot.nom,
        statut: 'optionnel',
        generation: robot.generation
      })
    }
  })

  activeTab.value = 'selection'
}

function removeItem(index: number) {
  const item = selectedItems.value[index]
  
  if (item.type === 'produit') {
    tempSelectedProduits.value.delete(item.ref_id)
  } else if (item.type === 'equipement') {
    tempSelectedEquipements.value.delete(item.ref_id)
  } else if (item.type === 'robot') {
    tempSelectedRobots.value.delete(item.ref_id)
  }
  
  selectedItems.value.splice(index, 1)
}

function valider() {
  if (!nomGroupe.value.trim()) {
    showToast("Veuillez saisir un nom pour le groupe.")
    return
  }
  iscreating.value = true
  emit('created', {
    type: 'group',
    ref_id: null,
    display_name: nomGroupe.value,
    group_items: [...selectedItems.value]
  })
}
</script>

<template>
  <div class="modal">
    <div class="modal-content">
      <h3>{{ props.initialGroup ? 'Modifier le groupe' : 'Créer un nouveau groupe' }}</h3>

      <div class="form-section">
        <label>Nom du groupe :</label>
        <input v-model="nomGroupe" placeholder="Nom du groupe" class="group-name-input" />
      </div>

      <!-- Navigation par onglets -->
      <div class="tabs-navigation">
        <button 
          :class="['tab-button', { active: activeTab === 'selection' }, `tab-${activeTab}`]"
          @click="activeTab = 'selection'"
        >
          <span class="tab-icon">📋</span>
          Sélection
          <span v-if="selectedItems.length > 0" class="tab-badge">{{ selectedItems.length }}</span>
        </button>
        
        <button 
          :class="['tab-button', { active: activeTab === 'produit' }, `tab-${activeTab}`]"
          @click="activeTab = 'produit'"
        >
          <span class="tab-icon">🧩</span>
          Produits
          <span v-if="selectedProduitsCount > 0" class="tab-badge">{{ selectedProduitsCount }}</span>
        </button>
        
        <button 
          :class="['tab-button', { active: activeTab === 'equipement' }, `tab-${activeTab}`]"
          @click="activeTab = 'equipement'"
        >
          <span class="tab-icon">🔧</span>
          Équipements
          <span v-if="selectedEquipementsCount > 0" class="tab-badge">{{ selectedEquipementsCount }}</span>
        </button>
        
        <button 
          :class="['tab-button', { active: activeTab === 'robot' }, `tab-${activeTab}`]"
          @click="activeTab = 'robot'"
        >
          <span class="tab-icon">🤖</span>
          Robots
          <span v-if="selectedRobotsCount > 0" class="tab-badge">{{ selectedRobotsCount }}</span>
        </button>
      </div>

      <!-- Contenu des onglets -->
      <div class="tab-content">
        <!-- Onglet Sélection -->
        <div v-if="activeTab === 'selection'" class="selection-tab">
          <div class="selection-header">
            <h4>Éléments du groupe</h4>
            <p class="selection-count">{{ selectedItems.length }} élément(s) sélectionné(s)</p>
          </div>
          
          <div v-if="selectedItems.length === 0" class="empty-selection">
            <div class="empty-icon">📦</div>
            <p>Aucun élément sélectionné</p>
            <p class="empty-hint">Utilisez les onglets ci-dessus pour ajouter des produits, équipements ou robots</p>
          </div>
          
          <Draggable
            v-else
            v-model="selectedItems"
            item-key="label"
            handle=".drag-handle"
            animation="200"
            class="selected-items-list"
          >
            <template #item="{ element, index }">
              <div class="selected-item">
                <div class="drag-handle">⋮⋮</div>
                <div class="item-info">
                  <div class="item-name">{{ element.label }}</div>
                  <div class="item-details">
                    <span class="item-type" :class="`type-${element.type}`">{{ element.type }}</span>
                    <span v-if="element.description" class="item-desc">
                      {{ element.description.length > 30 ? element.description.slice(0, 20) + '…' : element.description }}
                    </span>
                    <span v-else-if="element.generation" class="item-desc">{{ element.generation }}</span>
                  </div>
                </div>
                
                <div class="item-actions">
                  <label class="statut-toggle">
                    <input
                      type="checkbox"
                      v-model="selectedItems[index].statut"
                      :true-value="'standard'"
                      :false-value="'optionnel'"
                    />
                    <span class="toggle-slider"></span>
                    <span class="toggle-label">Standard</span>
                  </label>
                  
                  <button class="remove-button" @click="removeItem(index)" title="Retirer">
                    ✕
                  </button>
                </div>
              </div>
            </template>
          </Draggable>
        </div>

        <!-- Onglet Produits -->
        <div v-if="activeTab === 'produit'" class="table-tab">
          <div class="tab-header">
            <div class="search-section">
              <input 
                v-model="searchProduit" 
                placeholder="Rechercher un produit..."
                class="search-input"
              />
            </div>
            <button v-if="selectedProduitsCount > 0" @click="applySelections" class="apply-button">
              Appliquer ({{ selectedProduitsCount }})
            </button>
          </div>
          
          <div class="table-container">
            <table class="items-table">
              <thead>
                <tr>
                  <th>Nom</th>
                  <th>Reference</th>
                  <th>Description</th>
                  <th>Fournisseur</th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="produit in filteredProduits" 
                  :key="produit.id"
                  :class="['table-row', { selected: isSelected('produit', produit.id) }]"
                  @click="toggleSelection('produit', produit.id)"
                >
                  <td class="name-cell">
                    <div class="selection-indicator">
                      <div class="checkbox" :class="{ checked: isSelected('produit', produit.id) }">
                        ✓
                      </div>
                    </div>
                    {{ produit.nom }}
                  </td>
                  <td class="reference-cell"> {{ produit.reference || '—' }} </td>
                  <td class="description-cell">{{ produit.description || '—' }}</td>
                  <td class="fournisseur-cell">
                    {{ mapFournisseur(produit.fournisseur_id) || 'Inconnu' }}
                  </td>
                </tr>
              </tbody>
            </table>
            
            <div v-if="filteredProduits.length === 0" class="no-results">
              <div class="no-results-icon">🔍</div>
              <p>Aucun produit trouvé</p>
            </div>
          </div>
        </div>

        <!-- Onglet Équipements -->
        <div v-if="activeTab === 'equipement'" class="table-tab">
          <div class="tab-header">
            <div class="search-section">
              <input 
                v-model="searchEquipement" 
                placeholder="Rechercher un équipement..."
                class="search-input"
              />
            </div>
            <button v-if="selectedEquipementsCount > 0" @click="applySelections" class="apply-button">
              Appliquer ({{ selectedEquipementsCount }})
            </button>
          </div>
          
          <div class="table-container">
            <table class="items-table">
              <thead>
                <tr>
                  <th>Nom</th>
                  <th>Référence</th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="equipement in filteredEquipements" 
                  :key="equipement.id"
                  :class="['table-row', { selected: isSelected('equipement', equipement.id) }]"
                  @click="toggleSelection('equipement', equipement.id)"
                >
                  <td class="name-cell">
                    <div class="selection-indicator">
                      <div class="checkbox" :class="{ checked: isSelected('equipement', equipement.id) }">
                        ✓
                      </div>
                    </div>
                    {{ equipement.nom }}
                  </td>
                  <td class="reference-cell">{{ equipement.reference || '—' }}</td>
                </tr>
              </tbody>
            </table>
            
            <div v-if="filteredEquipements.length === 0" class="no-results">
              <div class="no-results-icon">🔍</div>
              <p>Aucun équipement trouvé</p>
            </div>
          </div>
        </div>

        <!-- Onglet Robots -->
        <div v-if="activeTab === 'robot'" class="table-tab">
          <div class="tab-header">
            <div class="search-section">
              <input 
                v-model="searchRobot" 
                placeholder="Rechercher un robot..."
                class="search-input"
              />
            </div>
            <button v-if="selectedRobotsCount > 0" @click="applySelections" class="apply-button">
              Appliquer ({{ selectedRobotsCount }})
            </button>
          </div>
          
          <div class="table-container">
            <table class="items-table">
              <thead>
                <tr>
                  <th>Nom</th>
                  <th>Référence</th>
                  <th>Génération</th>
                  <th>Client</th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="robot in filteredRobots" 
                  :key="robot.id"
                  :class="['table-row', { selected: isSelected('robot', robot.id) }]"
                  @click="toggleSelection('robot', robot.id)"
                >
                  <td class="name-cell">
                    <div class="selection-indicator">
                      <div class="checkbox" :class="{ checked: isSelected('robot', robot.id) }">
                        ✓
                      </div>
                    </div>
                    {{ robot.nom }}
                  </td>
                  <td class="reference-cell">{{ robot.reference || '—' }}</td>
                  <td class="description-cell">{{ robot.generation || '—' }}</td>
                  <td class="client-cell">
                    {{ mapClient(robot.client) || 'Inconnu' }}
                  </td>
                </tr>
              </tbody>
            </table>
            
            <div v-if="filteredRobots.length === 0" class="no-results">
              <div class="no-results-icon">🔍</div>
              <p>Aucun robot trouvé</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="actions">
        <button @click="$emit('close')" class="cancel-button">
          Annuler
        </button>
        <button :disabled="iscreating || selectedItems.length === 0" @click="valider" class="submit-button">
          {{ props.initialGroup ? 'Modifier' : 'Créer' }} le groupe
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal {
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;
  background: rgba(30, 41, 59, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
  backdrop-filter: blur(6px);
}

.modal-content {
  background: #ffffff;
  padding: 2rem;
  border-radius: 20px;
  width: 90%;
  max-width: 900px;
  height: 90vh;
  max-height: 90vh;
  margin-bottom: 2rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

h3 {
  font-size: 2rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  text-align: center;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-section label {
  font-weight: 600;
  color: #475569;
}

.group-name-input {
  padding: 0.75rem 1rem;
  font-size: 1.1rem;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  transition: all 0.3s ease;
  outline: none;
}

.group-name-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.tabs-navigation {
  display: flex;
  gap: 0.5rem;
  border-bottom: 2px solid #f1f5f9;
  padding-bottom: 0.5rem;
}

.tab-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border: none;
  border-radius: 12px 12px 0 0;
  background: transparent;
  color: #64748b;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.tab-button:hover {
  background: #f8fafc;
  color: #334155;
}

.tab-selection.active {
  background: linear-gradient(135deg, #1e1e1e, #929292);
  color: white;
  font-weight: 600;
}

.tab-produit.active {
  background: linear-gradient(135deg, #3b82f6, #60a5fa);
  color: white;
  font-weight: 600;
}

.tab-equipement.active {
  background: linear-gradient(135deg, #f59e0b, #fbbf24); 
  color: white;
  font-weight: 600;
}

.tab-robot.active {
  background: linear-gradient(135deg, #10b981, #34d399);
  color: white;
  font-weight: 600;
}

.tab-icon {
  font-size: 1.1rem;
}

.tab-badge {
  background: rgba(255, 255, 255, 0.9);
  color: #3b82f6;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.2rem 0.5rem;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

.tab-button.active .tab-badge {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.tab-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.selection-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 1rem;
}

.selection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.selection-header h4 {
  margin: 0;
  font-size: 1.3rem;
  color: #1e293b;
}

.selection-count {
  margin: 0;
  color: #64748b;
  font-size: 0.9rem;
}

.empty-selection {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #64748b;
  gap: 1rem;
}

.empty-icon {
  font-size: 4rem;
  opacity: 0.5;
}

.empty-hint {
  font-size: 0.9rem;
  opacity: 0.8;
}

.selected-items-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.selected-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.4rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.selected-item:hover {
  background: #f1f5f9;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.drag-handle {
  color: #94a3b8;
  cursor: grab;
  font-size: 1.2rem;
  user-select: none;
}

.drag-handle:active {
  cursor: grabbing;
}

.item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.item-name {
  font-weight: 600;
  color: #1e293b;
  font-size: 1.05rem;
}

.item-details {
  display: flex;
  gap: 0.75rem;
  font-size: 0.9rem;
}

.item-type {
  color: white;
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
}

.type-produit {
  background: linear-gradient(135deg, #3b82f6, #60a5fa);
}

.type-equipement {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  
}

.type-robot {
  background: linear-gradient(135deg, #10b981, #34d399); 
}

.item-desc {
  color: #64748b;
  font-style: italic;
}

.item-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.statut-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.statut-toggle input {
  display: none;
}

.toggle-slider {
  width: 40px;
  height: 20px;
  background: #e2e8f0;
  border-radius: 10px;
  position: relative;
  transition: all 0.3s ease;
}

.toggle-slider::before {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  border-radius: 8px;
  background: white;
  top: 2px;
  left: 2px;
  transition: all 0.3s ease;
}

.statut-toggle input:checked + .toggle-slider {
  background: #3b82f6;
}

.statut-toggle input:checked + .toggle-slider::before {
  transform: translateX(20px);
}

.toggle-label {
  font-size: 0.9rem;
  color: #475569;
  font-weight: 500;
}

.remove-button {
  background: none;
  border: none;
  color: #ef4444;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.remove-button:hover {
  background: #fee2e2;
  transform: scale(1.1);
}

.table-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 1rem;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.search-section {
  flex: 1;
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
  outline: none;
}

.search-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.apply-button {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.apply-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3);
}

.table-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: white;
}

.items-table {
  width: 100%;
  border-collapse: collapse;
}

.items-table thead {
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  position: sticky;
  top: 0;
  z-index: 10;
}

.items-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #475569;
  border-bottom: 2px solid #e2e8f0;
}

.table-row {
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid #f1f5f9;
}

.table-row:hover {
  background: linear-gradient(90deg, #f0f9ff, #e0f2fe);
  transform: scale(1.01);
}

.table-row.selected {
  background: linear-gradient(90deg, #dbeafe, #bfdbfe);
  border-color: #3b82f6;
}

.table-row.selected:hover {
  background: linear-gradient(90deg, #bfdbfe, #93c5fd);
}

.items-table td {
  padding: 1rem;
  vertical-align: middle;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 600;
  color: #1e293b;
}

.selection-indicator {
  flex-shrink: 0;
}

.checkbox {
  width: 20px;
  height: 20px;
  border: 2px solid #d1d5db;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  color: transparent;
  font-size: 14px;
  font-weight: bold;
}

.checkbox.checked {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-color: #3b82f6;
  color: white;
}

.description-cell {
  color: #64748b;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-cell {
  text-align: center;
}

.status-badge {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  padding: 0.3rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: #94a3b8;
  text-align: center;
  gap: 1rem;
}

.no-results-icon {
  font-size: 3rem;
  opacity: 0.5;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #f1f5f9;
}

.cancel-button, .submit-button {
  padding: 0.75rem 2rem;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  border: none;
  transition: all 0.3s ease;
}

.cancel-button {
  background: #f8fafc;
  color: #64748b;
  border: 1px solid #e2e8f0;
}

.cancel-button:hover {
  background: #f1f5f9;
  transform: translateY(-1px);
}

.submit-button {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: white;
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Scrollbars personnalisées */
.selected-items-list::-webkit-scrollbar,
.table-container::-webkit-scrollbar,
.items-table::-webkit-scrollbar {
  width: 8px;
}

.selected-items-list::-webkit-scrollbar-track,
.table-container::-webkit-scrollbar-track,
.items-table::-webkit-scrollbar-track {
  background: #f8fafc;
  border-radius: 4px;
}

.selected-items-list::-webkit-scrollbar-thumb,
.table-container::-webkit-scrollbar-thumb,
.items-table::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.selected-items-list::-webkit-scrollbar-thumb:hover,
.table-container::-webkit-scrollbar-thumb:hover,
.items-table::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

</style>