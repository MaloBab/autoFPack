<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '../components/Interaction/PageHeader.vue'
import SQLTable from '../components/Table/Table.vue'
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
  margin-left: 1%;
  margin-top: 0.5%;
  position: relative;
  overflow: hidden;
  background-color: #ef4444;
  color: white;
  font-weight: 700;
  font-size: 0.9rem;
  padding: 0.6rem 1.2rem;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  box-shadow: 0 8px 15px rgba(239, 68, 68, 0.3);
  transition: box-shadow 0.3s ease, transform 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 1px;
  user-select: none;
}

.btn-incompat:hover {
  background-color: #d63c3c;
  box-shadow: 0 12px 25px rgba(239, 68, 68, 0.4);
  transform: translateY(-3px);
}

.btn-incompat:active {
  box-shadow: 0 6px 12px rgba(239, 68, 68, 0.3);
  transform: translateY(1px);
}

.btn-prix {
  margin-left: 0.2%;
  margin-top: 0.5%;
  position: relative;
  overflow: hidden;
  background-color: #727272;
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
  padding: 0.6rem 1.2rem;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  box-shadow: 0 8px 15px rgba(114, 114, 114, 0.3);
  transition: box-shadow 0.3s ease, transform 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 1px;
  user-select: none;
}

.btn-prix:hover {
  background-color: #525252;
  box-shadow: 0 12px 25px rgba(114, 114, 114, 0.4);
  transform: translateY(-3px);
}

.btn-prix:active {
  box-shadow: 0 6px 12px rgba(114, 114, 114, 0.3);
  transform: translateY(1px);
}

</style>