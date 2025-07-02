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
<PageHeader titre="Clients" @ajouter="ajouter = true"/>
    <TableReader
      tableName="clients"
      :ajouter="ajouter"
      @added="resetAjouter"
      @cancelled="resetAjouter"
    />
  </div>
</template>