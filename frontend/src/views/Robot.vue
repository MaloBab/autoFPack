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
    <PageHeader titre="Robots" @ajouter="ajouter = true" />
    <router-link to="/incompatibilites">
      <button class="btn-incompat">⛔ Gérer Incompatibilités</button>
    </router-link>
    <TableReader
      tableName="robots"
      :ajouter="ajouter"
      :search="searchTerm"
      @added="resetAjouter"
      @cancelled="resetAjouter"
    />
    <TextSearch v-model="searchTerm" />
  </div>
</template>

<style lang="css" scoped>

.btn-incompat {
  padding: 0.4rem 0.8rem;
  margin-top: 0.5rem ;
  margin-left: 2%;
  background-color: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.9rem;
  cursor: pointer;
}
</style>
