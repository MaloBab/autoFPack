<script setup lang="ts">
import { computed, defineEmits, defineProps, ref, watch } from 'vue'
import { useTableReader } from '../../composables/Table/useTableReader'
import { useTableConfig } from '../../composables/Table/useTableConfig'
import { useTableFilters } from '../../composables/Table/useTableFilters'
import { useTableSorting } from '../../composables/Table/useTableSorting'
import { useTableNavigation } from '../../composables/Table/useTableNavigation'
import { useTableRowHandlers } from '../../composables/Table/useTableRowHandlers'
import { useForeignKeyHandlers } from '../../composables/Table/useForeignKeyHandlers'
import Filters from '../Searching/Filters.vue'
import TableRowAdd from './TableRowAdd.vue'
import TableRowEdit from './TableRowEdit.vue'
import TableRowDisplay from './TableRowDisplay.vue'
import TableActions from './TableActions.vue'

const scrollContainer = ref<HTMLElement | null>(null)

const props = defineProps<{
  tableName: string
  apiUrl?: string
  ajouter?: boolean
  search?: string
}>()

const emit = defineEmits(['added', 'cancelled'])

// Composables
const filters = ref<Record<string, Set<any>>>({})
const tableData = useTableReader(props, emit, filters)
const { tableConfig } = useTableConfig(props.tableName)
const { columnValues, filteredRows, updateFilter } = useTableFilters(tableData, filters, props)

const { sortOrders, onSortChange, filteredAndSortedRows } = useTableSorting(filteredRows, tableData.valueLabels)
const { remplirEquipement, remplirFPack, remplirProjet } = useTableNavigation(props.tableName)
const { getEditingId, handleStartEdit, handleValidateEdit, handleDeleteRow } = useTableRowHandlers(tableData, props.tableName)
const foreignKeyHandlers = useForeignKeyHandlers(tableData, props.tableName)

// Colonnes ordonnées
const orderedColumns = computed(() => {
  if (!tableData.columns.value) return []
  const cols = tableData.columns.value.filter((col:any) => 
    (col.toLowerCase() !== 'id' || props.tableName === 'prix_robot') && 
    col.toLowerCase() !== 'reference'
  )
  if (tableData.columns.value.some((col:any) => col.toLowerCase() === 'reference')) {
    cols.unshift('reference')
  }
  return cols
})

// Fonction pour obtenir le label d'une colonne
function getColumnLabel(col: string): string {
  const mappings: Record<string, Record<string, string>> = {
    produits: { fournisseur_id: 'Fournisseur' },
    prix: { client_id: 'Client', produit_id: 'Produit' },
    prix_robot: { id: 'Robot' },
    projets: { fpack_id: 'Fpack' }
  }
  return mappings[props.tableName]?.[col] || col.charAt(0).toUpperCase() + col.slice(1)
}

// Gestion du scroll et duplication
async function onDuplicate(row: any) {
  await tableData.duplicateRow(row)
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
  }
}

// Watch pour scroll lors de l'ajout
watch(() => props.ajouter, (val) => {
  if (val && scrollContainer.value) {
    scrollContainer.value.scrollTop = 0
  }
  foreignKeyHandlers.initializeNewRow(val)
})
</script>

<template>
  <div class="table-container">
    <table class="table-head">
      <thead>
        <tr>
          <th v-for="col in orderedColumns" :key="col">
            <div class="table-header-cell">
              <span>{{ getColumnLabel(col) }}</span>
              <Filters
                :column="col"
                :values="[...columnValues[col] || []]"
                :selected="filters[col] || new Set([...columnValues[col] || []])"
                :labels="tableData.valueLabels.value[col]"
                :sort-order="sortOrders[col] || null"
                @filter-change="updateFilter"
                @sort-change="onSortChange"
              />
            </div>
          </th>
          <th>Actions</th>
        </tr>
      </thead>
    </table>
    
    <div class="table-body-scroll" ref="scrollContainer">
      <table>
        <tbody>
          <!-- Ligne d'ajout -->
          <TableRowAdd
            v-if="ajouter"
            :columns="orderedColumns"
            :table-name="props.tableName"
            :new-row="tableData.newRow.value"
            :table-data="tableData"
            :column-values="columnValues"
            @validate="tableData.validateAdd"
            @cancel="tableData.cancelAdd"
          />

          <!-- Lignes de données -->
          <tr v-for="row in filteredAndSortedRows" :key="row.id">
            <!-- Cellules de données -->
            <template v-if="getEditingId(row)">
              <!-- Mode édition -->
              <TableRowEdit
                :row="row"
                :columns="orderedColumns"
                :table-name="props.tableName"
                :edit-row="tableData.editRow.value"
                :table-data="tableData"
                :column-values="columnValues"
                @validate="handleValidateEdit(row)"
                @cancel="tableData.cancelEdit"
              />
            </template>
            <template v-else>
              <!-- Mode lecture -->
              <TableRowDisplay
                :row="row"
                :columns="orderedColumns"
                :table-name="props.tableName"
                :table-data="tableData"
              />
            </template>

            <!-- Actions -->
            <TableActions
              :row="row"
              :is-editing="!!getEditingId(row)"
              :table-config="tableConfig"
              @edit="handleStartEdit(row)"
              @delete="handleDeleteRow(row)"
              @validate-edit="handleValidateEdit(row)"
              @cancel-edit="tableData.cancelEdit"
              @duplicate="onDuplicate(row)"
              @export="tableData.ExportRow(row)"
              @remplir-equipement="remplirEquipement(row)"
              @remplir-fpack="remplirFPack(row)"
              @remplir-projet="remplirProjet(row)"
            />
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.table-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  background: #f7f7f7;
}

.table-head {
  width: 95%;
  margin-top: 3%;
  margin-left: 2%;
  min-width: 80%;
  border-spacing: 0;
  background: white;
  font-family: inherit;
  border-radius: 1.5%;
  table-layout: fixed;
}

.table-header-cell {
  display: flex;
  align-items: center;     /* centre verticalement */
  justify-content: center; /* centre horizontalement */
  margin-left: 5%;
  gap: 0.3rem;    
}

.table-body-scroll {
  width: 95%;
  margin-left: 2%;
  max-height: 40vh;
  overflow-y: auto;
  padding-left: 1%;
  background: white;
  scrollbar-width: thin;
  scrollbar-color: #b3b3b3 #f3f4f6;
  text-align: center;
}

.table-body-scroll::-webkit-scrollbar {
  width: 10px;
  height: 10px;
  background: #f3f4f6;
  border-radius: 8px;
}
.table-body-scroll::-webkit-scrollbar-thumb {
  background: #b3b3b3;
  border-radius: 8px;
}
.table-body-scroll::-webkit-scrollbar-thumb:hover {
  background: #4d4e4f;
}

.table-body-scroll table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: white;
  font-family: inherit;
  table-layout: fixed;
}

th, td {
  padding: 0.75rem 1rem;
  text-align: center
}

th {
  font-weight: 600;
  color: #222;
  background: #eaeaea;
  border-bottom: 1px solid #e5e7eb;
}

.table-body-scroll ::v-deep tbody tr > * {
  border-bottom: 1px solid #e9e9e9;
}

.table-body-scroll ::v-deep tbody tr:last-child > * {
  border-bottom: none;
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

input, select {
  border: 1px solid #bbb;
  border-radius: 4px;
  padding: 0.3rem 0.5rem;
  font-size: 1rem;
  font-family: inherit;
  background: #f9fafb;
  color: #222;
  outline: none;
  transition: border 0.2s;
  width: 80%;
  min-width: 60px;
  max-width: 200px;
}
input:focus, select:focus {
  border: 1.5px solid #2563eb;
  background: #fff;
}
</style>