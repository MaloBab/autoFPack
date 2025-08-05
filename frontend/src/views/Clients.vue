<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '../components/Interaction/PageHeader.vue'
import TextSearch from '../components/Searching/TextSearch.vue'
import SQLTable from '../components/Table/Table.vue'

const ajouter = ref(false)
const searchTerm = ref('')

function resetAjouter() {
  ajouter.value = false
}
</script>

<template>
  <div>
    <PageHeader titre="Clients" @ajouter="ajouter = true" />
    <SQLTable
      tableName="clients"
      :ajouter="ajouter"
      :search="searchTerm"
      @added="resetAjouter"
      @cancelled="resetAjouter"
    />
    <TextSearch v-model="searchTerm" />
  </div>
</template>
