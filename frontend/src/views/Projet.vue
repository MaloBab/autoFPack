<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

interface FPack {
  id: number;
  nom: string;
}

const fpacks = ref<FPack[]>([])
const selectedFPackId = ref<number | null>(null)
const configColumns = ref<any[]>([])
const selectedItems = ref<Record<number, { type: string, ref_id: number }>>({})
const nomProjet = ref("")
const clientId = ref<number | null>(null)

onMounted(async () => {
  const res = await axios.get('http://localhost:8000/fpacks')
  fpacks.value = res.data
})

async function loadTemplateConfig() {
  if (!selectedFPackId.value) return
  const res = await axios.get(`http://localhost:8000/fpack_config_columns/${selectedFPackId.value}`)
  configColumns.value = res.data
  selectedItems.value = {}
}

const groupes = computed(() =>
  configColumns.value.filter(col => col.type === 'group')
)

const produitsFixes = computed(() =>
  configColumns.value.filter(col => col.type === 'produit')
)

const equipementsFixes = computed(() =>
  configColumns.value.filter(col => col.type === 'equipement')
)

async function submitProjet() {
    const payload = {
    nom: nomProjet.value,
    client: clientId.value,
    fpack_id: selectedFPackId.value,
    selections: Object.entries(selectedItems.value).map(([group_id, data]) => ({
        groupe_id: +group_id,
        type_item: data.type,
        ref_id: data.ref_id
    }))
    }

  await axios.post('http://localhost:8000/projets', payload)
  alert("Projet créé avec succès")
}
</script>

<template>
  <div class="projet-container">
    <h2>Créer un Projet</h2>

    <label>Nom du projet :</label>
    <input v-model="nomProjet" placeholder="Nom du projet" />
    <label>Client ID :</label>
    <input type="number" v-model="clientId" />
    <label>Sélectionner un template FPack :</label>
    <select v-model="selectedFPackId" @change="loadTemplateConfig">
      <option :value="null">-- Choisir --</option>
      <option v-for="f in fpacks" :key="f.id" :value="f.id">{{ f.nom }}</option>
    </select>

    <div v-if="produitsFixes.length || equipementsFixes.length">
      <h3>Produits ajoutés automatiquement</h3>
      <ul>
        <li v-for="p in produitsFixes" :key="p.ref_id">{{ p.display_name }}</li>
      </ul>
      <h3>Équipements ajoutés automatiquement</h3>
      <ul>
        <li v-for="e in equipementsFixes" :key="e.ref_id">{{ e.display_name }}</li>
      </ul>
    </div>

    <div v-if="groupes.length">
      <h3>Choix des éléments dans les groupes</h3>
      <div v-for="g in groupes" :key="g.ref_id">
        <label>{{ g.display_name }}</label>
        <select v-model="selectedItems[g.ref_id]">
          <option disabled :value="null">-- Choisir --</option>
          <option v-for="item in g.group_items" :key="item.ref_id" :value="{ type: item.type, ref_id: item.ref_id }">
            {{ item.label }}
          </option>
        </select>
      </div>
    </div>

    <button :disabled="!nomProjet || !selectedFPackId || groupes.length !== Object.keys(selectedItems).length" @click="submitProjet">
      Créer le projet
    </button>
  </div>
</template>

<style scoped>
.projet-container {
  max-width: 700px;
  margin: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
select, input {
  padding: 0.4rem;
  font-size: 1rem;
}
</style>
