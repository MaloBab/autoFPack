<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '../components/Interaction/PageHeader.vue'
import { showToast } from '../composables/useToast'
import TextSearch from '../components/Searching/TextSearch.vue'
import axios from 'axios'
import SQLTable from '../components/Table/Table.vue'

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
    <PageHeader titre="Projets" @ajouter="ajouter = true" />
    <SQLTable
      tableName="projets_global"
      :ajouter="ajouter"
      :search="searchTerm"
      @added="resetAjouter"
      @cancelled="resetAjouter"
    />
    <TextSearch v-model="searchTerm" />
</template>


