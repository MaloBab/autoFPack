<script setup lang="ts">
import { defineEmits, defineProps } from 'vue'

const props = defineProps<{
  row: any
  isEditing: boolean
  tableConfig: any
}>()

const emit = defineEmits([
  'edit',
  'delete', 
  'validate-edit',
  'cancel-edit',
  'duplicate',
  'export',
  'remplir-equipement',
  'remplir-fpack',
  'remplir-projet'
])
</script>

<template>
  <td class="actions">
    <!-- Mode édition -->
    <template v-if="isEditing">
      <button @click="emit('validate-edit')">✅</button>
      <button @click="emit('cancel-edit')">❌</button>
    </template>
    
    <!-- Mode normal -->
    <template v-else>
      <button title="Éditer" @click="emit('edit')">✏️</button>
      <button title="Supprimer" @click="emit('delete')">🗑️</button>
      
      <!-- Actions spécifiques par table -->
      <button 
        v-if="tableConfig.hasRemplir && tableConfig.remplirType === 'equipement'" 
        title="Remplir" 
        @click="emit('remplir-equipement')"
      >
        🗂️
      </button>
      
      <button 
        v-if="tableConfig.hasRemplir && tableConfig.remplirType === 'fpack'" 
        title="Remplir" 
        @click="emit('remplir-fpack')"
      >
        🛠️
      </button>
      
      <button 
        v-if="tableConfig.hasDuplicate" 
        title="Dupliquer" 
        @click="emit('duplicate')"
      >
        🔁
      </button>
      
      <button 
        v-if="tableConfig.hasExport" 
        title="Exporter" 
        @click="emit('export')"
      >
        📤
      </button>
      
      <button 
        v-if="tableConfig.hasRemplir && tableConfig.remplirType === 'projet'" 
        title="Completer" 
        @click="emit('remplir-projet')"
      >
        📝
      </button>
    </template>
  </td>
</template>

<style scoped>
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

</style>