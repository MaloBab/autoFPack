<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import TextSearch from '../components/TextSearch.vue'

const ajouter = ref(false)
const searchTerm = ref('')


</script>

<template>
  <div>
    <PageHeader titre="Equipements" @ajouter="ajouter = true" />



    <TextSearch v-model="searchTerm" />
  </div>
</template>
