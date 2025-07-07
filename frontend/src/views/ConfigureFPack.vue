<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ConfigureFPackTable from '../components/ConfigureFPackTable.vue'
import axios from 'axios'

const route = useRoute()
const fpackId = ref<number | null>(null)
const fpackName = ref<string>('')

onMounted(async () => {
  const rawId = Number(route.params.id)
  if (!isNaN(rawId)) {
    fpackId.value = rawId
    const res = await axios.get(`http://localhost:8000/fpacks/${rawId}`)
    fpackName.value = res.data.nom
  }
})
</script>

<template>
  <div>
    <p v-if="fpackId === null">Chargement de la configuration...</p>
    <ConfigureFPackTable
      v-else
      :fpackId="fpackId"
      :fpackName="fpackName"
    />
  </div>
</template>