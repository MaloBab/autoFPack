<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import AddGroupModal from './AddGroupModal.vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const props = defineProps<{
  fpackId: number
  fpackName: string
}>()

type GroupItem = {
  type: 'produit' | 'equipement' | 'robot'
  ref_id: number
  label: string
}

type ConfigColumn = {
  type: 'produit' | 'equipement' | 'group'
  ref_id: number
  ordre: number
  display_name: string
  type_detail?: string
  description?: string
  fournisseur_nom?: string
  produits_count?: number
  group_summary?: { produit: number; equipement: number; robot: number }
  group_items?: GroupItem[]
}

const columns = ref<ConfigColumn[]>([])
const produits = ref<any[]>([])
const equipements = ref<any[]>([])
const showAddGroupModal = ref(false)
const modeAjout = ref<'produit' | 'equipement' | null>(null)
const selectedRefId = ref<number | null>(null)
const editingIndex = ref<number | null>(null)
const editingGroupIndex = ref<number | null>(null)

const columnsRowRef = ref<HTMLElement | null>(null)

function summarizeGroupItems(items: GroupItem[]) {
  const summary = { produit: 0, equipement: 0, robot: 0 }
  items.forEach(item => summary[item.type]++)
  return summary
}

async function fetchConfiguration() {
  if (typeof props.fpackId !== 'number' || isNaN(props.fpackId)) return
  const res = await axios.get(`http://localhost:8000/fpack_config_columns/${props.fpackId}`)
  const enriched: ConfigColumn[] = []

  for (const col of res.data) {
    if (col.type === 'produit') {
      try {
        const prodRes = await axios.get(`http://localhost:8000/produits/${col.ref_id}`)
        const p = prodRes.data
        enriched.push({
          ...col,
          display_name: p.nom,
          type_detail: p.type,
          description: p.description,
          fournisseur_nom: p.fournisseur?.nom ?? ''
        })
      } catch {
        enriched.push(col)
      }
    } else if (col.type === 'equipement') {
      try {
        const eqRes = await axios.get(`http://localhost:8000/equipements/${col.ref_id}`)
        const eq = eqRes.data
        enriched.push({
          ...col,
          display_name: eq.nom,
          produits_count: eq.equipement_produits?.length ?? 0
        })
      } catch {
        enriched.push(col)
      }
    } else if (col.type === 'group') {
      enriched.push({
        ...col,
        group_summary: summarizeGroupItems(col.group_items || [])
      })
    } else {
      enriched.push(col)
    }
  }
  columns.value = enriched
}

async function fetchProduitsEtEquipements() {
  const [prod, eq] = await Promise.all([
    axios.get('http://localhost:8000/produits'),
    axios.get('http://localhost:8000/equipements')
  ])
  produits.value = prod.data
  equipements.value = eq.data
}

function handleWheel(e: WheelEvent) {
  const target = e.target as HTMLElement
  const columnBox = target.closest('.column-box') as HTMLElement | null
  if (columnBox) {
    const canScrollVertically = columnBox.scrollHeight > columnBox.clientHeight
    const isScrollingVertically = Math.abs(e.deltaY) > Math.abs(e.deltaX)
    if (isScrollingVertically && canScrollVertically) return
  }
  e.preventDefault()
  if (columnsRowRef.value) columnsRowRef.value.scrollLeft += e.deltaY
}

function moveLeft(index: number) {
  if (index === 0) return
  const tmp = columns.value[index]
  columns.value[index] = columns.value[index - 1]
  columns.value[index - 1] = tmp
}

function moveRight(index: number) {
  if (index === columns.value.length - 1) return
  const tmp = columns.value[index]
  columns.value[index] = columns.value[index + 1]
  columns.value[index + 1] = tmp
}

function startAdd(type: 'produit' | 'equipement') {
  modeAjout.value = type
  selectedRefId.value = null
  editingIndex.value = null
}

function startEdit(index: number) {
  const col = columns.value[index]
  if (col.type === 'produit' || col.type === 'equipement') {
    modeAjout.value = col.type
    selectedRefId.value = col.ref_id
    editingIndex.value = index
  } else if (col.type === 'group') {
    editingGroupIndex.value = index
    showAddGroupModal.value = true
  }
}

function validerAjoutOuModif() {
  const list = modeAjout.value === 'produit' ? produits.value : equipements.value
  const item = list.find(e => e.id === selectedRefId.value)
  if (!item) return

  const col: ConfigColumn = {
    type: modeAjout.value!,
    ref_id: item.id,
    display_name: item.nom,
    ordre: editingIndex.value ?? columns.value.length
  }

  if (editingIndex.value !== null) {
    columns.value[editingIndex.value] = col
  } else {
    columns.value.push(col)
  }

  modeAjout.value = null
  selectedRefId.value = null
  editingIndex.value = null
}

async function handleGroupUpdate(group: { type: 'group'; ref_id: null; display_name: string; group_items: GroupItem[] }) {
  const resGroup = await axios.post('http://localhost:8000/groupes', { nom: group.display_name })
  const groupe_id = resGroup.data.id
  await Promise.all(
    group.group_items.map(item =>
      axios.post('http://localhost:8000/groupe_items', {
        group_id: groupe_id,
        type: item.type,
        ref_id: item.ref_id
      })
    )
  )

  const configCol: ConfigColumn = {
    type: 'group',
    ref_id: groupe_id,
    display_name: group.display_name,
    ordre: editingGroupIndex.value ?? columns.value.length,
    group_items: group.group_items,
    group_summary: summarizeGroupItems(group.group_items)
  }

  if (editingGroupIndex.value !== null) {
    columns.value[editingGroupIndex.value] = configCol
  } else {
    columns.value.push(configCol)
  }

  handleGroupModalClose()
}

function handleGroupModalClose() {
  showAddGroupModal.value = false
  editingGroupIndex.value = null
}

async function resetFPack() {
  columns.value = []
}

async function saveConfiguration() {
  if (typeof props.fpackId !== 'number' || isNaN(props.fpackId)) {
    alert("Erreur : FPack ID non défini. Impossible de sauvegarder.")
    return
  }
  await axios.delete(`http://localhost:8000/fpack_config_columns/clear/${props.fpackId}`)
  for (let i = 0; i < columns.value.length; i++) {
    const col = columns.value[i]
    await axios.post(`http://localhost:8000/fpack_config_columns`, {
      fpack_id: props.fpackId,
      ordre: i,
      type: col.type,
      ref_id: col.ref_id
    })
  }
  router.back()
}

onMounted(async () => {
  await fetchProduitsEtEquipements()
  await fetchConfiguration()
  if (columnsRowRef.value) {
    columnsRowRef.value.addEventListener('wheel', handleWheel, { passive: false })
  }
})

onUnmounted(() => {
  if (columnsRowRef.value) {
    columnsRowRef.value.removeEventListener('wheel', handleWheel)
  }
})
</script>

<template>
  <div class="fpack-config-table">
    <h2>Configuration de la F-Pack <span class="fpack-nom">{{ props.fpackName }}</span></h2>

    <div class="actions">
      <button @click="startAdd('produit')">🧩 Ajouter Produit</button>
      <button @click="startAdd('equipement')">🔧 Ajouter Équipement</button>
      <button @click="showAddGroupModal = true">👥 Ajouter Groupe</button>
    </div>

    <div ref="columnsRowRef" class="columns-row">
      <div class="column-box" v-for="(col, index) in columns" :key="index">
        <strong class="title-col">
          <span v-if="col.type === 'produit'">🧩</span>
          <span v-else-if="col.type === 'equipement'">🔧</span>
          <span v-else-if="col.type === 'group'">👥</span>
          {{ col.display_name }}
        </strong>

        <div class="controls">
          <button @click="moveLeft(index)">◀️</button>
          <button @click="startEdit(index)">✏️</button>
          <button @click="columns.splice(index, 1)">🗑️</button>
          <button @click="moveRight(index)">▶️</button>
        </div>

        <div class="details" v-if="col.type === 'produit'">
          <p v-if="col.type_detail">Type: {{ col.type_detail }}</p>
          <p v-if="col.fournisseur_nom">Fournisseur: {{ col.fournisseur_nom }}</p>
          <p v-if="col.description">Description: {{ col.description }}</p>
        </div>

        <div class="details" v-else-if="col.type === 'equipement'">
          <p>{{ col.produits_count }} produits associés</p>
        </div>

        <div class="details" v-else-if="col.type === 'group' && col.group_summary">
          <p>{{ col.group_summary.produit }} produits, {{ col.group_summary.equipement }} équipements, {{ col.group_summary.robot }} robots</p>
        </div>

        <div v-if="col.type === 'group'" class="group-details">
          <p v-for="item in col.group_items" :key="item.ref_id">- {{ item.label }}</p>
        </div>
      </div>
    </div>

    <div v-if="modeAjout" class="ajout-inline">
      <select v-model="selectedRefId">
        <option :value="null" disabled>Choisir un {{ modeAjout }}</option>
        <option v-for="item in modeAjout === 'produit' ? produits : equipements" :key="item.id" :value="item.id">{{ item.nom }}</option>
      </select>
      <button @click="validerAjoutOuModif">✅</button>
      <button @click="modeAjout = null">❌</button>
    </div>

    <AddGroupModal
      v-if="showAddGroupModal"
      :initialGroup="editingGroupIndex !== null ? { display_name: columns[editingGroupIndex].display_name, group_items: columns[editingGroupIndex].group_items || [] } : undefined"
      @close="handleGroupModalClose"
      @created="handleGroupUpdate"
    />

    <div class="save-button">
      <button @click="saveConfiguration">Sauvegarder</button>
      <button @click="resetFPack">Effacer tout</button>
    </div>
  </div>
</template>

<style scoped>
.details {
  font-size: 0.85rem;
  color: #4b5563;
  margin-top: 0.3rem;
  line-height: 1.2;
}
.fpack-config-table {
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  padding: 2rem;
  background: #f7f7f7;
  color: #1f2937;
}

h2 {
  font-size: 1.75rem;
  margin-bottom: 1.5rem;
}

.title-col {
  text-align: center;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.actions button {
  background-color: #3b82f6;
  color: white;
  font-weight: 600;
  font-size: 0.95rem;
  padding: 0.65rem 1.2rem;
  border-radius: 0.5rem;
  cursor: pointer;
  border: none;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: background-color 0.2s ease;
}

.save-button {
  align-self: flex-start;
  margin-top: 1rem;
  gap: 1rem;
}
.save-button button {
  background-color: #3b82f6;
  color: white;
  margin-top: 0.4rem;
  font-weight: 600;
  font-size: 1rem;
  margin-right: 0.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  border: none;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: background-color 0.2s ease;
}

.actions button:hover {
  background-color: #2563eb;
}

.icon-plus {
  width: 1.1rem;
  height: 1.1rem;
  vertical-align: middle;
}

.fpack-nom {
  color: #3b82f6;
  font-weight: 700;
  margin-left: 0.5rem;
}

.columns-row {
  max-height: 45vh;
  overflow-x: auto;
  display: flex;
   padding-bottom: 1%;
   box-sizing: content-box;
  gap: 1rem;

}

.columns-row::-webkit-scrollbar {
  margin-top: 1rem;
  height: 8px;               
}

.columns-row::-webkit-scrollbar-thumb {
  background-color: #94a3b8;
  border-radius: 4px;
}

.columns-row::-webkit-scrollbar-track {
  background-color: #f1f5f9;
  border-radius: 4px;
}

.column-box {
  flex: 0 0 auto;
  min-width: 220px;
  max-height: 85%;
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  padding: 1rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s ease;
  overflow-y: auto;
  position: relative;
}

.column-box:hover {
  transform: translateY(-2px);
}

.column-box strong {
  display: block;
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}

.controls {
  margin-top: 0.75rem;
  display: flex;
  justify-content: center;
  gap: 0.6rem;
  background: #FFF;
  padding: 0.4rem 0.5rem;
}

.controls button {
  flex: none;
  width: 34px;
  height: 34px;
  background-color: #e5e7eb;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.1rem;
  color: #374151;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  transition: background-color 0.25s ease, color 0.25s ease, transform 0.15s ease;
  position: relative;
}

.controls button:hover {
  background-color: #3b82f6;
  color: white;
  transform: scale(1.1);
  box-shadow: 0 4px 10px rgba(59, 130, 246, 0.6);
}

.controls button:nth-child(1) {
  background-color: #e0f2fe;
  color: #0284c7;
}
.controls button:nth-child(1):hover {
  background-color: #0284c7;
  color: white;
}

.controls button:nth-child(4) {
  background-color: #e0f2fe;
  color: #0284c7;
}
.controls button:nth-child(4):hover {
  background-color: #0284c7;
  color: white;
}

.controls button:nth-child(2) {
  background-color: #fef3c7;
  color: #a16207;
}
.controls button:nth-child(2):hover {
  background-color: #a16207;
  color: white;
}

.controls button:nth-child(3) {
  background-color: #fee2e2;
  color: #b91c1c;
}
.controls button:nth-child(3):hover {
  background-color: #b91c1c;
  color: white;
}

.group-details {
  margin-top: 0.75rem;
  font-size: 0.9rem;
  color: #6b7280;
  padding-left: 0.5rem;
  border-left: 2px solid #cbd5e1;
}

.ajout-inline {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 1rem;
}

.ajout-inline select {
  padding: 0.5rem 1rem;
  font-size: 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background-color: white;
  color: #374151;
  appearance: none;
  max-width: 250px;
}

.ajout-inline button {
  background-color: #10b981;
  color: white;
  border: none;
  border-radius: 0.375rem;
  padding: 0.45rem 0.9rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.ajout-inline button:hover {
  background-color: #059669;
}

.ajout-inline button:last-child {
  background-color: #ef4444;
}

.ajout-inline button:last-child:hover {
  background-color: #dc2626;
}

.column-box::-webkit-scrollbar {
  width: 8px;
}

.column-box::-webkit-scrollbar-track {
  background: transparent;
}

.column-box::-webkit-scrollbar-thumb {
  background-color: #94a3b8; 
  border-radius: 4px;
  border: 2px solid transparent;
  background-clip: content-box;
}

.column-box::-webkit-scrollbar-thumb:hover {
  background-color: #64748b; 
}
</style>