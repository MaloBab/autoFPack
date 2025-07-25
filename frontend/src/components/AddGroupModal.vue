<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { showToast } from '../composables/useToast'

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

function addItem(type: 'produit' | 'equipement' | 'robot', id: number) {
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
}

function onProduitChange(event: Event) {
  const select = event.target as HTMLSelectElement
  const id = +select.value
  if (id) addItem('produit', id)
  select.value = ''
}

function onEquipementChange(event: Event) {
  const select = event.target as HTMLSelectElement
  const id = +select.value
  if (id) addItem('equipement', id)
  select.value = ''
}

function onRobotChange(event: Event) {
  const select = event.target as HTMLSelectElement
  const id = +select.value
  if (id) addItem('robot', id)
  select.value = ''
}

function removeItem(index: number) {
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

      <label>Nom du groupe :</label>
      <input v-model="nomGroupe" placeholder="Nom du groupe" />

      <div class="selectors">
      <select :value="''" @change="onProduitChange">
        <option value="">➕ Produit</option>
        <option v-for="p in produits" :key="p.id" :value="p.id">
  {{ p.nom }} - {{p.description ? p.description.length > 6 ? p.description.slice(0,6) + '...': p.description: ''}}</option>
      </select>

      <select :value="''" @change="onEquipementChange">
        <option value="">➕ Équipement</option>
        <option v-for="e in equipements" :key="e.id" :value="e.id">{{ e.nom }}</option>
      </select>

      <select :value="''" @change="onRobotChange">
        <option value="">➕ Robot</option>
        <option v-for="r in robots" :key="r.id" :value="r.id"> {{ r.nom}} - {{r.generation ? r.generation.length > 6 ? r.generation.slice(0,6) + '...': r.generation: ''}} </option>
      </select>
      </div>

<div class="preview">
  <h4>Éléments du groupe :</h4>
  <ul>
    <li v-for="(item, i) in selectedItems" :key="i">
      {{ item.label }}
      <template v-if="item.type === 'produit' && item.description">
        - {{ item.description.length > 10 ? item.description.slice(0, 10) + '…' : item.description }}
      </template>
      <template v-else-if="item.type === 'robot' && item.generation">{{ item.generation }}</template>
      ({{ item.type }})
      <div class="footer-buttons">
        <label class="statut-label">
          <input
            type="checkbox"
            v-model="selectedItems[i].statut"
            :true-value="'standard'"
            :false-value="'optionnel'"
          />
          <span class="tooltip-text">Standard</span>
        </label>

        <button class="cancel-button" @click="removeItem(i)">❌</button>
      </div>
    </li>
  </ul>
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
  padding: 2.5rem 3rem;
  border-radius: 16px;
  width: 480px;
  max-height: 90vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.15);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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

select {
  flex: 1;
  padding: 0.55rem 1.2rem 0.55rem 0.9rem;
  font-size: 1rem;
  border-radius: 10px;
  border: 1.5px solid #cbd5e1;
  background-color: #f9fafb;
  color: #334155;
  cursor: pointer;
  transition: border-color 0.3s ease, background-color 0.3s ease;
  appearance: none;
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 16px 16px;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

select:hover {
  border-color: #3b82f6;
  background-color: #e0e7ff;
}

.preview {
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  padding: 1rem 1.25rem;
  background-color: #f8fafc;
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
  max-height: 150px;
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
  padding: 0.35rem 0.5rem;
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
