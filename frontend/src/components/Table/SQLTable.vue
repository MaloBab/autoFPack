<script setup lang="ts">
import { computed, defineEmits, defineProps, reactive, ref, watch } from 'vue'
import { useTableReader } from '../../composables/useTableReader'
import Filters from '../Searching/Filters.vue'
import { useRouter } from 'vue-router'
import AutoComplete from '../Searching/AutoCompleteInput.vue'
import SearchSelect from '../Searching/SearchSelect.vue'

const scrollContainer = ref<HTMLElement | null>(null)

const props = defineProps<{
  tableName: string
  apiUrl?: string
  ajouter?: boolean
  search?: string
}>()
const emit = defineEmits(['added', 'cancelled'])
const router = useRouter()

const filters = ref<Record<string, Set<any>>>({})

const {
  columns, rows, newRow, editingId, editRow, 
  fournisseurs, clients, produits, robots, fpacks,
  validateAdd, cancelAdd, startEdit, validateEdit, cancelEdit, 
  deleteRow, duplicateRow, ExportRow, startEditPrix
} = useTableReader(props, emit, filters)

// Configuration spécifique pour chaque type de table
const tableConfig = computed(() => {
  const configs = {
    produits: { hasRemplir: false, hasDuplicate: true, hasExport: false },
    fournisseurs: { hasRemplir: false, hasDuplicate: false, hasExport: false },
    clients: { hasRemplir: false, hasDuplicate: false, hasExport: false },
    robots: { hasRemplir: false, hasDuplicate: false, hasExport: false },
    prix: { hasRemplir: false, hasDuplicate: false, hasExport: false, hasPrixEdit: true },
    prix_robot: { hasRemplir: false, hasDuplicate: false, hasExport: false },
    equipements: { hasRemplir: true, hasDuplicate: false, hasExport: false, remplirType: 'equipement' },
    fpacks: { hasRemplir: true, hasDuplicate: true, hasExport: true, remplirType: 'fpack' },
    projets: { hasRemplir: true, hasDuplicate: false, hasExport: false, remplirType: 'projet' }
  }
  return configs[props.tableName] || {}
})

const columnValues = computed(() => {
  const map: Record<string, Set<any>> = {}
  for (const row of rows.value) {
    for (const col of columns.value) {
      map[col] ??= new Set()
      map[col].add(row[col])
    }
  }
  return map
})

const filteredRows = computed(() =>
  rows.value
    .filter(row =>
      columns.value.every(col =>
        !filters.value[col] || filters.value[col].has(row[col])
      )
    )
    .filter(row => {
      if (!props.search) return true
      const search = props.search.toLowerCase()
      return columns.value.some(col => {
        let cellValue = row[col]

        // Gestion spéciale pour les foreign keys
        if (['projets', 'fpacks'].includes(props.tableName) && col === 'client') {
          const client = clients.value.find(c => c.id === cellValue)
          cellValue = client?.nom || ''
        }
        if (props.tableName === 'projets' && col === 'fpack_id') {
          const fpack = fpacks.value.find(f => f.id === cellValue)
          cellValue = fpack?.nom || ''
        }
        if (props.tableName === 'produits' && col === 'fournisseur_id') {
          const fournisseur = fournisseurs.value.find(f => f.id === cellValue)
          cellValue = fournisseur?.nom || ''
        }
        if (props.tableName === 'robots' && col === 'client') {
          const client = clients.value.find(c => c.id === cellValue)
          cellValue = client?.nom || ''
        }
        if (props.tableName === 'prix') {
          if (col === 'produit_id') {
            const produit = produits.value.find(p => p.id === cellValue)
            cellValue = produit?.nom || ''
          }
          if (col === 'client_id') {
            const client = clients.value.find(c => c.id === cellValue)
            cellValue = client?.nom || ''
          }
        }
        if (props.tableName === 'prix_robot' && col === 'id') {
          const robot = robots.value.find(r => r.id === cellValue)
          cellValue = robot?.nom || ''
        }

        return String(cellValue).toLowerCase().includes(search)
      })
    })
)

function updateFilter(col: string, values: Set<any>) {
  filters.value[col] = values
}

const valueLabels = computed(() => {
  const map: Record<string, Record<any, string>> = {}

  if (props.tableName === 'produits') {
    map['fournisseur_id'] = Object.fromEntries(
      fournisseurs.value.map(f => [f.id, f.nom])
    )
  }
  if (['fpacks', 'projets', 'robots'].includes(props.tableName)) {
    map['client'] = Object.fromEntries(
      clients.value.map(c => [c.id, c.nom])
    )
  }
  if (props.tableName === 'projets') {
    map['fpack_id'] = Object.fromEntries(
      fpacks.value.map(f => [f.id, f.nom])
    )
  }
  if (props.tableName === 'prix') {
    map['produit_id'] = Object.fromEntries(
      produits.value.map(p => [p.id, p.nom])
    )
    map['client_id'] = Object.fromEntries(
      clients.value.map(c => [c.id, c.nom])
    )
  }
  if (props.tableName === 'prix_robot') {
    map['id'] = Object.fromEntries(
      robots.value.map(r => [r.id, r.nom])
    )
  }
  
  return map
})

const orderedColumns = computed(() => {
  if (!columns.value) return []
  const cols = columns.value.filter(col => 
    (col.toLowerCase() !== 'id' || props.tableName === 'prix_robot') && 
    col.toLowerCase() !== 'reference'
  )
  if (columns.value.some(col => col.toLowerCase() === 'reference')) {
    cols.unshift('reference')
  }
  return cols
})

const sortOrders = reactive<Record<string, 'asc' | 'desc' | null>>({})

function onSortChange(column: string, order: 'asc' | 'desc' | null) {
  sortOrders[column] = order
}

const filteredAndSortedRows = computed(() => {
  let result = filteredRows.value.slice()

  for (const [col, order] of Object.entries(sortOrders)) {
    if (order) {
      result.sort((a, b) => {
        const valA = a[col]
        const valB = b[col]
        const labelA = valueLabels.value[col]?.[valA] ?? valA
        const labelB = valueLabels.value[col]?.[valB] ?? valB

        if (typeof labelA === 'string' && typeof labelB === 'string') {
          return order === 'asc'
            ? labelA.localeCompare(labelB)
            : labelB.localeCompare(labelA)
        }
        if (typeof valA === 'number' && typeof valB === 'number') {
          return order === 'asc' ? valA - valB : valB - valA
        }
        return 0
      })
    }
  }

  return result
})

// Fonctions de navigation
function remplirEquipement(row: any) {
  router.push(`/remplir/${props.tableName}/${row.id}`)
}
function remplirFPack(row: any) {
  router.push(`/configure/${props.tableName}/${row.id}`)
}
function remplirProjet(row: any) {
  router.push(`/complete/${props.tableName}/${row.id}`)
}

// Gestion des fpacks filtrés pour projets
const filteredFpacks = computed(() => {
  if (newRow.value.client_nom) {
    const client = clients.value.find(c => c.nom === newRow.value.client_nom)
    if (client) {
      return fpacks.value.filter(f => f.client === client.id)
    }
  }
  return fpacks.value
})

const filteredFpacksEdit = computed(() => {
  if (editRow.value.client_nom) {
    const client = clients.value.find(c => c.nom === editRow.value.client_nom)
    if (client) {
      return fpacks.value.filter(f => f.client === client.id)
    }
  }
  return fpacks.value
})

// Watchers pour projets
watch(() => newRow.value.client_nom, (clientNom) => {
  if (props.tableName !== 'projets') return
  if (!clientNom) {
    newRow.value.fpack_nom = ''
  } else {
    const client = clients.value.find(c => c.nom === clientNom)
    const fpack = fpacks.value.find(f => f.nom === newRow.value.fpack_nom)
    if (fpack && client && fpack.client !== client.id) {
      newRow.value.fpack_nom = ''
    }
  }
})

watch(() => newRow.value.fpack_nom, (fpackNom) => {
  if (props.tableName !== 'projets' || !fpackNom) return
  const fpack = fpacks.value.find(f => f.nom === fpackNom)
  if (fpack) {
    const client = clients.value.find(c => c.id === fpack.client)
    if (client && newRow.value.client_nom !== client.nom) {
      newRow.value.client_nom = client.nom
    }
  }
})

// Watchers pour prix_robot
watch(() => newRow.value.robot_nom, (nom) => {
  if (props.tableName !== 'prix_robot') return
  const r = robots.value.find(r => r.nom === nom)
  if (r) newRow.value.robot_reference = r.reference
})

watch(() => newRow.value.robot_reference, (ref) => {
  if (props.tableName !== 'prix_robot') return
  const r = robots.value.find(r => r.reference === ref)
  if (r) newRow.value.robot_nom = r.nom
})

watch(() => editRow.value.robot_nom, (nom) => {
  if (props.tableName !== 'prix_robot') return
  const r = robots.value.find(r => r.nom === nom)
  if (r) editRow.value.robot_reference = r.reference
})

watch(() => editRow.value.robot_reference, (ref) => {
  if (props.tableName !== 'prix_robot') return
  const r = robots.value.find(r => r.reference === ref)
  if (r) editRow.value.robot_nom = r.nom
})

// Watchers pour edit projets
watch(() => editRow.value.client_nom, (clientNom) => {
  if (props.tableName !== 'projets') return
  if (!clientNom) {
    editRow.value.fpack_nom = ''
  } else {
    const client = clients.value.find(c => c.nom === clientNom)
    const fpack = fpacks.value.find(f => f.nom === editRow.value.fpack_nom)
    if (fpack && client && fpack.client !== client.id) {
      editRow.value.fpack_nom = ''
    }
  }
})

watch(() => editRow.value.fpack_nom, (fpackNom) => {
  if (props.tableName !== 'projets' || !fpackNom) return
  const fpack = fpacks.value.find(f => f.nom === fpackNom)
  if (fpack) {
    const client = clients.value.find(c => c.id === fpack.client)
    if (client && editRow.value.client_nom !== client.nom) {
      editRow.value.client_nom = client.nom
    }
  }
})

// Scroll et initialisation
watch(() => props.ajouter, (val) => {
  if (val) {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = 0
    }
    
    // Initialisation spéciale pour projets
    if (props.tableName === 'projets') {
      if (!newRow.value.client_nom || !clients.value.some(c => c.nom === newRow.value.client_nom)) {
        if (clients.value.length > 0) {
          newRow.value.client_nom = clients.value[0].nom
        }
      }

      const fpacksForClient = fpacks.value.filter(f => {
        const client = clients.value.find(c => c.id === f.client)
        return client && client.nom === newRow.value.client_nom
      })
      if (!newRow.value.fpack_nom || !fpacksForClient.some(f => f.nom === newRow.value.fpack_nom)) {
        if (fpacksForClient.length > 0) {
          newRow.value.fpack_nom = fpacksForClient[0].nom
        } else {
          newRow.value.fpack_nom = ''
        }
      }
    }
  }
})

async function onDuplicate(row: any) {
  await duplicateRow(row)
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
  }
}

// Fonction pour obtenir le label d'une colonne
function getColumnLabel(col: string): string {
  const mappings: Record<string, Record<string, string>> = {
    produits: { fournisseur_id: 'fournisseur' },
    prix: { client_id: 'client', produit_id: 'produit' },
    prix_robot: { id: 'robot' },
    projets: { fpack_id: 'fpack' }
  }
  
  return mappings[props.tableName]?.[col] || col
}

// Fonction pour obtenir l'ID d'édition selon le type de table
function getEditingId(row: any): number | null {
  if (props.tableName === 'prix') {
    return editingId.value === Number(`${row.produit_id}${row.client_id}`) ? editingId.value : null
  }
  return editingId.value === row.id ? editingId.value : null
}

// Fonction pour démarrer l'édition selon le type de table
function handleStartEdit(row: any) {
  if (props.tableName === 'prix') {
    startEditPrix({ produit_id: row.produit_id, client_id: row.client_id })
  } else {
    startEdit(row.id)
  }
}

// Fonction pour valider l'édition selon le type de table
function handleValidateEdit(row: any) {
  if (props.tableName === 'prix') {
    validateEdit({ produit_id: row.produit_id, client_id: row.client_id })
  } else {
    validateEdit(row.id)
  }
}

// Fonction pour supprimer selon le type de table
function handleDeleteRow(row: any) {
  if (props.tableName === 'prix') {
    deleteRow({ produit_id: row.produit_id, client_id: row.client_id })
  } else {
    deleteRow(row.id)
  }
}
</script>

<template>
  <div class="table-container">
    <table class="table-head">
      <thead>
        <tr>
          <th v-for="col in orderedColumns" :key="col">
            <div style="display: flex; align-items: center; gap: 0.3rem;">
              <span>{{ getColumnLabel(col) }}</span>
              <Filters
                :column="col"
                :values="[...columnValues[col] || []]"
                :selected="filters[col] || new Set([...columnValues[col] || []])"
                :labels="valueLabels[col]"
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
          <tr v-if="ajouter">
            <td v-for="col in orderedColumns" :key="col">
              <!-- Gestion des selects pour foreign keys -->
              <template v-if="col === 'fournisseur_id' && props.tableName === 'produits'">
                <SearchSelect v-model="newRow.fournisseur_nom">
                  <option v-for="f in fournisseurs" :key="f.id" :value="f.nom">{{ f.nom }}</option>
                </SearchSelect>
              </template>
              
              <template v-else-if="col === 'client' && ['fpacks', 'projets', 'robots'].includes(props.tableName)">
                <SearchSelect v-model="newRow.client_nom" :disabled="props.tableName === 'projets' && !!newRow.fpack_nom">
                  <option v-for="c in clients" :key="c.id" :value="c.nom">{{ c.nom }}</option>
                </SearchSelect>
              </template>

              <template v-else-if="col === 'fpack_id' && props.tableName === 'projets'">
                <SearchSelect v-model="newRow.fpack_nom" :disabled="!!newRow.client_nom && !newRow.fpack_nom" :key="newRow.client_nom">
                  <option v-for="f in filteredFpacks" :key="f.id" :value="f.nom">{{ f.nom }}</option>
                </SearchSelect>
              </template>

              <template v-else-if="col === 'produit_id' && props.tableName === 'prix'">
                <SearchSelect v-model="newRow.produit_nom">
                  <option v-for="p in produits" :key="p.id" :value="p.nom">{{ p.nom }}</option>
                </SearchSelect>
              </template>

              <template v-else-if="col === 'client_id' && props.tableName === 'prix'">
                <SearchSelect v-model="newRow.client_nom">
                  <option v-for="c in clients" :key="c.id" :value="c.nom">{{ c.nom }}</option>
                </SearchSelect>
              </template>

              <template v-else-if="col === 'reference' && props.tableName === 'prix_robot'">
                <SearchSelect v-model="newRow.robot_reference">
                  <option v-for="r in robots" :key="r.id" :value="r.reference">{{ r.reference }}</option>
                </SearchSelect>
              </template>

              <template v-else-if="col === 'id' && props.tableName === 'prix_robot'">
                <SearchSelect v-model="newRow.robot_nom">
                  <option v-for="r in robots" :key="r.id" :value="r.nom">{{ r.nom }}</option>
                </SearchSelect>
              </template>

              <template v-else-if="col !== 'id'">
                <AutoComplete v-model="newRow[col]" @keyup.enter="validateAdd" :suggestions="[...columnValues[col] || []]" />
              </template>
            </td>
            <td class="actions">
              <button @click="validateAdd">✅</button>
              <button @click="cancelAdd">❌</button>
            </td>
          </tr>

          <!-- Lignes de données -->
          <tr v-for="row in filteredAndSortedRows" :key="row.id">
            <td v-for="col in orderedColumns" :key="col">
              <!-- Mode édition -->
              <template v-if="getEditingId(row)">
                <!-- Selects pour foreign keys en mode édition -->
                <template v-if="col === 'fournisseur_id' && props.tableName === 'produits'">
                  <SearchSelect v-model="editRow.fournisseur_nom" @keyup.enter="handleValidateEdit(row)">
                    <option v-for="f in fournisseurs" :key="f.id" :value="f.nom">{{ f.nom }}</option>
                  </SearchSelect>
                </template>
                
                <template v-else-if="col === 'client' && ['fpacks', 'projets', 'robots'].includes(props.tableName)">
                  <SearchSelect v-model="editRow.client_nom" @keyup.enter="handleValidateEdit(row)">
                    <option v-for="c in clients" :key="c.id" :value="c.nom">{{ c.nom }}</option>
                  </SearchSelect>
                </template>

                <template v-else-if="col === 'fpack_id' && props.tableName === 'projets'">
                  <SearchSelect v-model="editRow.fpack_nom" @keyup.enter="handleValidateEdit(row)">
                    <option v-for="f in filteredFpacksEdit" :key="f.id" :value="f.nom">{{ f.nom }}</option>
                  </SearchSelect>
                </template>

                <template v-else-if="col === 'client_id' && props.tableName === 'prix'">
                  <SearchSelect v-model="editRow.client_nom" @keyup.enter="handleValidateEdit(row)">
                    <option v-for="c in clients" :key="c.id" :value="c.nom">{{ c.nom }}</option>
                  </SearchSelect>
                </template>

                <template v-else-if="col === 'produit_id' && props.tableName === 'prix'">
                  <SearchSelect v-model="editRow.produit_nom" @keyup.enter="handleValidateEdit(row)">
                    <option v-for="p in produits" :key="p.id" :value="p.nom">{{ p.nom }}</option>
                  </SearchSelect>
                </template>

                <template v-else-if="col === 'reference' && props.tableName === 'prix_robot'">
                  <SearchSelect v-model="editRow.robot_reference">
                    <option v-for="r in robots" :key="r.id" :value="r.reference">{{ r.reference }}</option>
                  </SearchSelect>
                </template>

                <template v-else-if="col === 'id' && props.tableName === 'prix_robot'">
                  <SearchSelect v-model="editRow.robot_nom" @keyup.enter="handleValidateEdit(row)">
                    <option v-for="r in robots" :key="r.id" :value="r.nom">{{ r.nom }}</option>
                  </SearchSelect>
                </template>

                <template v-else-if="col !== 'id'">
                  <AutoComplete v-model="editRow[col]" @keyup.enter="handleValidateEdit(row)" :suggestions="[...columnValues[col] || []]" />
                </template>
              </template>

              <!-- Mode lecture -->
              <template v-else>
                <template v-if="col === 'fournisseur_id' && props.tableName === 'produits'">
                  {{ fournisseurs.find(f => f.id === row.fournisseur_id)?.nom || row.fournisseur_id }}
                </template>
                
                <template v-else-if="col === 'client' && ['fpacks', 'projets', 'robots'].includes(props.tableName)">
                  {{ clients.find(c => c.id === row.client)?.nom || row.client }}
                </template>

                <template v-else-if="col === 'fpack_id' && props.tableName === 'projets'">
                  {{ fpacks.find(f => f.id === row.fpack_id)?.nom || row.fpack_id }}
                </template>

                <template v-else-if="col === 'produit_id' && props.tableName === 'prix'">
                  {{ produits.find(p => p.id === row.produit_id)?.nom || row.produit_id }}
                </template>

                <template v-else-if="col === 'client_id' && props.tableName === 'prix'">
                  {{ clients.find(c => c.id === row.client_id)?.nom || row.client_id }}
                </template>

                <template v-else-if="col === 'id' && props.tableName === 'prix_robot'">
                  {{ robots.find(r => r.id === row.id)?.nom || row.id }}
                </template>

                <template v-else-if="col === 'nom' && props.tableName === 'projets'">
                  <span>{{ row.complet ? '✔️' : '⏳' }}</span> | {{ row.nom }}
                </template>

                <template v-else>
                  {{ row[col] }}
                </template>
              </template>
            </td>

            <!-- Actions -->
            <td class="actions">
              <template v-if="getEditingId(row)">
                <button @click="handleValidateEdit(row)">✅</button>
                <button @click="cancelEdit">❌</button>
              </template>
              <template v-else>
                <button title="Éditer" @click="handleStartEdit(row)">✏️</button>
                <button title="Supprimer" @click="handleDeleteRow(row)">🗑️</button>
                
                <!-- Actions spécifiques par table -->
                <button v-if="tableConfig.hasRemplir && tableConfig.remplirType === 'equipement'" 
                        title="Remplir" @click="remplirEquipement(row)">🗂️</button>
                
                <button v-if="tableConfig.hasRemplir && tableConfig.remplirType === 'fpack'" 
                        title="Remplir" @click="remplirFPack(row)">🛠️</button>
                
                <button v-if="tableConfig.hasDuplicate" 
                        title="Dupliquer" @click="onDuplicate(row)">🔁</button>
                
                <button v-if="tableConfig.hasExport" 
                        title="Exporter" @click="ExportRow(row)">📤</button>
                
                <button v-if="tableConfig.hasRemplir && tableConfig.remplirType === 'projet'" 
                        title="Completer" @click="remplirProjet(row)">📝</button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.table-container {
  width: 100%;
  background: #f7f7f7;
}

.table-head {
  width: 90%;
  margin-top: 3%;
  margin-left: 2%;
  min-width: 80%;
  border-collapse: separate;
  border-spacing: 0;
  background: white;
  font-family: inherit;
  border-radius: 1.5%;
  table-layout: fixed;
}

.table-body-scroll {
  width: 90%;
  margin-left: 2%;
  max-height: 40vh;
  overflow-y: auto;
  background: white;
  scrollbar-width: thin;
  scrollbar-color: #b3b3b3 #f3f4f6;
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
  gap: 0.6rem;
  align-items: center;
}

.actions button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-size: 1.2rem;
  color: #222;
}

.actions button:hover {
  color: #2563eb;
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
  width: 100%;
  min-width: 60px;
  max-width: 200px;
}
input:focus, select:focus {
  border: 1.5px solid #2563eb;
  background: #fff;
}
</style>