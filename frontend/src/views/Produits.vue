<script lang="ts">
import { defineComponent } from 'vue';
import PageHeader from '../components/PageHeader.vue';

export default defineComponent({
  name: 'Produits',
  components: {
    PageHeader
  }
});
</script>

<template>
  <div>
    <PageHeader titre="Produits" />
  </div>
</template>

