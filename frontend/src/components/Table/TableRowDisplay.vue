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
        return tableData.fournisseurs.value.find((f:any) => f.id === row.fournisseur_id)?.nom || row.fournisseur_id
      }
      break
      
    case 'client':
      if (['fpacks', 'projets_global', 'robots'].includes(tableName)) {
        return tableData.clients.value.find((c:any) => c.id === row.client)?.nom || row.client
      }
      break
      
    case 'fpack_id':
      if (tableName === 'projets') {
        return tableData.fpacks.value.find((f:any) => f.id === row.fpack_id)?.nom || row.fpack_id
      }
      break
      
    case 'produit_id':
      if (tableName === 'prix') {
        return tableData.produits.value.find((p:any) => p.id === row.produit_id)?.nom || row.produit_id
      }
      break
      
    case 'client_id':
      if (tableName === 'prix') {
        return tableData.clients.value.find((c:any) => c.id === row.client_id)?.nom || row.client_id
      }
      break
      
    case 'id':
      if (tableName === 'prix_robot') {
        return tableData.robots.value.find((r:any) => r.id === row.id)?.nom || row.id
      }
      break
      
    case 'nom':
      if (tableName === 'projets') {
        return `${row.complet ? '✔️' : '⏳'} | ${row.nom}`
      }
      break

    case 'prix_produit':
    case 'prix_transport':
      if (tableName === 'prix' && typeof row[col] === 'number') {
        return `${row[col].toLocaleString('fr-FR')} €`
      }
      break
  }
  
  return row[col]
}

function getCellType(value: any) {
  if (typeof value === 'number') return 'number'
  if (typeof value === 'boolean') return 'boolean'
  if (value && typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}/)) return 'date'
  if (value && typeof value === 'string' && value.includes('@')) return 'email'
  if (value && typeof value === 'string' && value.match(/^https?:\/\//)) return 'url'
  if (value && typeof value === 'string' && value.includes('€')) return 'currency'
  return 'text'
}

function formatCellValue(value: any, type: string) {
  switch (type) {
    case 'number':
      return new Intl.NumberFormat('fr-FR').format(value)
    case 'currency':
      return value
    case 'date':
      return new Date(value).toLocaleDateString('fr-FR')
    case 'boolean':
      return value ? '✅' : '❌'
    default:
      return value
  }
}

</script>

<template>
  <td 
    v-for="col in props.columns" 
    :key="col" 
    class="modern-cell"
    :class="[
      `cell-${getCellType(getDisplayValue(props.row, col, props.tableName, props.tableData))}`,
      `cell-disp`
    ]"
  >
    <div class="cell-content">
      <div class="cell-value">
        {{ formatCellValue(
          getDisplayValue(props.row, col, props.tableName, props.tableData),
          getCellType(getDisplayValue(props.row, col, props.tableName, props.tableData))
        ) }}
      </div>
      
      <div 
        v-if="getCellType(getDisplayValue(props.row, col, props.tableName, props.tableData)) !== 'text'" 
        class="cell-type-indicator"
      >
        <span v-if="getCellType(getDisplayValue(props.row, col, props.tableName, props.tableData)) === 'currency'">💰</span>
        <span v-else-if="getCellType(getDisplayValue(props.row, col, props.tableName, props.tableData)) === 'date'">📅</span>
        <span v-else-if="getCellType(getDisplayValue(props.row, col, props.tableName, props.tableData)) === 'email'">📧</span>
        <span v-else-if="getCellType(getDisplayValue(props.row, col, props.tableName, props.tableData)) === 'url'">🔗</span>
        <span v-else-if="getCellType(getDisplayValue(props.row, col, props.tableName, props.tableData)) === 'boolean'">🔘</span>
      </div>
      
      <div class="cell-highlight"></div>
    </div>
  </td>
</template>

<style scoped>
.modern-cell {
  position: relative;
  padding: 0.875rem 1rem !important;
  vertical-align: middle;
  transition: all 0.2s ease;
  text-align: center;
  overflow: hidden;
}

.cell-content {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-height: 1.5rem;
}

.cell-value {
  flex: 1;
  font-weight: 500;
  color: var(--text-primary);
  transition: all 0.2s ease;
  line-height: 1.4;
}

.cell-type-indicator {
  opacity: 0;
  font-size: 0.75rem;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.modern-cell:hover .cell-type-indicator {
  opacity: 0.7;
}

.cell-highlight {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.1), transparent);
  transform: translateX(-100%);
  transition: transform 0.6s ease;
  pointer-events: none;
}

.modern-cell:hover .cell-highlight {
  transform: translateX(100%);
}

.cell-number .cell-value,
.cell-currency .cell-value {
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  font-weight: 600;
  text-align: center;
  color: #059669;
}

.cell-currency .cell-value {
  color: #dca226;
  font-weight: 700;
}

.cell-date .cell-value {
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  color: #7c3aed;
  font-weight: 500;
}

.cell-email .cell-value {
  color: #dc2626;
  text-decoration: none;
  cursor: pointer;
}

.cell-email:hover .cell-value {
  text-decoration: underline;
}

.cell-url .cell-value {
  color: #2563eb;
  text-decoration: none;
  cursor: pointer;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-url:hover .cell-value {
  text-decoration: underline;
}

.cell-boolean .cell-value {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
}


.cell-disp {
  border-left: 3px solid transparent;
}

.cell-disp:hover {
  background: rgba(59, 130, 246, 0.05);
  border-left-color: #3b82f6;
  transform: translateX(2px);
}

.modern-cell {
  animation: cellSlideIn 0.3s ease-out;
  animation-fill-mode: both;
}

@keyframes cellSlideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>