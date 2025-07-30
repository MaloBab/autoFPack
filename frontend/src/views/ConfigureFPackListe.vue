<script setup lang="ts">
import { onMounted, ref } from 'vue'
import axios from 'axios'
import { useRoute, useRouter } from 'vue-router'
import { useLoading } from '../composables/useLoading'
import Draggable from 'vuedraggable'

const { startLoading, stopLoading } = useLoading()

const router = useRouter()
const route = useRoute()
const fpackId = Number(route.params.id)
const fpackName = String(route.query.name ?? '')

const columns = ref<any[]>([])
const produits = ref<any[]>([])
const fournisseurs = ref<any[]>([])
const expandedIndexes = ref(new Set<number>())
const allExpanded = ref(false)

function toggleAll() {
  if (allExpanded.value) {
    expandedIndexes.value.clear()
  } else {
    columns.value.forEach((_, idx) => expandedIndexes.value.add(idx))
  }
  allExpanded.value = !allExpanded.value
}

function toggleExpanded(index: number) {
  if (expandedIndexes.value.has(index)) {
    expandedIndexes.value.delete(index)
  } else {
    expandedIndexes.value.add(index)
  }
}

function formatTypeLabel(type: string) {
  if (type === 'produit') return 'Produit'
  if (type === 'equipement') return 'Équipement'
  if (type === 'group') return 'Groupe'
  return type
}

async function configView() {
    await axios.delete(`http://localhost:8000/fpack_config_columns/clear/${fpackId}`)
    for (let i = 0; i < columns.value.length; i++) {
      const col = columns.value[i]
      await axios.post(`http://localhost:8000/fpack_config_columns`, {
        fpack_id: fpackId,
        ordre: i,
        type: col.type,
        ref_id: col.ref_id
    })
  }
  router.push({ name: 'ConfigureFPack', params: { tableName: 'fpacks', id: fpackId }, query: { name: fpackName } })
}

onMounted(async () => {
  startLoading()
  const [colRes, prodRes, fournRes] = await Promise.all([
    axios.get(`http://localhost:8000/fpack_config_columns/${fpackId}`),
    axios.get(`http://localhost:8000/produits`),
    axios.get(`http://localhost:8000/fournisseurs`)
  ])
  produits.value = prodRes.data
  fournisseurs.value = fournRes.data

  const enriched = await Promise.all(colRes.data.map(async (col: any) => {
    if (col.type === 'produit') {
      const produit = produits.value.find(p => p.id === col.ref_id)
      const fournisseur = fournisseurs.value.find(f => f.id === produit?.fournisseur_id)
      return {
        ...col,
        display_name: produit?.nom || col.display_name,
        description: produit?.description || '',
        type_detail: produit?.type || '',
        fournisseur_nom: fournisseur?.nom || ''
      }
    } else if (col.type === 'equipement') {
      const eqRes = await axios.get(`http://localhost:8000/equipements/${col.ref_id}`)
      const equipement = eqRes.data
      const produitIds = equipement.equipement_produit?.map((ep: any) => ep.produit_id) || []
      const produitsInternes = produits.value.filter(p => produitIds.includes(p.id))
      return {
        ...col,
        display_name: equipement.nom,
        content: equipement.equipement_produit,
        produits_count: equipement.equipement_produit.reduce((sum: number, p: any) => sum + (p.quantite || 0), 0),
        produits: produitsInternes
      }
    } else if (col.type === 'group') {
      return {
        ...col,
        display_name: col.display_name,
        group_items: col.group_items
      }
    }
    return col
  }))
  columns.value = enriched
  stopLoading()
})
</script>

<template>
  <div class="liste-page">
    <div class="header-bar">
      <h2>🧾 Liste du F-Pack : <span class="fpack-name">{{ fpackName }}</span></h2>
      <div class="header-actions">
        <button class="btn-secondary" @click="toggleAll"> {{ allExpanded ? 'Tout replier' : 'Tout déplier' }} </button>
        <button class="btn-retour" @click="configView">
           🛠️ Vue Configuration / Sauvegarder
        </button>
        </div>
    </div>

    <div class="scroll-container">
      <ul class="liste-ul">
        <Draggable v-model="columns" item-key="ordre" handle=".drag-handle" animation="200">
          <template #item="{ element: col, index }">
            <li
              class="liste-item"
              :class="'type-' + col.type"
            >
              <div class="header-row" @click="toggleExpanded(index)">
                <div class="icon drag-handle" style="cursor: grab;">
                  <span v-if="col.type === 'produit'">📦</span>
                  <span v-else-if="col.type === 'equipement'">🔧</span>
                  <span v-else>👥</span>
                </div>

                <div class="content">
                  <div class="main-line">
                    <strong class="label">#{{ index + 1 }} - {{ col.display_name }}</strong>
                    <span class="badge" :class="'badge-' + col.type">{{ formatTypeLabel(col.type) }}</span>
                  </div>
                  <div class="sub-text">
                    Cliquez pour {{ expandedIndexes.has(index) ? 'replier' : 'déplier' }}
                  </div>
                </div>
              </div>

              <transition name="slide-fade">
                <div v-show="expandedIndexes.has(index)" class="details">
                  <template v-if="col.type === 'produit'">
                    <p><strong>Fournisseur :</strong> {{ col.fournisseur_nom || 'Inconnu' }}</p>
                    <p><strong>Description :</strong> {{ col.description || '—' }}</p>
                    <p><strong>Type :</strong> {{ col.type_detail || '—' }}</p>
                  </template>

                  <template v-else-if="col.type === 'equipement'">
                    <p><strong>Nombre de produits liés :</strong> {{ col.produits_count }}</p>
                    <ul class="sub-list" v-if="col.produits && col.produits.length">
                      <li v-for="p in col.produits" :key="p.id">
                        • {{ p.nom }} <strong>x{{ col.content.find((prod: any) => prod.produit_id === p.id)?.quantite }}</strong>
                      </li>
                    </ul>
                  </template>

                  <template v-else-if="col.type === 'group'">
                    <p><strong>Contenu du groupe :</strong></p>
                    <ul class="sub-list">
                      <li v-for="item in col.group_items" :key="item.ref_id">
                        {{ item.label }} ({{ formatTypeLabel(item.type) }})
                      </li>
                    </ul>
                  </template>
                </div>
              </transition>
            </li>
          </template>
        </Draggable>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.liste-page {
  display: flex;
  flex-direction: column;
  height: 90vh;
  padding: 1.5rem 2rem;
  box-sizing: border-box;
  background: #f8fafc;
}

.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-secondary {
  background-color: #e5e7eb;
  color: #1e293b;
  padding: 0.4rem 0.9rem;
  border-radius: 8px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: background 0.2s ease;
}

.btn-secondary:hover {
  background-color: #d1d5db;
}

.btn-retour {
  background-color: #facc15;
  color: #111827;
  padding: 0.45rem 3.5rem;
  border-radius: 8px;
  font-weight: 600;
  border: none;
  cursor: pointer;
}

.fpack-name {
  color: #2563eb;
  font-weight: 700;
  margin-left: 0.5rem;
}

.scroll-container {
  flex: 1;
  overflow-y: auto;
  background: #ffffff;
  border-radius: 12px;
  padding: 1rem;
  box-shadow: 0 0 8px rgba(0, 0, 0, 0.05);
}

.liste-ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.liste-item {
  border-left: 4px solid #94a3b8;
  border-radius: 8px;
  background: #f9fafb;
  padding: 0.5rem 0.8rem;
  transition: background 0.2s;
}

.type-produit { border-left-color: #3b82f6; }
.type-equipement { border-left-color: #f97316; }
.type-group { border-left-color: #10b981; }

.header-row {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  cursor: pointer;
}

.icon {
  font-size: 1.2rem;
  padding-top: 0.2rem;
}

.content {
  flex: 1;
}

.main-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label {
  font-weight: 600;
  font-size: 0.95rem;
  color: #1e293b;
}

.badge {
  background: #e5e7eb;
  padding: 0.25rem 0.6rem;
  font-size: 0.75rem;
  border-radius: 6px;
  font-weight: 500;
  color: #334155;
  white-space: nowrap;
}

.badge-produit {
  background: #3b82f6;
  color: white;
}
.badge-equipement {
  background: #f59e0b;
  color: white;
}
.badge-group {
  background: #10b981;
  color: white;
}

.sub-text {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.2rem;
  font-style: italic;
}

.details {
  margin-top: 0.5rem;
  padding-left: 2.4rem;
  font-size: 0.85rem;
  color: #475569;
}

.sub-list {
  margin-top: 0.3rem;
  padding-left: 1rem;
}

.slide-fade-enter-active {
  transition: all 0.3s ease;
}
.slide-fade-enter-from {
  opacity: 0;
  transform: translateY(-5px);
}

.slide-fade-leave-active {
  transition: all 0.1s ease;
}

.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
</style>
