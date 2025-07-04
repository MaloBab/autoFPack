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

const groupeId = Number(route.params.id)
const nomGroupe = ref('')
const produitsAssocies = ref<Set<number>>(new Set())
const loading = ref(true)

async function fetchNomGroupe() {
  const res = await axios.get(`http://localhost:8000/groupes/${groupeId}`)
  nomGroupe.value = res.data.nom 
}

async function fetchAssociations() {
  const res = await axios.get(`http://localhost:8000/groupeproduit/${groupeId}`)
  produitsAssocies.value = new Set(res.data.map((p: any) => p.produit_id))
}

async function enregistrer() {
  await axios.delete(`http://localhost:8000/groupeproduit/clear/${groupeId}`)
  for (const produitId of produitsAssocies.value) {
    await axios.post(`http://localhost:8000/groupeproduit`, {
      groupe_id: groupeId,
      produit_id: produitId
    })
  }
  router.back()
}

onMounted(async () => {
  loading.value = true
  await fetchNomGroupe()
  await fetchAssociations()
  loading.value = false
})
</script>

<template>
  <div class="remplir-container">
    <h2>Contenu de l'équipement <span class="title">{{ nomGroupe }}</span></h2>
    <SelectableTable
      tableName="produits"
      :selectedIds="produitsAssocies"
      :search="searchTerm"
      @selection-changed="produitsAssocies = $event"
      :filter-mode="filterMode"
    />
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
