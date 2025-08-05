<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '../components/Interaction/PageHeader.vue'
import SQLTable from '../components/Table/SQLTable.vue'
import TextSearch from '../components/Searching/TextSearch.vue'
import ExportButton from '../components/Interaction/ExportButton.vue'
import ImportButton from '../components/Interaction/ImportButton.vue'

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
    <PageHeader titre="Produits" @ajouter="ajouter = true" />
    <ExportButton exportUrl="http://localhost:8000/produits/export/excel" label="Exporter produits" />
    <ImportButton addUrl="http://localhost:8000/produits/import/add" @import-success= "refreshTable"/>
    <router-link to="/incompatibilites">
      <button class="btn-incompat">⛔ Gérer Incompatibilités</button>
    </router-link>
    <router-link to="/prix">
      <button class="btn-prix">💵 Gerer Prix</button>
    </router-link>
    
    <SQLTable
      :key="tableKey"
      tableName="produits"
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