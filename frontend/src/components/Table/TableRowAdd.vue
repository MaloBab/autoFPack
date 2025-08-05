<!-- components/TableRowAdd.vue -->
<script setup lang="ts">
import { defineEmits, defineProps } from 'vue'
import AutoComplete from '../Searching/AutoCompleteInput.vue'
import TableCellForeignKey from '../Table/TableCellForeignKey.vue'

const props = defineProps<{
  columns: string[]
  tableName: string
  newRow: any
  tableData: any
  columnValues: Record<string, Set<any>>
}>()

const emit = defineEmits(['validate', 'cancel'])

function isForeignKeyColumn(col: string, tableName: string): boolean {
  const foreignKeys = {
    produits: ['fournisseur_id'],
    fpacks: ['client'],
    projets_global: ['client'],
    robots: ['client'],
    prix: ['produit_id', 'client_id'],
    prix_robot: ['id', 'reference']
  }
  
  return foreignKeys[tableName]?.includes(col) || false
}

</script>

<template>
  <tr>
    <td v-for="col in columns" :key="col">
      <TableCellForeignKey
        v-if="isForeignKeyColumn(col, tableName)"
        :column="col"
        :table-name="tableName"
        :model-value="newRow"
        :table-data="tableData"
        mode="add"
        @keyup.enter="emit('validate')"
      />
      
      <AutoComplete
        v-else-if="col !== 'id'"
        v-model="newRow[col]"
        @keyup.enter="emit('validate')"
        :suggestions="[...columnValues[col] || []]"
      />
    </td>
    <td class="actions">
      <button @click="emit('validate')">✅</button>
      <button @click="emit('cancel')">❌</button>
    </td>
  </tr>
</template>

<style scoped>
.actions {
  display: flex;
  gap: 0.6rem;
  align-items: flex-end;
  margin-left: 14px;
}

.actions button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-size: 1.2rem;
  color: #222;
}
</style>