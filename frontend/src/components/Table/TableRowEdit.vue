<script setup lang="ts">
import { defineEmits, defineProps } from 'vue'
import AutoComplete from '../Searching/AutoCompleteInput.vue'
import TableCellForeignKey from '../Table/TableCellForeignKey.vue'

const props = defineProps<{
  row: any
  columns: string[]
  tableName: string
  editRow: any
  tableData: any
  columnValues: Record<string, Set<any>>
}>()

const emit = defineEmits(['validate', 'cancel'])

function isForeignKeyColumn(col: string, tableName: string): boolean {
  const foreignKeys = {
    produits: ['fournisseur_id'],
    fpacks: ['client'],
    projets: ['client', 'fpack_id'],
    robots: ['client'],
    prix: ['produit_id', 'client_id'],
    prix_robot: ['id', 'reference']
  }
  
  return foreignKeys[tableName]?.includes(col) || false
}
</script>

<template>
  <td v-for="col in props.columns" :key="col">
    <TableCellForeignKey
      v-if="isForeignKeyColumn(col, props.tableName)"
      :column="col"
      :table-name="props.tableName"
      :model-value="props.editRow"
      :table-data="props.tableData"
      mode="edit"
      @keyup.enter="emit('validate')"
    />
    
    <AutoComplete
      v-else-if="col !== 'id'"
      v-model="props.editRow[col]"
      @keyup.enter="emit('validate')"
      :suggestions="[...props.columnValues[col] || []]"
    />
  </td>
</template>