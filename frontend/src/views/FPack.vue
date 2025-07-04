<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import TextSearch from '../components/TextSearch.vue'
import TopLevelTable from '../components/TopLevelTable.vue'

const ajouter = ref(false)
const searchTerm = ref('')

function resetAjouter() {
  ajouter.value = false
}

</script>

<template>
  <div>
    <PageHeader titre="FPacks" @ajouter="ajouter = true" />

    <TopLevelTable
      tableName="fpacks"
      :ajouter="ajouter"
      :search="searchTerm"
      @added="resetAjouter"
      @cancelled="resetAjouter"
    />

    <TextSearch v-model="searchTerm" />
  </div>
</template>
