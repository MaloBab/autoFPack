<script setup lang="ts">
import { ref, onMounted, watch, defineEmits } from 'vue'
import axios from 'axios'

const emit = defineEmits(['added', 'cancelled'])

const props = defineProps<{
  tableName: string
  apiUrl?: string
  ajouter?: boolean
}>()

const columns = ref<string[]>([])
const rows = ref<any[]>([])
const newRow = ref<any>({})
const adding = ref(false)

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

watch(() => props.ajouter, (val) => {
  if (val) startAddRow()
})

function startAddRow() {
  if (adding.value) return
  adding.value = true
  newRow.value = {}
  columns.value.forEach(col => newRow.value[col] = '')
}

async function validateAdd() {
  try {
    const dataToSend = { ...newRow.value }
    delete dataToSend.id
    await axios.post(
      props.apiUrl
        ? `${props.apiUrl}/${props.tableName}`
        : `http://localhost:8000/${props.tableName}`,
      dataToSend
    )
    adding.value = false
    await fetchData()
    emit('added')
  } catch (e) {
    alert("Erreur lors de l'ajout")
  }
}

function cancelAdd() {
  adding.value = false
  emit('cancelled')
}
</script>

<template>
  <div>
    <table>
      <thead>
        <tr>
          <th v-for="col in columns" :key="col">{{ col }}</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="adding">
          <td v-for="col in columns" :key="col">
            <input v-if="col !== 'id'" v-model="newRow[col]" />
          </td>
          <td class="actions">
            <button @click="validateAdd">✅</button>
            <button @click="cancelAdd">❌</button>
          </td>
        </tr>
        <tr v-for="row in rows" :key="row.id">
          <td v-for="col in columns" :key="col">{{ row[col] }}</td>
          <td class="actions">
            <button title="Éditer">✏️</button>
            <button title="Supprimer">🗑️</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>



<style scoped>
.add-btn {
  margin-bottom: 1rem;
  background: #2563eb;
  color: #fff;
  border: none;
  padding: 0.5rem 1.2rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}
.add-btn:hover {
  background: #1d4ed8;
}

table {
  width: 80%;
  margin-top: 3%;
  margin-left: 2%;
  border-collapse: separate;
  border-spacing: 0;
  background: white;
  font-family: inherit;
  border-radius: 1.5%;
  overflow: hidden; 
}

th, td {
  padding: 0.75rem 1rem;
  text-align: left;
}

th {
  font-weight: 600;
  color: #222;
  background: #eaeaea;
  border-bottom: 1px solid #e5e7eb;
}

tbody tr {
  border-bottom: 1px solid #e5e7eb;
}

tbody tr:last-child {
  border-bottom: none;
}

td {
  vertical-align: middle;
  font-size: 1rem;
  color: #222;
}

.actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.actions button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-size: 1.5rem; 
  color: #222;
}

.actions button:hover {
  color: #2563eb;
}
</style>