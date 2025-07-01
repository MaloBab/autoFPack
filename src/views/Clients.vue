<script lang="ts">
import { defineComponent } from 'vue';
import PageHeader from '../components/PageHeader.vue';

export default defineComponent({
  name: 'Clients',
  components: {
    PageHeader
  }
});
</script>

<template>
  <div>
    <PageHeader titre="Clients" />
  </div>
</template>
