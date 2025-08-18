<script setup lang="ts">
import { computed, defineEmits, defineProps } from 'vue'
import SearchSelect from '../Searching/SearchSelect.vue'

const props = defineProps<{
  column: string
  tableName: string
  modelValue: any
  tableData: any
  mode: 'add' | 'edit'
}>()

const emit = defineEmits(['update:modelValue'])

const rowData = computed(() => props.mode === 'add' ? props.tableData.newRow.value : props.tableData.editRow.value)

const options = computed(() => {
  switch (props.column) {
    case 'fournisseur_id':
      return props.tableData.fournisseurs.value
    case 'client':
    case 'client_id':
      return props.tableData.clients.value
    case 'fpack_id':
      if (props.tableName === 'projets') {
        const clientNom = rowData.value.client_nom
        if (clientNom) {
          const client = props.tableData.clients.value.find((c:any) => c.nom === clientNom)
          if (client) {
            return props.tableData.fpacks.value.filter((f:any) => f.client === client.id)
          }
        }
      }
      return props.tableData.fpacks.value
    case 'produit_id':
      return props.tableData.produits.value
    case 'id':
    case 'reference':
      if (props.tableName === 'prix_robot') {
        return props.tableData.robots.value
      }
      return []
    default:
      return []
  }
})

const modelKey = computed(() => {
  const keyMap = {
    fournisseur_id: 'fournisseur_nom',
    client: 'client_nom',
    client_id: 'client_nom',
    fpack_id: 'fpack_nom',
    produit_id: 'produit_nom',
    id: props.tableName === 'prix_robot' ? 'robot_nom' : 'id',
    reference: props.tableName === 'prix_robot' ? 'robot_reference' : 'reference'
  } as any
  return keyMap[props.column] || props.column
})

const optionValue = computed(() => {
  if (props.column === 'reference' && props.tableName === 'prix_robot') {
    return 'reference'
  }
  return 'nom'
})

const isDisabled = computed(() => {
  if (props.tableName === 'projets') {
    if (props.column === 'client' && !!rowData.value.fpack_nom) {
      return true
    }
    if (props.column === 'fpack_id' && !!rowData.value.client_nom && !rowData.value.fpack_nom) {
      return true
    }
  }
  return false
})
</script>

<template>
  <SearchSelect 
    v-model="rowData[modelKey]" 
    :disabled="isDisabled"
    :key="tableName === 'projets' && column === 'fpack_id' ? rowData.client_nom : undefined"
  >
    <option v-for="option in options" :key="option.id" :value="option[optionValue]">
      {{ option[optionValue] }}
    </option>
  </SearchSelect>
</template>