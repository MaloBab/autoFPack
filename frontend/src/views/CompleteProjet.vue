<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { showToast } from '../composables/useToast'

const route = useRoute()
const router = useRouter()

const projet = ref<any>(null)
const configColumns = ref<any[]>([])
const produitsSeuls = ref<any[]>([])
const equipementsSeuls = ref<any[]>([])
const groupes = ref<any[]>([])
const selected = ref<Record<number, any>>({})
const loading = ref(true)

onMounted(async () => {
  const projetId = route.params.id
  try {
    const resProjet = await axios.get(`/projets/${projetId}/complete`)
    projet.value = resProjet.data

    const resConfig = await axios.get(`/fpack_config_columns/${projet.value.fpack_id}`)
    configColumns.value = resConfig.data

    produitsSeuls.value = configColumns.value.filter(c => c.type === 'produit' && !c.group_items)
    equipementsSeuls.value = configColumns.value.filter(c => c.type === 'equipement' && !c.group_items)
    groupes.value = configColumns.value.filter(c => c.type === 'group')

    groupes.value.forEach(g => selected.value[g.ref_id] = '')
  } catch (err) {
    showToast('Erreur lors du chargement du projet ou du FPack', 'error')
  } finally {
    loading.value = false
  }
})

async function save() {
  const selections = [
    ...produitsSeuls.value.map(p => ({
      groupe_id: null,
      type_item: 'produit',
      ref_id: p.ref_id
    })),
    ...equipementsSeuls.value.map(e => ({
      groupe_id: null,
      type_item: 'equipement',
      ref_id: e.ref_id
    })),
    ...groupes.value.map(g => ({
      groupe_id: g.ref_id,
      type_item: selected.value[g.ref_id]?.type,
      ref_id: selected.value[g.ref_id]?.ref_id
    }))
  ].filter(sel => sel.ref_id)

  try {
    await axios.put(`/projets/${projet.value.id}/complete`, {
      nom: projet.value.nom,
      client: projet.value.client,
      fpack_id: projet.value.fpack_id,
      selections
    })
    showToast('Projet complété avec succès', 'success')
    router.push('/projets')
  } catch (err) {
    showToast("Erreur lors de l'enregistrement", 'error')
  }
}
</script>

<template>
  <div class="p-6 bg-gray-50 min-h-screen">
    <div v-if="loading" class="text-center text-gray-500 mt-10">Chargement des données...</div>

    <div v-else class="mt-6 space-y-8">
      <section>
        <h2 class="text-lg font-semibold text-gray-700">Produits seuls</h2>
        <ul class="list-disc list-inside text-gray-800">
          <li v-for="p in produitsSeuls" :key="p.ref_id">{{ p.display_name }}</li>
        </ul>
      </section>

      <section>
        <h2 class="text-lg font-semibold text-gray-700">Équipements seuls</h2>
        <ul class="list-disc list-inside text-gray-800">
          <li v-for="e in equipementsSeuls" :key="e.ref_id">{{ e.display_name }}</li>
        </ul>
      </section>

      <section>
        <h2 class="text-lg font-semibold text-gray-700">Groupes à compléter</h2>
        <div v-for="groupe in groupes" :key="groupe.ref_id" class="mt-4">
          <label class="block mb-1 text-sm font-medium text-gray-600">{{ groupe.display_name }}</label>
          <select v-model="selected[groupe.ref_id]" class="w-full p-2 border border-gray-300 rounded-md">
            <option disabled value="">-- Choisir un élément --</option>
            <option
              v-for="item in groupe.group_items"
              :key="item.ref_id"
              :value="item"
            >
              {{ item.label }}
            </option>
          </select>
        </div>
      </section>

      <div class="flex justify-end">
        <button
          @click="save"
          class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded shadow"
        >
          💾 Enregistrer
        </button>
      </div>
    </div>
  </div>
</template>