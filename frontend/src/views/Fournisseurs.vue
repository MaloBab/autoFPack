<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import TableReader from '../components/TableReader.vue'
const ajouter = ref(false)

function resetAjouter() {
  ajouter.value = false
}

</script>

<template>
  <div>
    <PageHeader titre="Fournisseurs" @ajouter="ajouter = true"/>
    <TableReader
      tableName="fournisseurs"
      :ajouter="ajouter"
      @added="resetAjouter"
      @cancelled="resetAjouter"
    />
  </div>
</template>