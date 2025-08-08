<script setup lang="ts">
import { ref, onMounted, computed, nextTick, onUnmounted } from 'vue'
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
const iscreating = ref(false)

// États pour les selects recherchables
const searchProduit = ref('')
const searchEquipement = ref('')
const searchRobot = ref('')

const searchProduitInput = ref<HTMLInputElement | null>(null)
const searchEquipementInput = ref<HTMLInputElement | null>(null)
const searchRobotInput = ref<HTMLInputElement | null>(null)

const isOpenProduit = ref(false)
const isOpenEquipement = ref(false)
const isOpenRobot = ref(false)

// Références pour les dropdowns
const produitDropdownRef = ref<HTMLElement>()
const equipementDropdownRef = ref<HTMLElement>()
const robotDropdownRef = ref<HTMLElement>()
const modalContentRef = ref<HTMLElement>()

async function loadData() {
  const [prodRes, eqRes, robRes] = await Promise.all([
    axios.get('http://localhost:8000/produits'),
    axios.get('http://localhost:8000/equipements'),
    axios.get('http://localhost:8000/robots')
  ])
  produits.value = prodRes.data
  equipements.value = eqRes.data
  robots.value = robRes.data
}

onMounted(loadData)

// Produits filtrés par recherche
const filteredProduits = computed(() => {
  if (!searchProduit.value) return produits.value
  return produits.value.filter(p => 
    p.nom.toLowerCase().includes(searchProduit.value.toLowerCase()) ||
    (p.description && p.description.toLowerCase().includes(searchProduit.value.toLowerCase()))
  )
})

const filteredEquipements = computed(() => {
  if (!searchEquipement.value) return equipements.value
  return equipements.value.filter(e => 
    e.nom.toLowerCase().includes(searchEquipement.value.toLowerCase())
  )
})

const filteredRobots = computed(() => {
  const robotsClient = robots.value.filter(r => r.client === props.fpackClient)
  if (!searchRobot.value) return robotsClient
  return robotsClient.filter(r => 
    r.nom.toLowerCase().includes(searchRobot.value.toLowerCase()) ||
    (r.generation && r.generation.toLowerCase().includes(searchRobot.value.toLowerCase()))
  )
})

// Fonction pour ajuster la position du dropdown
async function adjustDropdownPosition(dropdownType: 'produit' | 'equipement' | 'robot') {
  await nextTick()
  
  const dropdownRef = dropdownType === 'produit' ? produitDropdownRef.value :
                     dropdownType === 'equipement' ? equipementDropdownRef.value :
                     robotDropdownRef.value
  
  if (!dropdownRef || !modalContentRef.value) return
  
  const modalRect = modalContentRef.value.getBoundingClientRect()
  
  // Réinitialiser les styles
  dropdownRef.style.left = ''
  dropdownRef.style.right = ''
  dropdownRef.style.transform = ''
  dropdownRef.style.width = ''
  
  // Calculer la position optimale
  const dropdownWidth = 250 // Largeur souhaitée du dropdown
  const selectWidth = dropdownRef.parentElement?.offsetWidth || 0
  
  // Position par défaut : aligné sur le select parent
  let leftPosition = 0
  
  // Vérifier si le dropdown dépasse à droite
  const parentRect = dropdownRef.parentElement?.getBoundingClientRect()
  if (parentRect) {
    const rightEdge = parentRect.left + dropdownWidth
    const modalRightEdge = modalRect.right - 20 // Marge de 20px
    
    if (rightEdge > modalRightEdge) {
      // Aligner à droite du select
      leftPosition = selectWidth - dropdownWidth
      // Si ça dépasse encore à gauche, ajuster
      if (parentRect.left + leftPosition < modalRect.left + 20) {
        leftPosition = -(parentRect.left - modalRect.left - 20)
      }
    }
  }
  
  dropdownRef.style.left = `${leftPosition}px`
  dropdownRef.style.width = `${dropdownWidth}px`
}

function addItem(type: 'produit' | 'equipement' | 'robot', id: number, event?: Event) {
  const source = type === 'produit' ? produits.value :
                 type === 'equipement' ? equipements.value :
                 robots.value

  const item = source.find(i => i.id === id)
  if (!item) return
  const alreadyAdded = selectedItems.value.some(e => e.type === type && e.ref_id === id)
  if (!alreadyAdded) {
    selectedItems.value.push({ 
      type, 
      ref_id: id, 
      label: item.nom,
      statut: 'optionnel',
      description: item.description,
      generation: item.generation      
    })
  }
  
  // Fermer le dropdown et vider la recherche
  if (type === 'produit') {
    isOpenProduit.value = false
    searchProduit.value = ''
    searchProduitInput.value?.blur()

  } else if (type === 'equipement') {
    isOpenEquipement.value = false
    searchEquipement.value = ''
    searchEquipementInput.value?.blur()
  } else {
    isOpenRobot.value = false
    searchRobot.value = ''
    searchRobotInput.value?.blur()
  }

  if (event && event.target instanceof HTMLElement) {
    event.target.blur()
  }

}

function removeItem(index: number) {
  selectedItems.value.splice(index, 1)
}

async function openDropdown(type: 'produit' | 'equipement' | 'robot') {
  if (type === 'produit') {
    isOpenProduit.value = true
    isOpenEquipement.value = false
    isOpenRobot.value = false
  }
  else if (type === 'equipement') { 
    isOpenEquipement.value = true
    isOpenProduit.value = false
    isOpenRobot.value = false
  }
  else {
    isOpenRobot.value = true
    isOpenProduit.value = false
    isOpenEquipement.value = false
  }
  
  await adjustDropdownPosition(type)
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

// Fermer les dropdowns quand on clique ailleurs
function handleClickOutside(event: Event) {
  const target = event.target as HTMLElement
  
  if (!target.closest('.searchable-select.produit')) {
    isOpenProduit.value = false
  }
  if (!target.closest('.searchable-select.equipement')) {
    isOpenEquipement.value = false
  }
  if (!target.closest('.searchable-select.robot')) {
    isOpenRobot.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="modal">
    <div ref="modalContentRef" class="modal-content">
      <h3>{{ props.initialGroup ? 'Modifier le groupe' : 'Créer un nouveau groupe' }}</h3>

      <label>Nom du groupe :</label>
      <input v-model="nomGroupe" placeholder="Nom du groupe" />

      <div class="selectors">
        <!-- Select Produit avec recherche -->
        <div class="searchable-select produit">
          <div class="select-header" @click="openDropdown('produit')" @blur="isOpenProduit = false">
            <span class="select-icon">🧩</span>
            <input 
              v-model="searchProduit" 
              placeholder="Produit" 
              class="search-input"
              @click.stop
              @input="openDropdown('produit')"
              @focus="openDropdown('produit')"
              @blur="isOpenProduit = false"
              ref="searchProduitInput"
            />
          </div>
          <div 
            v-if="isOpenProduit" 
            ref="produitDropdownRef"
            class="dropdown-list"
            @mousedown.prevent
          >
            <div 
              v-for="p in filteredProduits" 
              :key="p.id" 
              class="dropdown-item"
              @click="addItem('produit', p.id)"
            >
              <div class="item-main">{{ p.nom }}</div>
              <div v-if="p.description" class="item-sub">
                {{ p.description }}
              </div>
            </div>
            <div v-if="filteredProduits.length === 0" class="no-results">
              Aucun produit trouvé
            </div>
          </div>
        </div>

        <!-- Select Équipement avec recherche -->
        <div class="searchable-select equipement">
          <div class="select-header" @click="openDropdown('equipement')" @blur="isOpenEquipement = false">
            <span class="select-icon">🔧</span>
            <input 
              v-model="searchEquipement" 
              placeholder="Equipement" 
              class="search-input"
              @click.stop
              @input="openDropdown('equipement')"
              @focus="openDropdown('equipement')"
              @blur="isOpenEquipement = false"
              ref="searchEquipementInput"
            />
          </div>
          <div 
            v-if="isOpenEquipement" 
            ref="equipementDropdownRef"
            class="dropdown-list"
            @mousedown.prevent
          >
            <div 
              v-for="e in filteredEquipements" 
              :key="e.id" 
              class="dropdown-item"
              @click="addItem('equipement', e.id)"
            >
              <div class="item-main">{{ e.nom }}</div>
            </div>
            <div v-if="filteredEquipements.length === 0" class="no-results">
              Aucun équipement trouvé
            </div>
          </div>
        </div>

        <!-- Select Robot avec recherche -->
        <div class="searchable-select robot">
          <div class="select-header" @click="openDropdown('robot')" @blur="isOpenRobot = false">
            <span class="select-icon">🤖</span>
            <input 
              v-model="searchRobot" 
              placeholder="Robot" 
              class="search-input"
              @click.stop
              @input="openDropdown('robot')"
              @focus="openDropdown('robot')"
              @blur="isOpenRobot = false"
              ref="searchRobotInput"
            />
          </div>
          <div 
            v-if="isOpenRobot" 
            ref="robotDropdownRef"
            class="dropdown-list"
            @mousedown.prevent
          >
            <div 
              v-for="r in filteredRobots" 
              :key="r.id" 
              class="dropdown-item"
              @click="addItem('robot', r.id)"
            >
              <div class="item-main">{{ r.nom }}</div>
              <div v-if="r.generation" class="item-sub">
                {{ r.generation }}
              </div>
            </div>
            <div v-if="filteredRobots.length === 0" class="no-results">
              Aucun robot trouvé
            </div>
          </div>
        </div>
      </div>

      <div class="preview">
        <h4>Éléments du groupe :</h4>
        <Draggable
          v-model="selectedItems"
          item-key="label"
          handle=".liste-item"
          animation="200"
        >
          <template #item="{ element, index }">
            <li class="liste-item">
              {{ element.label }}
              
              <template v-if="element.type === 'produit' && element.description">
                - {{ element.description.length > 10 ? element.description.slice(0, 10) + '…' : element.description }}
              </template>
              
              <template v-else-if="element.type === 'robot' && element.generation">
                {{ element.generation }}
              </template>
              
              ({{ element.type }})

              <div class="footer-buttons">
                <label class="statut-label">
                  <input
                    type="checkbox"
                    v-model="selectedItems[index].statut"
                    :true-value="'standard'"
                    :false-value="'optionnel'"
                  />
                  <span class="tooltip-text">Standard</span>
                </label>

                <button class="cancel-button" @click="removeItem(index)">❌</button>
              </div>
            </li>
          </template>
        </Draggable>
      </div>

      <div class="actions">
        <button :disabled="iscreating" @click="valider">✅ {{ props.initialGroup ? 'Modifier' : 'Créer' }}</button>
        <button @click="$emit('close')">❌ Annuler</button>
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
  padding: 0 3rem 2rem 3rem;
  border-radius: 16px;
  width: 480px;
  max-height: 90vh;
  height: 90%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.15);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  position: relative;
}

h3 {
  font-size: 1.8rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 0.5rem;
  text-align: center;
  letter-spacing: 0.03em;
}

label {
  font-weight: 600;
  color: #475569;
  margin-bottom: 0.25rem;
  user-select: none;
}

input {
  padding: 0.6rem 1rem;
  font-size: 1rem;
  border-radius: 8px;
  border: 1.5px solid #cbd5e1;
  transition: border-color 0.3s ease;
  outline-offset: 2px;
  outline-color: transparent;
}

input:focus {
  border-color: #3b82f6;
  outline-color: #bfdbfe;
  box-shadow: 0 0 8px #bfdbfeaa;
}

.selectors {
  display: flex;
  gap: 1rem;
  justify-content: space-between;
}

.searchable-select {
  flex: 1;
  position: relative;
  min-width: 0;
}

.select-header {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1.5px solid #cbd5e1;
  border-radius: 12px;
  padding: 0.35rem 0.7rem;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
  height: 38px;
}

.select-header:hover {
  background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.select-icon {
  font-size: 0.90rem;
  opacity: 0.8;
  user-select: none;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 0.85rem;
  color: #334155;
  font-weight: 500;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.search-input::placeholder {
  color: #64748b;
  font-size: 0.85rem;
  font-weight: 500;
}

.dropdown-list {
  position: absolute;
  top: 100%;
  left: 0;
  width: 250px;
  background: #ffffff;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.12);
  z-index: 1001;
  max-height: 300px;
  overflow-y: auto;
  margin-top: 6px;
  backdrop-filter: blur(10px);
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 transparent;
}

.dropdown-list::-webkit-scrollbar {
  width: 6px;
}

.dropdown-list::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 3px;
}

.dropdown-list::-webkit-scrollbar-track {
  background: transparent;
}

.dropdown-item {
  padding: 1rem 1.4rem;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid #f1f5f9;
}

.dropdown-item:hover {
  background: linear-gradient(90deg, #e0e7ff 0%, #f0f4ff 100%);
}

.dropdown-item:last-child {
  border-bottom: none;
}

.item-main {
  font-weight: 600;
  color: #1e293b;
  font-size: 1.05rem;
  margin-bottom: 4px;
  line-height: 1.4;
  word-wrap: break-word;
}

.item-sub {
  font-size: 0.9rem;
  color: #64748b;
  font-style: italic;
  line-height: 1.3;
  word-wrap: break-word;
  max-width: 100%;
}

.no-results {
  padding: 1.2rem;
  text-align: center;
  color: #64748b;
  font-style: italic;
  font-size: 0.95rem;
}

.preview {
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  padding: 1rem 1.25rem;
  background-color: #f8fafc;
  height: 70%;
  max-height: 70%;
  overflow-y: auto;
}

.preview h4 {
  margin-bottom: 0.75rem;
  font-weight: 600;
  color: #334155;
  border-bottom: 2px solid #3b82f6;
  padding-bottom: 0.3rem;
}

.preview ul {
  list-style: none;
  padding-left: 0;
  max-height: 310px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: #94a3b8 #f1f5f9;
}

.preview ul::-webkit-scrollbar {
  width: 7px;
}

.preview ul::-webkit-scrollbar-thumb {
  background-color: #94a3b8;
  border-radius: 10px;
}

.preview li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.1rem 0.5rem;
  border-radius: 8px;
  transition: background-color 0.15s ease;
  cursor: default;
}

.preview li:hover {
  background-color: #e0e7ff;
}

.preview li button {
  background: transparent;
  border: none;
  font-size: 1.25rem;
  color: #ef4444;
  cursor: pointer;
  transition: color 0.2s ease;
}

.preview li button:hover {
  color: #b91c1c;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 1.2rem;
}

.actions button {
  padding: 0.65rem 1.6rem;
  border-radius: 10px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  border: none;
  box-shadow: 0 5px 15px rgb(59 130 246 / 0.4);
  transition: background-color 0.25s ease, box-shadow 0.25s ease;
  user-select: none;
}

.actions button:first-child {
  background-color: #3b82f6;
  color: white;
}

.actions button:first-child:hover {
  background-color: #2563eb;
  box-shadow: 0 8px 20px rgb(37 99 235 / 0.6);
}

.actions button:last-child {
  background-color: #f87171;
  color: white;
}

.actions button:last-child:hover {
  background-color: #dc2626;
  box-shadow: 0 8px 20px rgb(220 38 38 / 0.6);
}

.footer-buttons {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-top: 12px;
}

.statut-label {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.statut-label input[type="checkbox"] {
  width: 14px;
  height: 14px;
  appearance: none;
  border: 2px solid #555;
  border-radius: 4px;
  background-color: white;
  display: grid;
  place-content: center;
  transition: all 0.2s ease;
  margin-top: 5px;
}

.statut-label input[type="checkbox"]::before {
  content: "✔";
  font-size: 12px;
  color: white;
  transform: scale(0);
  transition: transform 0.2s ease;
}

.statut-label input[type="checkbox"]:checked {
  background-color: #0e76fd;
  border-color: #0e76fd;
}

.statut-label input[type="checkbox"]:checked::before {
  transform: scale(1);
}

.tooltip-text {
  visibility: hidden;
  opacity: 0;
  background-color: #1f2937;
  color: white;
  border-radius: 6px;
  padding: 5px 8px;
  position: absolute;
  left: 120%;
  top: 50%;
  transform: translateY(-50%);
  white-space: nowrap;
  font-size: 12px;
  transition: opacity 0.2s ease;
  pointer-events: none;
  z-index: 2;
}

.statut-label:hover .tooltip-text {
  visibility: visible;
  opacity: 1;
}

.cancel-button:hover {
  background-color: #f3f4f6;
}
</style>