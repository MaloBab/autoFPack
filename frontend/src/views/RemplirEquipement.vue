<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import TextSearch from '../components/TextSearch.vue'
import SelectableTable from '../components/SelectableTable.vue'

const route = useRoute()
const router = useRouter()
const searchTerm = ref('')

const equipementId = Number(route.params.id)
const produitsAssocies = ref<Set<number>>(new Set())
const loading = ref(true)

async function fetchAssociations() {
  const res = await axios.get(`http://localhost:8000/groupeproduit/${equipementId}`)
  produitsAssocies.value = new Set(res.data.map((p: any) => p.produit_id))
}

async function enregistrer() {
  const data = { produits: Array.from(produitsAssocies.value) }
  await axios.post(`http://localhost:8000/groupeproduit/${equipementId}`, data)
  router.back()
}

onMounted(async () => {
  loading.value = true
  await fetchAssociations()
  loading.value = false
})
</script>

<template>
<div class="remplir-container">
    <h2>Lier des produits à l'équipement n°{{ equipementId }}</h2>

    <div v-if="loading">Chargement...</div>
    <div v-else>
    <SelectableTable
        tableName="produits"
        :selectedIds="produitsAssocies"
        :search="searchTerm"
        @selection-changed="produitsAssocies = $event"
    />
    <TextSearch v-model="searchTerm"/>
    <div class="actions">
        <button @click="enregistrer">Enregistrer</button>
        <button @click="router.back()">Retour</button>
    </div>
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
button {
  background-color: #2563eb;
  color: white;
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