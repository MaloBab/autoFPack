<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import AddGroupModal from './AddGroupModal.vue'

const props = defineProps<{
  fpackId: number
}>()

type GroupItem = {
  type: 'produit' | 'equipement' | 'robot'
  ref_id: number
  label: string
}

type ConfigColumn = {
  type: 'produit' | 'equipement' | 'group'
  ref_id: number | null
  ordre: number
  display_name: string
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

function asGroupProp(col: ConfigColumn | undefined): { display_name: string; group_items: GroupItem[] } | undefined {
  if (!col || col.type !== 'group' || !col.group_items) return undefined
  return {
    display_name: col.display_name,
    group_items: col.group_items
  }
}

async function fetchProduitsEtEquipements() {
  const [prod, eq] = await Promise.all([
    axios.get('http://localhost:8000/produits'),
    axios.get('http://localhost:8000/equipements')
  ])
  produits.value = prod.data
  equipements.value = eq.data
}

onMounted(fetchProduitsEtEquipements)

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

function handleGroupUpdate(group: {
  type: 'group'
  ref_id: null
  display_name: string
  group_items: GroupItem[]
}) {
  if (editingGroupIndex.value !== null) {
    const ordre = columns.value[editingGroupIndex.value].ordre
    columns.value[editingGroupIndex.value] = {
      ...group,
      ordre
    }
  } else {
    columns.value.push({
      ...group,
      ordre: columns.value.length
    })
  }
  handleGroupModalClose()
}

function handleGroupModalClose() {
  showAddGroupModal.value = false
  editingGroupIndex.value = null
}

async function saveConfiguration() {
  await axios.delete(`http://localhost:8000/fpack_config_columns/${props.fpackId}`)
  for (let i = 0; i < columns.value.length; i++) {
    const col = columns.value[i]
    await axios.post(`http://localhost:8000/fpack_config_columns`, {
      fpack_id: props.fpackId,
      ordre: i,
      type: col.type,
      ref_id: col.ref_id
    })
  }
  alert("Configuration sauvegardée")
}
</script>

<template>
  <div class="fpack-config-table">
    <h2>Configuration de la F-Pack</h2>

    <div class="columns-row">
      <div class="column-box" v-for="(col, index) in columns" :key="index">
        <strong>{{ col.display_name }}</strong>
        <div class="controls">
          <button @click="moveLeft(index)">◀️</button>
          <button @click="moveRight(index)">▶️</button>
          <button @click="startEdit(index)">✏️</button>
          <button @click="columns.splice(index, 1)">🗑️</button>
        </div>
        <div v-if="col.type === 'group'" class="group-details">
          <p v-for="item in col.group_items" :key="item.ref_id">- {{ item.label }}</p>
        </div>
      </div>
    </div>

    <div class="actions">
      <button @click="startAdd('produit')">➕ Produit</button>
      <button @click="startAdd('equipement')">➕ Équipement</button>
      <button @click="showAddGroupModal = true">➕ Groupe</button>
      <button @click="saveConfiguration">💾 Sauvegarder</button>
    </div>

    <div v-if="modeAjout" class="ajout-inline">
      <select v-model="selectedRefId">
        <option :value="null" disabled>Choisir un {{ modeAjout }}</option>
        <option
          v-for="item in modeAjout === 'produit' ? produits : equipements"
          :key="item.id"
          :value="item.id"
        >
          {{ item.nom }}
        </option>
      </select>
      <button @click="validerAjoutOuModif">✅</button>
      <button @click="modeAjout = null">❌</button>
    </div>

    <AddGroupModal
      v-if="showAddGroupModal"
      :initialGroup="asGroupProp(columns[editingGroupIndex ?? -1])"
      @close="handleGroupModalClose"
      @created="handleGroupUpdate"
    />
  </div>
</template>

<style scoped>
.fpack-config-table {
  margin: 2%;
  background: white;
  padding: 2rem;
  border-radius: 1rem;
  box-shadow: 0 0 10px #ccc;
}

.columns-row {
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  margin-bottom: 2rem;
}

.column-box {
  min-width: 180px;
  background: #f9fafb;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
}

.controls {
  margin-top: 0.5rem;
  display: flex;
  justify-content: space-between;
}

.group-details {
  margin-top: 0.5rem;
  font-size: 0.9rem;
  color: #555;
}

.actions {
  display: flex;
  gap: 1rem;
  justify-content: start;
  margin-bottom: 1rem;
}

.ajout-inline {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1rem;
}
</style>
