<script setup lang="ts">
import { ref, onMounted, nextTick} from 'vue'
import axios from 'axios'

interface Produit {
  id: number
  nom: string
  description?: string
}

interface Robot {
  id: number
  nom: string
  generation: string
}

interface ProduitIncompatibilite {
  produit_id_1: number
  produit_id_2: number
}

interface RobotProduitIncompatibilite {
  robot_id: number
  produit_id: number
}

const produits = ref<Produit[]>([])
const produitsMap = ref<Record<number, Produit>>({})
const robots = ref<Robot[]>([])
const robotsMap = ref<Record<number, Robot>>({})
const incompProduits = ref<ProduitIncompatibilite[]>([])
const incompRobotProduits = ref<RobotProduitIncompatibilite[]>([])

const newProd1 = ref<number | null>(null)
const newProd2 = ref<number | null>(null)
const newRobot = ref<number | null>(null)
const newProdForRobot = ref<number | null>(null)

const animAdded = ref<number | null>(null)
const animRobotAdded = ref<number | null>(null)

function formatProduit(id: number): string {
  const p = produitsMap.value[id]
  return p ? `${p.nom} - ${p.description ?? ''}` : `(${id})`
}

function formatRobot(id: number): string {
  const r = robotsMap.value[id]
  return r ? `${r.nom}${r.generation}` : `(${id})`
}

async function fetchData() {
  const [prodRes, robRes, incompProdRes, incompRobProdRes] = await Promise.all([
    axios.get('http://localhost:8000/produits'),
    axios.get('http://localhost:8000/robots'),
    axios.get('http://localhost:8000/produit-incompatibilites'),
    axios.get('http://localhost:8000/robot-produit-incompatibilites')
    ])

  produits.value = prodRes.data.sort((a: Produit, b: Produit) => a.nom.localeCompare(b.nom))
  robots.value = robRes.data.sort((a: Robot, b: Robot) => a.nom.localeCompare(b.nom))

  produitsMap.value = Object.fromEntries(prodRes.data.map((p: Produit) => [p.id, p]))
  robotsMap.value = Object.fromEntries(robRes.data.map((r: Robot) => [r.id, r]))

  incompProduits.value = incompProdRes.data
  incompRobotProduits.value = incompRobProdRes.data
}

async function addProduitIncompatibilite() {
  if (!newProd1.value || !newProd2.value || newProd1.value === newProd2.value) return
  const exists = incompProduits.value.some(
    i =>
      (i.produit_id_1 === newProd1.value && i.produit_id_2 === newProd2.value) ||
      (i.produit_id_2 === newProd1.value && i.produit_id_1 === newProd2.value)
  )
  if (exists) return

  await axios.post('http://localhost:8000/produit-incompatibilites', {
    produit_id_1: newProd1.value,
    produit_id_2: newProd2.value
  })
  await fetchData()
  animAdded.value = incompProduits.value.length - 1
  nextTick(() => setTimeout(() => (animAdded.value = null), 2000))
  newProd1.value = null
  newProd2.value = null
}

async function addRobotProduitIncompatibilite() {
  if (!newRobot.value || !newProdForRobot.value) return
  const exists = incompRobotProduits.value.some(
    i => i.robot_id === newRobot.value && i.produit_id === newProdForRobot.value
  )
  if (exists) return

  await axios.post('http://localhost:8000/robot-produit-incompatibilites', {
    robot_id: newRobot.value,
    produit_id: newProdForRobot.value
  })
  await fetchData()
  animRobotAdded.value = incompRobotProduits.value.length - 1
  nextTick(() => setTimeout(() => (animRobotAdded.value = null), 2000))
  newRobot.value = null
  newProdForRobot.value = null
}

async function deleteProduitIncomp(inc: ProduitIncompatibilite) {
  await axios.delete('http://localhost:8000/produit-incompatibilites', { data: inc })
  incompProduits.value = incompProduits.value.filter(
    i => !(i.produit_id_1 === inc.produit_id_1 && i.produit_id_2 === inc.produit_id_2)
  )
}

async function deleteRobotProduitIncomp(inc: RobotProduitIncompatibilite) {
  await axios.delete('http://localhost:8000/robot-produit-incompatibilites', { data: inc })
  incompRobotProduits.value = incompRobotProduits.value.filter(
    i => !(i.robot_id === inc.robot_id && i.produit_id === inc.produit_id)
  )
}

onMounted(fetchData)
</script>

<template>
  <div class="page">
    <section class="incompat-section">
      <h2>Produits incompatibles</h2>
      <div class="add-form">
        <select v-model="newProd1">
          <option disabled :value="null">Produit</option>
          <option v-for="p in produits" :key="p.id" :value="p.id">
            {{ formatProduit(p.id) }}
          </option>
        </select>
        <select v-model="newProd2">
          <option disabled :value="null">Produit</option>
          <option v-for="p in produits" :key="p.id" :value="p.id">
            {{ formatProduit(p.id) }}
          </option>
        </select>
        <button class="add-btn" @click="addProduitIncompatibilite">➕</button>
      </div>
      <div class="table-wrapper" :class="{ scroll: incompProduits.length > 3 }">
        <table class="styled-table">
          <thead>
            <tr>
              <th>Produit</th>
              <th>Produit</th>
              <th></th>
            </tr>
          </thead>
          <tbody class="table-scrollable-body">
            <tr v-for="(inc, i) in incompProduits" :key="i" :class="{ highlight: animAdded === i }">
              <td>{{ formatProduit(inc.produit_id_1) }}</td>
              <td>{{ formatProduit(inc.produit_id_2) }}</td>
              <td><button class="delete-btn" @click="deleteProduitIncomp(inc)">🗑️</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="incompat-section">
      <h2>Robot - Produit incompatibles</h2>
      <div class="add-form">
        <select v-model="newRobot">
          <option disabled :value="null">Robot</option>
          <option v-for="r in robots" :key="r.id" :value="r.id">
            {{ formatRobot(r.id) }}
          </option>
        </select>
        <select v-model="newProdForRobot">
          <option disabled :value="null">Produit</option>
          <option v-for="p in produits" :key="p.id" :value="p.id">
            {{ formatProduit(p.id) }}
          </option>
        </select>
        <button class="add-btn" @click="addRobotProduitIncompatibilite">➕</button>
      </div>
      <div class="table-wrapper">
        <table class="styled-table">
          <thead>
            <tr>
              <th>Robot</th>
              <th>Produit</th>
              <th></th>
            </tr>
          </thead>
          <tbody class="table-scrollable-body">
            <tr v-for="(inc, i) in incompRobotProduits" :key="i" :class="{ highlight: animRobotAdded === i }">
              <td>{{ formatRobot(inc.robot_id) }}</td>
              <td>{{ formatProduit(inc.produit_id) }}</td>
              <td><button class="delete-btn" @click="deleteRobotProduitIncomp(inc)">🗑️</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
  <button @click="$router.back()" class="back-btn">Retour</button>
</template>


<style scoped>

.page {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
  padding: 1rem;
  background: #f7f7f7;
  box-sizing: border-box;

}

.back-btn {
  display: block;
  margin: 0rem auto; 
  background-color: #e74c3c;
  color: white;                    
  border: none;
  padding: 0.6rem 15rem;
  font-size: 1.2rem;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  box-shadow: 0 4px 8px rgba(231, 76, 60, 0.4);
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
  user-select: none;
}

.back-btn:hover {
  background-color: #c0392b; 
  box-shadow: 0 6px 12px rgba(192, 57, 43, 0.6);
}

.back-btn:active {
  background-color: #a93226;
  box-shadow: 0 2px 4px rgba(169, 50, 38, 0.8);
  transform: translateY(2px);
}

.incompat-section {
  display: flex;
  flex-direction: column;
  min-height: 50vh;
  justify-content: space-between;
  background: white;
}

.incompat-section h2 {
      text-align: center;
}

.incompat-section:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.08);
}

.incompat-section header {
  background: #2563eb;
  color: #ffffff;
  padding: 0.75rem 1rem;
  font-weight: 600;
  height: auto;
  font-size: 1rem;
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
}

.add-form {
  display: flex;
  gap: 0.75rem;
  padding: 1rem;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
}

.add-form select {
  width: 50%;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
  font-size: 0.95rem;
  color: #000000;
  margin-right: 0.5rem;
  background: #ffffff;
  transition: border-color 0.2s ease;
}
.add-form select:focus {
  outline: none;
  border-color: #2563eb;
}

.add-form button {
  background: #10b981;
  color: #ffffff;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.1s ease;
}
.add-form button:hover {
  background: #059669;
  transform: translateY(-1px);
}

.table-scrollable-body {
  max-height: 40vh;
  overflow-y: auto;
  display: block;
}
.table-scrollable-body::-webkit-scrollbar {
  width: 6px;
}
.table-scrollable-body::-webkit-scrollbar-thumb {
  background: #94a3b8;
  border-radius: 3px;
}

.table-scrollable-body tr {
  display: table;
  width: 100%;
  table-layout: fixed;
}

.table-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  background: #ffffff;
}

.styled-table {
  width: 100%;
  border-collapse: collapse;
}

.styled-table thead {
  display: table;
  width: 100%;
  table-layout: fixed;
}

.styled-table thead th {
  background: #e0e7ff;
  color: #1e3a8a;
  padding: 0.75rem 1rem;
  font-size: 0.9rem;
  text-transform: uppercase;
}

.styled-table td {
  padding: 0.65rem 1rem;
  font-size: 0.9rem;
  color: #374151;
}

.styled-table tbody tr:nth-child(odd) {
  background: #f8fafc;
}
.styled-table tbody tr:hover {
  background: #e0f2fe;
}

.delete-btn {
  background: #ef4444;
  color: #ffffff;
  padding: 0.35rem 0.75rem;
  border: none;
  border-radius: 5px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.1s ease;
}
.delete-btn:hover {
  background: #dc2626;
  transform: translateY(-1px);
}

.highlight {
  animation: highlightGlow 1s ease-out;
}
@keyframes highlightGlow {
  0% { background-color: #b90303; }
  100% { background-color: transparent; }
}
</style>