<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import TopLevelTable from '../components/TopLevelTable.vue'
import { showToast } from '../composables/useToast'
import TextSearch from '../components/TextSearch.vue'
import axios from 'axios'

const projets = ref<any[]>([])
const loading = ref(false)
const ajouter = ref(false)
const searchTerm = ref('')

function resetAjouter() {
  ajouter.value = false
}

async function fetchProjets() {
  loading.value = true
  try {
    const response = await axios.get('http://localhost:8000/projets')
    projets.value = response.data
  } catch (e) {
    console.error(e)
    showToast('Erreur lors du chargement des projets', 'error')
  } finally {
    loading.value = false
  }
}
fetchProjets()
</script>

<template>
  <div class="p-6">
    <PageHeader titre="Projet" @ajouter="ajouter = true" />
    <TopLevelTable
      tableName="projets"
      :ajouter="ajouter"
      :search="searchTerm"
      @added="resetAjouter"
      @cancelled="resetAjouter"
    />
    <TextSearch v-model="searchTerm" />
  </div>
</template>


