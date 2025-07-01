<script lang="ts">
import { defineComponent } from 'vue';
import PageHeader from '../components/PageHeader.vue';
import TableReader from '../components/TableReader.vue'

export default defineComponent({
  name: 'Produits',
  components: {
    PageHeader,
    TableReader
  }
});
</script>

<template>
  <div>
    <PageHeader titre="Produits" />
     <TableReader tableName="produits" />
  </div>
</template>

