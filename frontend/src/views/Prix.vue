<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import TableReader from '../components/TableReader.vue'
import TextSearch from '../components/TextSearch.vue'

const ajouter = ref(false)
const searchTerm = ref('')

function resetAjouter() {
  ajouter.value = false
}
</script>

<template>
  <div>
    <PageHeader titre="Prix" @ajouter="ajouter = true" />
    <TableReader
      tableName="prix"
      :ajouter="ajouter"
      :search="searchTerm"
      @added="resetAjouter"
      @cancelled="resetAjouter"
    />
    <TextSearch v-model="searchTerm" />
  </div>
</template>