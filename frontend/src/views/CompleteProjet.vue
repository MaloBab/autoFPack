<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { showToast } from '../composables/useToast'
import { useLoading } from '../composables/useLoading'

const { startLoading, stopLoading } = useLoading()

const route = useRoute()
const router = useRouter()

const projet = ref<any>(null)
const configColumns = ref<any[]>([])
const produits = ref<any[]>([])
const robots = ref<any[]>([])
const produitsSeuls = ref<any[]>([])
const equipementsSeuls = ref<any[]>([])
const groupes = ref<any[]>([])
const selections = ref<Record<number, any>>({})
const loading = ref(true)
const saving = ref(false)
const expandedGroups = ref<Set<number>>(new Set())
const groupesRefs = ref<Record<number, HTMLElement | null>>({})

const equipementProduitsMap = ref<Record<number, number[]>>({})
const produitIncompatibilites = ref<{produit_id_1: number, produit_id_2: number}[]>([])
const robotProduitCompatibilites = ref<{robot_id: number, produit_id: number}[]>([])



const groupesRemplis = computed(() =>
  groupes.value.filter(g => selections.value[g.ref_id])
)
const groupesRestants = computed(() =>
  groupes.value.filter(g => !selections.value[g.ref_id])
)

const RobotsRef = computed<Record<number, string>>(() => {
  if (!robots.value) return {}

  return robots.value.reduce((acc, r) => {
    if (r?.id && r?.reference) {
      acc[r.id] = r.reference
    }
    return acc
  }, {} as Record<string, string>)
})

const ProduitRef = computed<Record<number, string>>(() => {
  if (!produits.value) return {}

  return produits.value.reduce((acc, r) => {
    if (r?.id && r?.reference) {
      acc[r.id] = r.reference
    }
    return acc
  }, {} as Record<string, string>)
})

function areProduitsIncompatible(id1: number, id2: number): boolean {
  return produitIncompatibilites.value.some(
    inc =>
      (inc.produit_id_1 === id1 && inc.produit_id_2 === id2) ||
      (inc.produit_id_1 === id2 && inc.produit_id_2 === id1)
  )
}

function isRobotcompatibleWithProduit(robotId: number, produitId: number): boolean {
  return robotProduitCompatibilites.value.some(
    inc => inc.robot_id === robotId && inc.produit_id === produitId
  )
}

function isItemIncompatible(groupe: any, item: any): boolean {
  const selectedItems: {type: string, ref_id: number}[] = []
  produitsSeuls.value.forEach(p => selectedItems.push({type: 'produit', ref_id: p.ref_id}))
  equipementsSeuls.value.forEach(e => selectedItems.push({type: 'equipement', ref_id: e.ref_id}))
  Object.entries(selections.value).forEach(([gid, ref_id]) => {
    if (Number(gid) !== groupe.ref_id && ref_id) {
      const groupObj = groupes.value.find(g => g.ref_id === Number(gid))
      if (groupObj) {
        const selectedItem = groupObj.group_items.find((i:any) => i.ref_id === ref_id)
        if (selectedItem) selectedItems.push({type: selectedItem.type, ref_id: selectedItem.ref_id})
      }
    }
  })
  for (const sel of selectedItems) {
    if (item.type === 'produit' && sel.type === 'produit') {
      if (areProduitsIncompatible(item.ref_id, sel.ref_id)) return true
    }
    if (item.type === 'equipement' && sel.type === 'produit') {
      const produits = equipementProduitsMap.value[item.ref_id] || []
      if (produits.some(pid => areProduitsIncompatible(pid, sel.ref_id))) return true
    }
    if (item.type === 'produit' && sel.type === 'equipement') {
      const produits = equipementProduitsMap.value[sel.ref_id] || []
      if (produits.some(pid => areProduitsIncompatible(item.ref_id, pid))) return true
    }
    if (item.type === 'robot' && sel.type === 'produit') {
      if (!isRobotcompatibleWithProduit(item.ref_id, sel.ref_id)) return true
    }
    if (item.type === 'produit' && sel.type === 'robot') {
      if (!isRobotcompatibleWithProduit(sel.ref_id, item.ref_id)) return true
    }
  }
  return false
}


function onEnter(el: Element, done: () => void) {
  const htmlEl = el as HTMLElement
  htmlEl.style.height = '0'
  htmlEl.style.overflow = 'hidden'
  void htmlEl.offsetHeight
  htmlEl.style.transition = 'height 0.3s'
  htmlEl.style.height = htmlEl.scrollHeight + 'px'
  setTimeout(() => {
    done()
  }, 300)
}
function onAfterEnter(el: Element) {
  const htmlEl = el as HTMLElement
  htmlEl.style.height = ''
  htmlEl.style.overflow = ''
  htmlEl.style.transition = ''
}
function onLeave(el: Element, done: () => void) {
  const htmlEl = el as HTMLElement
  htmlEl.style.height = htmlEl.scrollHeight + 'px'
  htmlEl.style.overflow = 'hidden'
  void htmlEl.offsetHeight
  htmlEl.style.transition = 'height 0.3s'
  htmlEl.style.height = '0'
  setTimeout(() => {
    done()
  }, 300)
}

function resetSelections() {
  Object.keys(selections.value).forEach((key:any) => {
    selections.value[key] = ''
  })
}

const allExpanded = computed(() => expandedGroups.value.size === groupes.value.length)

function toggleGroup(ref_id: number) {
  if (expandedGroups.value.has(ref_id)) {
    expandedGroups.value.delete(ref_id)
  } else {
    expandedGroups.value.add(ref_id)
    nextTick(() => {
      groupesRefs.value[ref_id]?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    })
  }
}

function expandAll() {
  expandedGroups.value = new Set(groupes.value.map(g => g.ref_id))
}
function collapseAll() {
  expandedGroups.value = new Set()
}

function goToNextUnfilled() {
  const next = groupesRestants.value[0]
  if (next) {
    expandedGroups.value.add(next.ref_id)
    nextTick(() => {
      groupesRefs.value[next.ref_id]?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    })
  }
}

async function fetchData() {
  loading.value = true
  try {

    const resProduits = await axios.get('http://localhost:8000/produits')
    produits.value = resProduits.data
    console.log("OK produit")

    const resRobots = await axios.get('http://localhost:8000/robots')
    robots.value = resRobots.data
    console.log("OK robot")

    const projetId = route.params.id
    const resProjet = await axios.get(`http://localhost:8000/sous_projets/${projetId}`)
    projet.value = resProjet.data
    console.log("OK sous_projet")
    console.log(projet.value)

    const resConfig = await axios.get(`http://localhost:8000/fpack_config_columns/${projet.value.fpack_id}`)
    configColumns.value = resConfig.data
    console.log("OK fpack config columns")


    produitsSeuls.value = configColumns.value.filter(c => c.type === 'produit' && !c.group_items)
    equipementsSeuls.value = configColumns.value.filter(c => c.type === 'equipement' && !c.group_items)
    groupes.value = configColumns.value.filter(c => c.type === 'group')

    const resSelections = await axios.get(`http://localhost:8000/sous_projets/${projetId}/selections`)
    for (const sel of resSelections.data) {
      if (sel.groupe_id && groupes.value.find(g => g.ref_id === sel.groupe_id)) {
        selections.value[sel.groupe_id] = sel.ref_id
      }
    }
    console.log("OK selections")
    if (groupesRestants.value.length) {
      expandedGroups.value.add(groupesRestants.value[0].ref_id)
    }

    const resEqProd = await axios.get('http://localhost:8000/equipementproduits')
    equipementProduitsMap.value = {}
    for (const [eqId, produitsArr] of Object.entries(resEqProd.data)) {
      const arr = produitsArr as Array<{ equipement_id: number, produit_id: number }>
      equipementProduitsMap.value[Number(eqId)] = arr.map(ep => ep.produit_id)
    }
    console.log("OK equipementProduit")


  } catch (err) {
    showToast('Erreur lors du chargement du projet ou de la configuration', '#EE1111')
  } finally {
    loading.value = false
    stopLoading()
  }
}

function handleExport() {
  // TODO : logique d’export
  showToast("Fonction Export en cours de développement", "#2563eb")
}

function handleShowBill() {
  if (!projet.value) return
  saveSelections(false)
  router.push({ name: 'FactureProjet', params: { id: projet.value.id } })
}

onMounted(async () => {
  startLoading()
  const resProdInc = await axios.get('http://localhost:8000/produit-incompatibilites')
  produitIncompatibilites.value = resProdInc.data
  const resRobotInc = await axios.get('http://localhost:8000/robot-produit-compatibilites')
  robotProduitCompatibilites.value = resRobotInc.data
  fetchData()
})

async function saveSelections(goBack = true) {
  saving.value = true
  try {
    const payload = groupes.value.map(groupe => {
      const selectedRefId = selections.value[groupe.ref_id]
      const selectedItem = groupe.group_items.find((item: any) => item.ref_id === selectedRefId)
      return {
        groupe_id: groupe.ref_id,
        ref_id: selectedRefId ?? null,
        type_item: selectedItem?.type ?? null
      }
    })
    await axios.put(`http://localhost:8000/sous_projets/${projet.value.id}/selections`, { selections: payload })
    showToast('Sélection enregistrée', "#059669")
  } catch (err) {
    showToast("Erreur lors de l'enregistrement","#EE1111")
  } finally {
    saving.value = false
  }
  if (goBack) {
    router.back()
  }
}
</script>

<template>
  <div class="complete-projet-container">
    <header class="sticky-header">
      <h1>
        Compléter le projet : <span class="projet-nom">{{ projet?.nom }}</span>
      </h1>
      <div class="progress-bar">
        <span>
          Groupes remplis : <b>{{ groupesRemplis.length }}</b> / {{ groupes.length }}
        </span>
        <div class="progress-track">
          <div class="progress-fill" :style="{width: (groupesRemplis.length/groupes.length*100)+'%'}"></div>
        </div>
      </div>
      <div class="header-actions">
        <button @click="goToNextUnfilled" :disabled="!groupesRestants.length" class="btn-next">
          Aller au prochain groupe à remplir
        </button>
        <button v-if="!allExpanded" @click="expandAll" class="btn-expand">Tout déplier</button>
        <button v-else @click="collapseAll" class="btn-collapse">Tout replier</button>
      </div>
    </header>
    <div v-if="loading" class="loading">Chargement...</div>
    <div v-else class="content-scroll">
      <section class="section">
        <h2>Produits seuls</h2>
        <ul class="chips-list">
          <li v-for="p in produitsSeuls" :key="p.ref_id" class="chip chip-produit">
            🧩 {{ p.display_name }}
          </li>
        </ul>
      </section>
      <section class="section">
        <h2>Équipements seuls</h2>
        <ul class="chips-list">
          <li v-for="e in equipementsSeuls" :key="e.ref_id" class="chip chip-equipement">
            🔧 {{ e.display_name }}
          </li>
        </ul>
      </section>
      <section class="section groupes-section">
        <h2>Groupes à compléter</h2>
        <div class="groupes-list">
          <div
            v-for="groupe in groupes"
            :key="groupe.ref_id"
            class="groupe-accordion"
            :class="{
              'rempli': selections[groupe.ref_id],
              'non-rempli': !selections[groupe.ref_id]
            }"
            ref="el => groupesRefs.value[groupe.ref_id] = el"
          >
            <div class="groupe-header" @click="toggleGroup(groupe.ref_id)">
              <span class="groupe-title">
                <span v-if="selections[groupe.ref_id]" class="checkmark">✔️</span>
                <span v-else class="warning">⏳</span>
                {{ groupe.display_name }}
              </span>
              <span class="arrow" :class="{open: expandedGroups.has(groupe.ref_id)}">▼</span>
            </div>
            <transition name="accordion" @enter="onEnter" @after-enter="onAfterEnter" @leave="onLeave">
              <div v-show="expandedGroups.has(groupe.ref_id)" class="groupe-body" ref="el => groupesRefs.value[groupe.ref_id] = el">
                <select v-model="selections[groupe.ref_id]" class="groupe-select">
                  <option disabled value="">-- Choisir un élément --</option>
                  <option
                    v-for="item in groupe.group_items"
                    :key="item.ref_id"
                    :value="item.ref_id"
                    :disabled="isItemIncompatible(groupe, item)"
                    :class="{ 'option-incompatible': isItemIncompatible(groupe, item) }">
                    <span v-if="(item.statut ?? 'optionnel') === 'standard'" class="badge-standard">⭐</span>
                    {{ item.label }}
                    <span v-if="item.type === 'produit'">— {{ ProduitRef[item.ref_id] }} 🧩</span>
                    <span v-else-if="item.type === 'equipement'">🔧</span>
                    <span v-else-if="item.type === 'robot'"> — {{ RobotsRef[item.ref_id] }} 🤖</span>
                  </option>
                </select>
              </div>
            </transition>
          </div>
        </div>
      </section>
    </div>
    <div class="actions">

      <button @click="saveSelections(true)" :disabled="saving" class="btn-save">
        💾 Enregistrer
      </button>
      <button @click="resetSelections" class="btn-reset">
        🔄 Réinitialiser
      </button>

      <button @click="handleExport" class="btn-export">
        📤 Exporter
      </button>
      <button @click="handleShowBill" class="btn-bill">
        🪙 Voir la facture
      </button>

      <button @click="router.back()" class="btn-back">
        Retour
      </button>
    </div>
  </div>

</template>

<style scoped>

.complete-projet-container {
  max-width: 900px;
  margin: 0 auto;
  margin-top: 1rem;
  margin-bottom: 1rem;
  background: #f8fafc;
  border-radius: 16px;
  padding: 0 0 2rem 0;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  font-family: 'Segoe UI', sans-serif;
  height: 82vh;           
  min-height: unset;       
  display: flex;
  flex-direction: column;        
}
.sticky-header {
  position: sticky;
  top: 0;
  background: #f8fafc;
  z-index: 10;
  padding: 0.3rem 2.5rem 0.7rem 2.5rem;
  border-radius: 16px 16px 0 0;
  box-shadow: 0 2px 12px rgba(0,0,0,0.03);
  flex-shrink: 0;
}
h1 {
  font-size: 1.7rem;
  margin-bottom: 0.7rem;
}
.projet-nom {
  color: #2563eb;
}
.progress-bar {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  margin-bottom: 0.7rem;
}
.progress-track {
  flex: 1;
  height: 10px;
  background: #e0e7ef;
  border-radius: 6px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #38bdf8, #059669);
  transition: width 0.3s;
}
.header-actions {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
}
.btn-next, .btn-expand, .btn-collapse {
  background: #f1f5f9;
  color: #2563eb;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1.2rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.option-incompatible {
  background: #fee2e2 !important;
  color: #991b1b !important;
}
.btn-next:disabled {
  background: #e0e7ef;
  color: #94a3b8;
  cursor: not-allowed;
}
.btn-expand, .btn-collapse {
  background: #e0e7ef;
  color: #334155;
}
.btn-expand:hover, .btn-collapse:hover {
  background: #cbd5e1;
}
.content-scroll {
  overflow-y: auto;
  flex: 1 1 0;
  padding: 0 2.5rem;
}
.section {
  margin-bottom: 1rem;
}
.section h2 {
  font-size: 1.2rem;
  color: #334155;
  margin-bottom: 0.7rem;
}
.chips-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0;
  margin: 0;
}
.chip {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: #e0e7ef;
  border-radius: 16px;
  padding: 0.3rem 1rem;
  font-size: 1rem;
  font-weight: 500;
}
.chip-produit { background: #dbeafe; color: #2563eb; }
.chip-equipement { background: #fef3c7; color: #b45309; }
.groupes-section {
  margin-bottom: 2.5rem;
}
.groupes-list {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
  border-radius: 12px;
  background: #f1f5f9;
  padding: 1rem;
}
.groupe-accordion {
  background: white;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  transition: box-shadow 0.2s;
  border-left: 6px solid #e0e7ef;
  margin-bottom: 1rem ;
}
.groupe-accordion.rempli {
  border-left: 6px solid #059669;
}
.groupe-accordion.non-rempli {
  border-left: 6px solid #f59e0b;
}
.groupe-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.8rem 1.2rem;
  cursor: pointer;
  font-size: 1.1rem;
  font-weight: 600;
  color: #334155;
  background: #f8fafc;
  user-select: none;
}
.groupe-title {
  display: flex;
  align-items: center;
  gap: 0.7rem;
}
.checkmark {
  color: #059669;
  font-size: 1.2rem;
}
.warning {
  color: #f59e0b;
  font-size: 1.2rem;
}
.arrow {
  transition: transform 0.2s;
  font-size: 1.2rem;
}
.arrow.open {
  transform: rotate(180deg);
}
.groupe-body {
  padding: 1rem 1.2rem 1.2rem 1.2rem;
  background: #f1f5f9;
}
.groupe-select {
  width: 100%;
  padding: 0.6rem 0.8rem;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  font-size: 1rem;
  margin-top: 0.2rem;
  background: white;
}
.actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  justify-content: flex-end;
  padding: 0 2.5rem;
}
.btn-save {
  background: #059669;
  color: white;
  font-weight: 600;
  padding: 0.7rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-save:disabled {
  background: #a7f3d0;
  cursor: not-allowed;
}

.btn-save:hover {
  background: #047752;
}

.btn-back {
  background: #e5e7eb;
  color: #1e293b;
  font-weight: 600;
  padding: 0.7rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-back:hover {
  background: #cbd5e1;
}

.btn-reset {
  background: #76a8e8;
  color: white;
  font-weight: 600;
  padding: 0.7rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-reset:hover {
  background: #3f87d4;
}

.btn-export, .btn-bill {
  background: #e0e7ff;
  color: #3730a3;
  font-weight: 600;
  padding: 0.7rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-export:hover, .btn-bill:hover {
  background: #c7d2fe;
}

.loading {
  text-align: center;
  color: #64748b;
  font-size: 1.2rem;
  margin: 2rem 0;
}

.accordion-enter-active, .accordion-leave-active {
  transition: height 0.3s;
}
.accordion-enter-from, .accordion-leave-to {
  height: 0;
  overflow: hidden;
}

</style>