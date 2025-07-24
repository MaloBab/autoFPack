<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import TextSearch from '../components/TextSearch.vue'
import SelectableTable from '../components/SelectableTable.vue'
import SelectionFilter from '../components/SelectionFilterMode.vue'

const filterMode = ref<'all' | 'selected' | 'unselected'>('all')
const route = useRoute()
const router = useRouter()
const searchTerm = ref('')
const quantites = ref<Record<number, number>>({})

const equipementId = Number(route.params.id)
const nomEquipement = ref('')
const produitsAssocies = ref<Set<number>>(new Set())
const loading = ref(true)

async function fetchNomEquipement() {
  const res = await axios.get(`http://localhost:8000/equipements/${equipementId}`)
  nomEquipement.value = res.data.nom 
}

async function fetchAssociations() {
  const res = await axios.get(`http://localhost:8000/equipementproduit/${equipementId}`)
  const data = res.data
  produitsAssocies.value = new Set(data.map((p: any) => p.produit_id))
  quantites.value = Object.fromEntries(data.map((p: any) => [p.produit_id, p.quantite || 1]))
}

async function enregistrer() {

  await axios.delete(`http://localhost:8000/equipementproduit/clear/${equipementId}`);

  for (const produitId of produitsAssocies.value) {
      const quantite = quantites.value[produitId] || 1;
      console.log(`🚀 POSTing { equip=${equipementId}, prod=${produitId}, qte=${quantite} }`);
      await axios.post(`http://localhost:8000/equipementproduit`, {
        equipement_id: equipementId,
        produit_id: produitId,
        quantite: quantite
      });


  }

  router.back();
}

function handleSelectionChanged(newSelected: Set<number>, newQuantities: Record<number, number>) {
  produitsAssocies.value = new Set(newSelected)
  quantites.value = { ...newQuantities }
}

onMounted(async () => {
  loading.value = true
  await fetchNomEquipement()
  await fetchAssociations()
  loading.value = false
})
</script>

<template>
  <div class="remplir-container">
    <h2>Contenu de l'équipement <span class="title">{{ nomEquipement }}</span></h2>
    <SelectableTable
      tableName="produits"
      :equipement-id="equipementId"
      :selectedIds="produitsAssocies"
      :search="searchTerm"
      :filter-mode="filterMode"
      @selection-changed="handleSelectionChanged"/>
      
    <div class="research">
      <TextSearch v-model="searchTerm" />
      <SelectionFilter v-model="filterMode" />
    </div>
    <div class="actions">
      <button @click="enregistrer">Enregistrer</button>
      <button @click="router.back()">Retour</button>
    </div>
  </div>
</template>

<style scoped>
.remplir-container {
  padding: 2rem;
}
.actions {
  margin-top: 1.5rem;
  display: flex;
  gap: 1rem;
}

.research {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.title {
  font-size: 1.5rem;
  color: #2563eb;  
}

button {
  background-color: #2563eb;
  color: white;
  margin-left: 2%;
  font-weight: 500;
  font-size: 1rem;
  padding: 0.6rem 1.2rem;
  border-radius: 0.375rem;
  cursor: pointer;
  border: none;
}
button:hover {
  background-color: #1040e8;
}
</style>
