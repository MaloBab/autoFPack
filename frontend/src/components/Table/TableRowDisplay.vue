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
      
    // Formatage spécial pour les prix
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
      return value // Déjà formaté dans getDisplayValue
    case 'date':
      return new Date(value).toLocaleDateString('fr-FR')
    case 'boolean':
      return value ? '✅' : '❌'
    default:
      return value
  }
}

function getCellVariant(col: string, value: any, tableName: string) {
  if (col === 'nom' && tableName === 'projets') {
    return props.row.complet ? 'success' : 'warning'
  }
  if (col === 'prix_produit' || col === 'prix_transport') {
    if (typeof props.row[col] === 'number') {
      if (props.row[col] > 1000) return 'success'
      if (props.row[col] < 100) return 'warning'
    }
  }
  if (typeof value === 'number' && value < 0) return 'danger'
  if (typeof value === 'boolean') return value ? 'success' : 'danger'
  return 'default'
}
</script>

<template>
  <td 
    v-for="col in props.columns" 
    :key="col" 
    class="modern-cell"
    :class="[
      `cell-${getCellType(getDisplayValue(props.row, col, props.tableName, props.tableData))}`,
      `cell-variant-${getCellVariant(col, getDisplayValue(props.row, col, props.tableName, props.tableData), props.tableName)}`
    ]"
  >
    <div class="cell-content">
      <div class="cell-value">
        {{ formatCellValue(
          getDisplayValue(props.row, col, props.tableName, props.tableData),
          getCellType(getDisplayValue(props.row, col, props.tableName, props.tableData))
        ) }}
      </div>
      
      <!-- Indicateur de type pour certaines cellules -->
      <div 
        v-if="getCellType(getDisplayValue(props.row, col, props.tableName, props.tableData)) !== 'text'" 
        class="cell-type-indicator"
      >
        <span v-if="getCellType(getDisplayValue(props.row, col, props.tableName, props.tableData)) === 'number'">🔢</span>
        <span v-else-if="getCellType(getDisplayValue(props.row, col, props.tableName, props.tableData)) === 'currency'">💰</span>
        <span v-else-if="getCellType(getDisplayValue(props.row, col, props.tableName, props.tableData)) === 'date'">📅</span>
        <span v-else-if="getCellType(getDisplayValue(props.row, col, props.tableName, props.tableData)) === 'email'">📧</span>
        <span v-else-if="getCellType(getDisplayValue(props.row, col, props.tableName, props.tableData)) === 'url'">🔗</span>
        <span v-else-if="getCellType(getDisplayValue(props.row, col, props.tableName, props.tableData)) === 'boolean'">🔘</span>
      </div>
      
      <!-- Effet de surbrillance -->
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

/* Types de cellules */
.cell-number .cell-value,
.cell-currency .cell-value {
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  font-weight: 600;
  text-align: center;
  color: #059669;
}

.cell-currency .cell-value {
  color: #dc2626;
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

/* Variants de cellules */
.cell-variant-success {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.05), rgba(34, 197, 94, 0.05));
  border-left: 3px solid #10b981;
}

.cell-variant-success .cell-value {
  color: #065f46;
  font-weight: 600;
}

.cell-variant-warning {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.05), rgba(245, 158, 11, 0.05));
  border-left: 3px solid #f59e0b;
}

.cell-variant-warning .cell-value {
  color: #92400e;
  font-weight: 600;
}

.cell-variant-danger {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.05), rgba(220, 38, 38, 0.05));
  border-left: 3px solid #ef4444;
}

.cell-variant-danger .cell-value {
  color: #991b1b;
  font-weight: 600;
}

.cell-variant-default {
  border-left: 3px solid transparent;
}

/* Effets hover pour les variants */
.cell-variant-success:hover {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(34, 197, 94, 0.1));
  transform: translateX(2px);
}

.cell-variant-warning:hover {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.1), rgba(245, 158, 11, 0.1));
  transform: translateX(2px);
}

.cell-variant-danger:hover {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.1));
  transform: translateX(2px);
}

.cell-variant-default:hover {
  background: rgba(59, 130, 246, 0.05);
  border-left-color: #3b82f6;
  transform: translateX(2px);
}

/* Animation d'entrée pour les cellules */
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