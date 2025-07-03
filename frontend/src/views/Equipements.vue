<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import TextSearch from '../components/TextSearch.vue'
import EquipementTable from '../components/EquipementTable.vue'

const ajouter = ref(false)
const searchTerm = ref('')

function resetAjouter() {
  ajouter.value = false
}

</script>

<template>
  <div>
    <PageHeader titre="Equipements" @ajouter="ajouter = true" />

    <EquipementTable
      tableName="groupes"
      :ajouter="ajouter"
      :search="searchTerm"
      @added="resetAjouter"
      @cancelled="resetAjouter"
    />

    <TextSearch v-model="searchTerm" />
  </div>
</template>
