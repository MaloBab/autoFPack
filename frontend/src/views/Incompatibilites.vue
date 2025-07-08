<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const newProduit1 = ref<number | null>(null)
const newProduit2 = ref<number | null>(null)
const selectedRobot = ref<number | null>(null)
const selectedProduit = ref<number | null>(null)

type Produit = {
  id: number
  nom: string
  description: string
  fournisseur_id : number
  type : string
}

type Robot = {
  id: number
  nom: string
  generation: string
  client : number
  payload : number
  range : number
}

type ProduitIncompatibilite = {
  produit_id_1: number
  produit_id_2: number
}

type RobotProduitIncompatibilite = {
  robot_id: number
  produit_id: number
}


const produits = ref<Produit[]>([])
const robots = ref<Robot[]>([])
const produitIncompatibilites = ref<ProduitIncompatibilite[]>([])
const robotProduitIncompatibilites = ref<RobotProduitIncompatibilite[]>([])


async function loadData() {
  const [prod, rob, prodInc, robProdInc] = await Promise.all([
    axios.get('http://localhost:8000/produits'),
    axios.get('http://localhost:8000/robots'),
    axios.get('http://localhost:8000/produit-incompatibilites'),
    axios.get('http://localhost:8000/robot-produit-incompatibilites')
  ])
  produits.value = prod.data
  robots.value = rob.data
  produitIncompatibilites.value = prodInc.data
  robotProduitIncompatibilites.value = robProdInc.data
}

function addProduitIncompatibilite() {
  if (newProduit1.value && newProduit2.value && newProduit1.value !== newProduit2.value) {
    const [id1, id2] = [newProduit1.value, newProduit2.value].sort((a, b) => a - b)
    axios.post('http://localhost:8000/produit-incompatibilites', {
      produit_id_1: id1,
      produit_id_2: id2
    }).then(() => loadData())
  }
}

function addRobotProduitIncompatibilite() {
  if (selectedRobot.value && selectedProduit.value) {
    axios.post('http://localhost:8000/robot-produit-incompatibilites', {
      robot_id: selectedRobot.value,
      produit_id: selectedProduit.value
    }).then(() => loadData())
  }
}

onMounted(loadData)
</script>

<template>
  <div class="page">
    <h2>Incompatibilités</h2>

    <section>
      <h3>Produit ↔ Produit</h3>
      <div class="form-inline">
        <select v-model="newProduit1">
          <option disabled value="">Produit 1</option>
          <option v-for="p in produits" :key="p.id" :value="p.id">{{ p.nom }}</option>
        </select>
        <select v-model="newProduit2">
          <option disabled value="">Produit 2</option>
          <option v-for="p in produits" :key="p.id" :value="p.id">{{ p.nom }}</option>
        </select>
        <button @click="addProduitIncompatibilite">Ajouter</button>
      </div>

      <ul>
        <li v-for="inc in produitIncompatibilites" :key="`${inc.produit_id_1}-${inc.produit_id_2}`">
          {{ produits.find(p => p.id === inc.produit_id_1)?.nom }} ⛔ {{ produits.find(p => p.id === inc.produit_id_2)?.nom }}
        </li>
      </ul>
    </section>

    <section>
      <h3>Robot ↔ Produit</h3>
      <div class="form-inline">
        <select v-model="selectedRobot">
          <option disabled value="">Robot</option>
          <option v-for="r in robots" :key="r.id" :value="r.id">{{ r.nom }}</option>
        </select>
        <select v-model="selectedProduit">
          <option disabled value="">Produit</option>
          <option v-for="p in produits" :key="p.id" :value="p.id">{{ p.nom }}</option>
        </select>
        <button @click="addRobotProduitIncompatibilite">Ajouter</button>
      </div>

      <ul>
        <li v-for="inc in robotProduitIncompatibilites" :key="`${inc.robot_id}-${inc.produit_id}`">
          {{ robots.find(r => r.id === inc.robot_id)?.nom }} ⛔ {{ produits.find(p => p.id === inc.produit_id)?.nom }}
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.page {
  padding: 2rem;
}
.form-inline {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}
select, button {
  padding: 0.5rem;
}
h3 {
  margin-top: 2rem;
}
</style>
