<!-- filepath: src/components/TableGenerique.vue -->
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'

const props = defineProps<{
  tableName: string
  apiUrl?: string 
}>()

const columns = ref<string[]>([])
const rows = ref<any[]>([])

const fetchData = async () => {
  const colRes = await axios.get(
    props.apiUrl
      ? `${props.apiUrl}/table-columns/${props.tableName}`
      : `http://localhost:8000/table-columns/${props.tableName}`
  )
  columns.value = colRes.data

  const dataRes = await axios.get(
    props.apiUrl
      ? `${props.apiUrl}/${props.tableName}`
      : `http://localhost:8000/${props.tableName}`
  )
  rows.value = dataRes.data
}

onMounted(fetchData)
watch(() => props.tableName, fetchData)
</script>

<template>
  <table>
    <thead>
      <tr>
        <th v-for="col in columns" :key="col">{{ col }}</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="row in rows" :key="row.id">
        <td v-for="col in columns" :key="col">{{ row[col] }}</td>
        <td>
          <!-- Actions personnalisées ici -->
        </td>
      </tr>
    </tbody>
  </table>
</template>