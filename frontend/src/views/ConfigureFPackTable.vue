<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import axios from 'axios'
import AddGroupModal from '../components/Modal/AddGroupModal.vue'
import { useRouter } from 'vue-router'
import { useIncompatibilitesChecker } from '../composables/useIncompatibilitesChecker'
import { showToast } from '../composables/useToast'
import { useLoading } from '../composables/useLoading'
import AddProduitModal from '../components/Modal/AddProduitModal.vue'
import AddEquipementModal from '../components/Modal/AddEquipementModal.vue';

const { startLoading, stopLoading } = useLoading()

const { 
    loadIncompatibilites,
    isProduitIncompatible,
    isEquipementIncompatible,
    getFullyConflictingGroups,
    getConflictingColumns
} = useIncompatibilitesChecker(() => columns.value)


const router = useRouter()
const conflictingColumnIndexes = computed(() => getConflictingColumns())
const showAddProduitModal = ref(false)
const showAddEquipementModal = ref(false);

const props = defineProps<{
  fpackId: number
  fpackName: string
}>()

type GroupItem = {
  type: 'produit' | 'equipement' | 'robot'
  ref_id: number
  label: string
  description?: string
  generation?: string
  statut?: 'standard' | 'optionnel'
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

interface Equipement {
  id: number
  reference: string
  nom: string
  equipement_produit: { equipement_id: number; produit_id: number; quantite: number }[]
}

const columns = ref<ConfigColumn[]>([])
const produits = ref<any[]>([])
const fournisseurs = ref<Equipement[]>([])
const equipements = ref<any[]>([])
const robots = ref<any[]>([])
const clientID = ref<number>(-1)
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
  console.log('Données reçues:', res.data)
  const enriched: ConfigColumn[] = []

  for (const col of res.data.columns) {
    if (col.type === 'produit') {
      try {
        const prodRes = await axios.get(`http://localhost:8000/produits/${col.ref_id}`)
        const p = prodRes.data
        const fournisseur = fournisseurs.value.find(f => f.id === p.fournisseur_id)
        enriched.push({
          ...col,
          display_name: p.nom,
          type_detail: p.type,
          description: p.description,
          fournisseur_nom: fournisseur?.nom ?? ''
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
          produits_count: eq.equipement_produit?.reduce((sum: number, ep: any) => sum + (ep.quantite || 0), 0) ?? 0
        })
      } catch {
        enriched.push(col)
      }
    } else if (col.type === 'group') {
      const enrichedGroupItems = (col.group_items || []).map((item: any) => {
        if (item.type === 'produit') {
          const p = produits.value.find(p => p.id === item.ref_id)
          return { ...item, description: p?.description ?? '', statut: item.statut ?? 'optionnel' }
        } else if (item.type === 'robot') {
          const r = robots.value.find(r => r.id === item.ref_id)
          return { ...item, generation: r?.generation ?? '', statut: item.statut ?? 'optionnel' }
        }
        return { ...item, statut: item.statut ?? 'optionnel' }
      })

      enriched.push({
        ...col,
        group_items: enrichedGroupItems,
        group_summary: summarizeGroupItems(enrichedGroupItems)
      })
    } else {
      enriched.push(col)
    }
  }

  columns.value = enriched

}

async function fetchProduitsEtEquipements() {
  const [prod, eq, rob, four,currFpack] = await Promise.all([
    axios.get('http://localhost:8000/produits'),
    axios.get('http://localhost:8000/equipements'),
    axios.get('http://localhost:8000/robots'),
    axios.get('http://localhost:8000/fournisseurs'),
    axios.get(`http://localhost:8000/fpacks/${props.fpackId}`)
  ])
  produits.value = prod.data
  equipements.value = eq.data
  robots.value = rob.data
  fournisseurs.value = four.data
  clientID.value = currFpack.data.client
}

function handleWheel(e: WheelEvent) {
  const target = e.target as HTMLElement
  
  const inGroupList = target.closest('.group-list') as HTMLElement | null
  if (inGroupList) {
    const canScrollVertically = inGroupList.scrollHeight > inGroupList.clientHeight
    const isScrollingVertically = Math.abs(e.deltaY) > Math.abs(e.deltaX)
    if (isScrollingVertically && canScrollVertically) {
      return
    }
  }

  const columnBox = target.closest('.column-card') as HTMLElement | null
  if (columnBox) {
    const canScrollVertically = columnBox.scrollHeight > columnBox.clientHeight
    const isScrollingVertically = Math.abs(e.deltaY) > Math.abs(e.deltaX)
    if (isScrollingVertically && canScrollVertically) {
      return
    }
  }

  if (columnsRowRef.value) {
    const canScrollVertically = columnsRowRef.value.scrollHeight > columnsRowRef.value.clientHeight
    
    if (canScrollVertically) {
      return
    }
  }}


function handleAddProduit(item: { id: number; nom: string; type: string; fournisseur: string; description?: string }) {
  if (isProduitIncompatible(item.id)) {
    showToast("Ce produit est incompatible avec un élément déjà présent.", "#ef4444")
    return
  }

  const fournisseur = fournisseurs.value.find(f => f.nom === item.fournisseur)
  const col: ConfigColumn = {
    type: 'produit',
    ref_id: item.id,
    ordre: columns.value.length,
    display_name: item.nom,
    type_detail: item.type,
    description: item.description ?? '',       
    fournisseur_nom: fournisseur?.nom ?? ''
  }

  const fullyConflictingGroupIndexes = getFullyConflictingGroups(columns.value, col)

  if (fullyConflictingGroupIndexes.length > 0) {
    const groupeNames = fullyConflictingGroupIndexes
      .map(i => columns.value[i]?.display_name)
      .filter(Boolean)
      .join(', ')
    showToast(`Ce produit rend ce(s) groupe(s) inutilisable(s) : ${groupeNames}.`, "#f97316")
    return
  }
  
  columns.value.push(col)
}

function handleAddEquipement(item: Equipement) {

    const col: ConfigColumn = {
    type: 'equipement',
    ref_id: item.id,
    ordre: columns.value.length,
    display_name: item.nom,
    produits_count: item.equipement_produit.reduce((sum, ep) => sum + (ep.quantite || 0), 0)
  };
  
  if (isEquipementIncompatible(item.id)) {
    showToast("Cet equipement est incompatible avec un élément déjà présent.", "#ef4444")
    return
  }
  const fullyConflictingGroupIndexes = getFullyConflictingGroups(columns.value,col)

  if (fullyConflictingGroupIndexes.length > 0) {
    const groupeNames = fullyConflictingGroupIndexes
      .map(i => columns.value[i]?.display_name)
      .filter(Boolean)
      .join(', ')
    showToast(`Cet equipement rend ce(s) groupe(s) inutilisable(s) : ${groupeNames}.`, "#f97316")
    return
  }

  columns.value.push(col);
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

async function handleGroupUpdate(group: { type: 'group'; ref_id: null; display_name: string; group_items: (GroupItem & { statut?: 'standard' | 'optionnel' })[]; }) {
  const enrichedGroupItems = group.group_items.map(item => {
    if (item.type === 'produit') {
      const produit = produits.value.find(p => p.id === item.ref_id)
      return {
        ...item,
        description: produit?.description ?? '',
        statut: item.statut ?? 'optionnel',
      }
    } else if (item.type === 'robot') {
      const robot = robots.value.find(r => r.id === item.ref_id)
      return {
        ...item,
        generation: robot?.generation ?? '',
        statut: item.statut ?? 'optionnel',
      }
    }
    return item
  })

  const resGroup = await axios.post('http://localhost:8000/groupes', { nom: group.display_name })
  const groupe_id = resGroup.data.id

  await Promise.all(
    enrichedGroupItems.map(item =>
      axios.post('http://localhost:8000/groupe_items', {
        group_id: groupe_id,
        type: item.type,
        ref_id: item.ref_id,
        statut: item.statut ?? 'optionnel'
      })
      
    )
  )

  const configCol: ConfigColumn = {
    type: 'group',
    ref_id: groupe_id,
    display_name: group.display_name,
    ordre: editingGroupIndex.value ?? columns.value.length,
    group_items: enrichedGroupItems,
    group_summary: summarizeGroupItems(enrichedGroupItems)
  }


  const fullyConflictingGroupIndexes = getFullyConflictingGroups(columns.value,configCol)

  if (fullyConflictingGroupIndexes.length > 0) {
    const groupeNames = fullyConflictingGroupIndexes
      .map(i => columns.value[i]?.display_name)
      .filter(Boolean)
      .join(', ')
    showToast(`Ce groupe rend ce(s) groupe(s) inutilisable(s) : ${groupeNames}.`, "#f97316")
    return
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
    showToast("Erreur : impossible de sauvegarder, ID de FPack non défini.", "#dc2626")
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
  router.push({ name: 'FPackMenu'})

}

async function listeView() {
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
  router.push({ name: 'ConfigureFPackListe', params: { id: props.fpackId }, query: { name: props.fpackName } })
}

function onCloseModal() {
  showAddProduitModal.value = false
  showAddEquipementModal.value = false;

}


onMounted(async () => {
  startLoading()
  await fetchProduitsEtEquipements()
  await fetchConfiguration()
  if (columnsRowRef.value) {
    columnsRowRef.value.addEventListener('wheel', handleWheel, { passive: false })
  }
  await loadIncompatibilites()
  stopLoading()
})

onUnmounted(() => {
  if (columnsRowRef.value) {
    columnsRowRef.value.removeEventListener('wheel', handleWheel)
  }
})
</script>

<template>
  <div class="fpack-config-wrapper">
    <h2 class="fpack-title">
      🛠️ Configuration du F-Pack :
      <span class="fpack-name">{{ props.fpackName }}</span>
    </h2>
    <button class="vue-liste-btn" @click="listeView()">
      🧾 Vue Liste
    </button>

    <div class="toolbar">
      <button @click="showAddProduitModal = true" class="addProduit">🧩 Ajouter Produit</button>
      <AddProduitModal v-if="showAddProduitModal" :produits="produits" :fournisseurs="fournisseurs" @add="handleAddProduit" @close="onCloseModal"/>

      <button @click="showAddEquipementModal = true" class="addEquipement">🔧 Ajouter Équipement</button>
      <AddEquipementModal v-if="showAddEquipementModal" :equipements="equipements" @add="handleAddEquipement" @close="onCloseModal"/>


      <button @click="showAddGroupModal = true" class="addGroupe">👥 Ajouter Groupe</button>
    </div>

    <div ref="columnsRowRef" class="columns-scroll-container">
      <div v-for="(col, index) in columns" :key="index" class="column-card" :class="{ conflict: conflictingColumnIndexes.includes(index) }">
        <div class="card-header">
          <span class="badge" :class="col.type">
            <template v-if="col.type === 'produit'">🧩 Produit</template>
            <template v-else-if="col.type === 'equipement'">🔧 Équipement</template>
            <template v-else>👥 Groupe</template>
          </span>
          <strong class="title">{{ col.display_name }}</strong>
        </div>

        <div class="card-content">
          <div class="info-line" v-if="col.type === 'produit'">
            <p v-if="col.type_detail"><strong>Type :</strong> {{ col.type_detail }}</p>
            <p v-if="col.fournisseur_nom"><strong>Fournisseur :</strong> {{ col.fournisseur_nom }}</p>
            <p v-if="col.description"><strong>Description :</strong> {{ col.description }}</p>
          </div>

          <div class="info-line" v-else-if="col.type === 'equipement'">
            <p><strong>Produit(s) associé(s) :</strong> {{ col.produits_count }}</p>
          </div>

          <div class="info-line" v-else-if="col.type === 'group' && col.group_summary">
            <p>
              <strong>Contenu :</strong>
              {{ col.group_summary.produit }}🧩 /
              {{ col.group_summary.equipement }}🔧 /
              {{ col.group_summary.robot }}🤖
            </p>
          </div>

          <ul v-if="col.type === 'group'" class="group-list">
            <li v-for="item in col.group_items" :key="item.ref_id + '-' + item.statut">
              <span v-if="(item.statut ?? 'optionnel') === 'standard'" class="badge-standard">⭐</span>
              {{ item.label }}
              <template v-if="item.type === 'produit' && item.description">
                - {{ item.description.length > 10 ? item.description.slice(0, 10) + '…' : item.description }}
              </template>
              <template v-else-if="item.type === 'robot' && item.generation">
                {{ item.generation.length > 6 ? item.generation.slice(0, 6) + '...' : item.generation }}
              </template>
            </li>
          </ul>
        </div>

        <div class="card-actions">
          <button @click="moveLeft(index)">◀️</button>
          <button @click="startEdit(index)">✏️</button>
          <button @click="columns.splice(index, 1)">🗑️</button>
          <button @click="moveRight(index)">▶️</button>
        </div>
      </div>
    </div>



    <AddGroupModal
      v-if="showAddGroupModal"
      :initialGroup="editingGroupIndex !== null ? { display_name: columns[editingGroupIndex].display_name, group_items: columns[editingGroupIndex].group_items || [] } : undefined"
      :fpackClient="clientID"
      @close="handleGroupModalClose"
      @created="handleGroupUpdate"
    />

    <div class="footer-actions">
      <button class="save" @click="saveConfiguration">Sauvegarder</button>
      <button class="clear" @click="resetFPack">Effacer tout</button>
    </div>
  </div>
</template>


<style scoped>

.vue-liste-btn {
  color: white;
  background-color: #e3ba12;
  padding: 0.6rem 1rem;
  border-radius: 8px;
  border: none;
  margin-bottom: 1%;
  font-weight: 600;
  width: 570px;
  font-size: 0.95rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.vue-liste-btn:hover {
  background-color: #c29e10;
  box-shadow: 0 6px 16px rgba(197, 179, 18, 0.4);
}

.vue-liste-btn:focus {
  outline: 2px solid #bfdbfe;
  outline-offset: 2px;
}

.fpack-config-wrapper {
  padding: 0rem 2rem 2rem 2rem;
  background-color: #f1f5f9;
  height: 90dvh;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  overflow: hidden;
}

.fpack-title {
  font-size: 1.75rem;
  font-weight: bold;
  margin-bottom: 1rem;
}

.fpack-name {
  color: #2563eb;
  font-weight: 700;
  margin-left: 0.5rem;
}

.toolbar {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.toolbar button {
  color: white;
  padding: 0.6rem 1rem;
  border-radius: 8px;
  border: none;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.conflict {
  border: 2px solid red;
  background-color: #ffe4e6;
}

.addProduit {
  background-color: #3b82f6;
}

.addEquipement {
  background-color: #f59e0b;
}

.addGroupe {
  background-color: #10b981;
}

.addProduit:hover {
  background-color: #2563eb;
}

.addEquipement:hover {
  background-color: #df920d;
}

.addGroupe:hover {
  background-color: #0d9b6c;
}

.columns-scroll-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  padding-bottom: 1rem;
  overflow-y: auto;
  max-height: calc(100vh - 300px);
}

.columns-scroll-container::-webkit-scrollbar {
  width: 8px;
  height: auto;
}

.columns-scroll-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.column-card {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  padding: 1rem;
  width: 220px;
  height: 80%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.card-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 0.75rem;
}

.title {
  font-size: 1.1rem;
  font-weight: 700;
  text-align: center;
  margin-top: 0.3rem;
}

.badge {
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: bold;
  color: white;
}

.badge.produit {
  background-color: #3b82f6;
}

.badge.equipement {
  background-color: #f59e0b;
}

.badge.group {
  background-color: #10b981;
}

.card-content {
  font-size: 0.9rem;
  color: #374151;
  padding-bottom: 0.75rem;
  flex: 1 1 auto;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.info-line {
  margin-bottom: 0.4rem;
}

.group-list {
  list-style-type: none;
  padding-left: 0.5rem;
  margin-top: 0.5rem;
  border-left: 2px solid #d1d5db;
  max-height: 100%;
  overflow-y: auto;
  flex: 1 1 auto;
}

.group-list li {
  font-size: 0.85rem;
  color: #6b7280;
  margin-bottom: 0.3rem;
}

.group-list::-webkit-scrollbar {
  width: 8px;
}

.group-list::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 4px;
}


.card-actions {
  display: flex;
  justify-content: space-around;
  margin-top: auto;
  padding-top: 0.75rem;
  border-top: 1px solid #e5e7eb;
}

.card-actions button {
  background-color: #e5e7eb;
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  font-size: 1.2rem;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: background-color 0.2s ease;
}

.card-actions button:hover {
  background-color: #3b82f6;
  color: white;
}

.add-select-inline {
  margin-top: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.add-select-inline select {
  padding: 0.6rem 1rem;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background-color: white;
  font-size: 1rem;
  color: #374151;
}

.add-select-inline button {
  padding: 0.6rem 1rem;
  font-size: 1rem;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.add-select-inline button:first-of-type {
  background-color: #10b981;
  color: white;
}

.add-select-inline button:last-of-type {
  background-color: #ad0303;
  color: white;
}

.footer-actions {
  margin-top: 0.5rem;
  display: flex;
  gap: 1rem;
}

.footer-actions .save {
  background-color: #3b82f6;
  color: white;
}

.footer-actions .clear {
  background-color: #ef4444;
  color: white;
}

.footer-actions button {
  padding: 0.7rem 1.4rem;
  font-size: 1rem;
  font-weight: bold;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.footer-actions .save:hover {
  background-color: #2563eb;
}

.footer-actions .clear:hover {
  background-color: #dc2626;
}

.badge-standard {
  background-color: #eaeaea;
  color: white;
  font-size: 0.7rem;
  border: #cdab22 solid 1px;
  font-weight: 700;
  border-radius: 4px;
  padding: 1px 6px;
  margin-left: 8px;
  user-select: none;
}

</style>