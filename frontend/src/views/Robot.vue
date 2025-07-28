<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import TableReader from '../components/TableReader.vue'
import TextSearch from '../components/TextSearch.vue'
import ExportButton from '../components/ExportButton.vue'
import ImportButton from '../components/ImportButton.vue'

const ajouter = ref(false)
const searchTerm = ref('')
const tableKey = ref(0)

function refreshTable() {
  tableKey.value++
}

function resetAjouter() {
  ajouter.value = false
}
</script>

<template>
  <div>
    <PageHeader titre="Robots" @ajouter="ajouter = true" />
    <ExportButton exportUrl="http://localhost:8000/robots/export/excel" label="Exporter robots" />
    <ImportButton addUrl="http://localhost:8000/robots/import/add" @import-success= "refreshTable"/>
    <router-link to="/incompatibilites">
      <button class="btn-incompat">⛔ Gérer Incompatibilités</button>
    </router-link>
    <router-link to="/prix_robot">
      <button class="btn-prix">💵 Gerer Prix</button>
    </router-link>
    <TableReader
      :key="tableKey"
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
  margin-top: 1rem ;
  margin-left: 3%;
  background-color: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.9rem;
  cursor: pointer;
}

.btn-incompat:hover {
  background-color: #d63c3c;

}


.btn-prix {
  padding: 0.4rem 0.8rem;
  margin-top: 0.5rem ;
  margin-left: 2%;
  background-color: #727272;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.9rem;
  cursor: pointer;
}

.btn-prix:hover {
  background-color: #525252;

}

</style>
