<script setup lang="ts">
import { defineProps } from 'vue'

const props = defineProps<{
  row: any
  columns: string[]
  tableName: string
  tableData: any
}>()

function getDisplayValue(row: any, col: string, tableName: string, tableData: any) {
  switch (col) {
    case 'fournisseur_id':
      if (tableName === 'produits') {
        return tableData.fournisseurs.value.find(f => f.id === row.fournisseur_id)?.nom || row.fournisseur_id
      }
      break
      
    case 'client':
      if (['fpacks', 'projets_global', 'robots'].includes(tableName)) {
        return tableData.clients.value.find(c => c.id === row.client)?.nom || row.client
      }
      break
      
    case 'fpack_id':
      if (tableName === 'projets') {
        return tableData.fpacks.value.find(f => f.id === row.fpack_id)?.nom || row.fpack_id
      }
      break
      
    case 'produit_id':
      if (tableName === 'prix') {
        return tableData.produits.value.find(p => p.id === row.produit_id)?.nom || row.produit_id
      }
      break
      
    case 'client_id':
      if (tableName === 'prix') {
        return tableData.clients.value.find(c => c.id === row.client_id)?.nom || row.client_id
      }
      break
      
    case 'id':
      if (tableName === 'prix_robot') {
        return tableData.robots.value.find(r => r.id === row.id)?.nom || row.id
      }
      break
      
    case 'nom':
      if (tableName === 'projets') {
        return `${row.complet ? '✔️' : '⏳'} | ${row.nom}`
      }
      break
  }
  
  return row[col]
}
</script>

<template>
  <td v-for="col in columns" :key="col">
    {{ getDisplayValue(row, col, tableName, tableData) }}
  </td>
</template>