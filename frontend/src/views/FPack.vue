<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '../components/Interaction/PageHeader.vue'
import TextSearch from '../components/Searching/TextSearch.vue'
import ExportButton from '../components/Interaction/ExportButton.vue'
import SQLTable from '../components/Table/Table.vue'

const ajouter = ref(false)
const searchTerm = ref('')

function resetAjouter() {
  ajouter.value = false
}

</script>

<template>
  <div>
    <PageHeader titre="FPacks" @ajouter="ajouter = true" />
    <ExportButton exportUrl="http://localhost:8000/export-fpacks/all" label="Tout exporter"/>
    <SQLTable
      tableName="fpacks"
      :ajouter="ajouter"
      :search="searchTerm"
      @added="resetAjouter"
      @cancelled="resetAjouter"
    />

    <TextSearch v-model="searchTerm" />
  </div>
</template>
