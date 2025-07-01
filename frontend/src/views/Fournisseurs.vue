<script lang="ts">
import { defineComponent } from 'vue';
import PageHeader from '../components/PageHeader.vue';

export default defineComponent({
  name: 'Fournisseurs',
  components: {
    PageHeader
  }
});
</script>

<template>
  <div>
    <PageHeader titre="Fournisseurs" />
  </div>
</template>