<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ConfigureFPackTable from '../components/ConfigureFPackTable.vue'

const route = useRoute()
const fpackId = ref<number | null>(null)

onMounted(() => {
  const rawId = Number(route.params.id)
  if (!isNaN(rawId)) {
    fpackId.value = rawId
  }
  }
)
</script>

<template>
  <div>
    <p v-if="fpackId === null">Chargement de la configuration...</p>
    <ConfigureFPackTable v-else :fpackId="fpackId" />
  </div>
</template>