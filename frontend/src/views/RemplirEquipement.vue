<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

const equipementId = Number(route.params.id)
const produits = ref<{ id: number, nom: string }[]>([])
const produitsAssocies = ref<Set<number>>(new Set())
const loading = ref(true)



async function fetchProduits() {
  const res = await axios.get(`http://localhost:8000/produits`)
  produits.value = res.data
}

async function fetchAssociations() {
  const res = await axios.get(`http://localhost:8000/groupeproduit/${equipementId}`)
  produitsAssocies.value = new Set(res.data.map((p: any) => p.produit_id))
}

function toggleProduit(id: number) {
  if (produitsAssocies.value.has(id)) {
    produitsAssocies.value.delete(id)
  } else {
    produitsAssocies.value.add(id)
  }
}

async function enregistrer() {
  const data = { produits: Array.from(produitsAssocies.value) }
  await axios.post(`http://localhost:8000/groupeproduit/${equipementId}`, data)
  router.back()
}

onMounted(async () => {
  loading.value = true
  await fetchProduits()
  await fetchAssociations()
  loading.value = false
})
</script>

<template>
  <div class="remplir-container">
    <h2>Lier des produits à l'équipement n°{{ equipementId }}</h2>

    <div v-if="loading">Chargement...</div>
    <div v-else>
      <ul class="produit-list">
        <li v-for="p in produits" :key="p.id">
          <label>
            <input type="checkbox" :checked="produitsAssocies.has(p.id)" @change="() => toggleProduit(p.id)" />
            {{ p.nom }}
          </label>
        </li>
      </ul>

      <div class="actions">
        <button @click="enregistrer">Enregistrer</button>
        <button @click="router.back()">Annuler</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.remplir-container {
  padding: 2rem;
}
.produit-list {
  list-style: none;
  padding: 0;
}
.produit-list li {
  margin: 0.5rem 0;
}
.actions {
  margin-top: 1.5rem;
  display: flex;
  gap: 1rem;
}
</style>
