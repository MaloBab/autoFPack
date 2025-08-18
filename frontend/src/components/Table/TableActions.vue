<script setup lang="ts">
import { computed, defineEmits, defineProps, ref, nextTick, onMounted, onUnmounted } from 'vue'

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

const showTooltip = ref<string | null>(null)
const isActionProcessing = ref<string | null>(null)
const showDropdown = ref(false)
const dropdownButton = ref<HTMLButtonElement | null>(null)
const dropdownMenu = ref<HTMLDivElement | null>(null)

const actionButtons = computed(() => {
  if (props.isEditing) {
    return [
      { 
        key: 'validate', 
        icon: '✅', 
        label: 'Valider', 
        variant: 'success',
        action: () => emit('validate-edit'),
        priority: 'primary'
      },
      { 
        key: 'cancel', 
        icon: '❌', 
        label: 'Annuler', 
        variant: 'danger',
        action: () => emit('cancel-edit'),
        priority: 'primary'
      }
    ]
  }
  
  const actions = [
    { 
      key: 'edit', 
      icon: '✏️', 
      label: 'Éditer', 
      variant: 'primary',
      action: () => emit('edit'),
      priority: 'primary'
    },
    { 
      key: 'delete', 
      icon: '🗑️', 
      label: 'Supprimer', 
      variant: 'danger',
      action: () => emit('delete'),
      priority: 'primary'
    }
  ]
  
  if (props.tableConfig.hasRemplir && props.tableConfig.remplirType === 'equipement') {
    actions.push({
      key: 'remplir-equipement',
      icon: '🗂️',
      label: 'Remplir équipement',
      variant: 'info',
      action: () => emit('remplir-equipement'),
      priority: 'secondary'
    })
  }
  
  if (props.tableConfig.hasRemplir && props.tableConfig.remplirType === 'fpack') {
    actions.push({
      key: 'remplir-fpack',
      icon: '🛠️',
      label: 'Remplir FPack',
      variant: 'info',
      action: () => emit('remplir-fpack'),
      priority: 'secondary'
    })
  }
  
  if (props.tableConfig.hasDuplicate) {
    actions.push({
      key: 'duplicate',
      icon: '🔁',
      label: 'Dupliquer',
      variant: 'secondary',
      action: () => emit('duplicate'),
      priority: 'secondary'
    })
  }
  
  if (props.tableConfig.hasExport) {
    actions.push({
      key: 'export',
      icon: '📤',
      label: 'Exporter',
      variant: 'secondary',
      action: () => emit('export'),
      priority: 'secondary'
    })
  }
  
  if (props.tableConfig.hasRemplir && props.tableConfig.remplirType === 'projet') {
    actions.push({
      key: 'remplir-projet',
      icon: '📝',
      label: 'Compléter projet',
      variant: 'info',
      action: () => emit('remplir-projet'),
      priority: 'secondary'
    })
  }
  
  return actions
})

const primaryActions = computed(() => {
  return actionButtons.value.filter(action => action.priority === 'primary')
})

const secondaryActions = computed(() => {
  return actionButtons.value.filter(action => action.priority === 'secondary')
})

async function handleAction(action: any) {
  isActionProcessing.value = action.key
  showDropdown.value = false
  try {
    await new Promise(resolve => setTimeout(resolve, 200))
    action.action()
  } finally {
    isActionProcessing.value = null
  }
}

function showActionTooltip(key: string) {
  showTooltip.value = key
}

function hideActionTooltip() {
  showTooltip.value = null
}

function toggleDropdown() {
  if (showDropdown.value) {
    closeDropdown()
  } else {
    openDropdown()
  }
}

async function openDropdown() {
  if (!dropdownButton.value) return
  
  showDropdown.value = true
  
  await nextTick()
  
  if (dropdownMenu.value && dropdownButton.value) {
    const buttonRect = dropdownButton.value.getBoundingClientRect()
    
    const top = buttonRect.bottom + 4
    const left = buttonRect.left + (buttonRect.width / 2) - (180 / 2) 
    
    dropdownMenu.value.style.position = 'fixed'
    dropdownMenu.value.style.top = `${top}px`
    dropdownMenu.value.style.left = `${left}px`
    dropdownMenu.value.style.zIndex = '9999'
    
    console.log('Button position:', buttonRect)
    console.log('Dropdown position:', { top, left })
  }
}

function closeDropdown() {
  showDropdown.value = false
}

function handleClickOutside(event: Event) {
  if (!dropdownButton.value || !dropdownMenu.value) return
  
  const target = event.target as Node
  if (!dropdownButton.value.contains(target) && !dropdownMenu.value.contains(target)) {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('scroll', closeDropdown)
  window.addEventListener('resize', closeDropdown)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('scroll', closeDropdown)
  window.removeEventListener('resize', closeDropdown)
})
</script>

<template>
  <td class="modern-actions">
    <div class="actions-container" :class="{ editing: props.isEditing }">
      <div class="actions-primary">
        <button
          v-for="action in primaryActions"
          :key="action.key"
          :class="[
            'action-button',
            'primary-action',
            `action-${action.variant}`,
            { 
              'processing': isActionProcessing === action.key,
              'tooltip-visible': showTooltip === action.key
            }
          ]"
          @click="handleAction(action)"
          @mouseenter="showActionTooltip(action.key)"
          @mouseleave="hideActionTooltip"
          :disabled="isActionProcessing !== null"
        >
          <span class="action-icon" :class="{ spinning: isActionProcessing === action.key }">
            <template v-if="isActionProcessing === action.key">⏳</template>
            <template v-else>{{ action.icon }}</template>
          </span>
          
          <div class="action-tooltip" v-if="showTooltip === action.key">
            {{ action.label }}
            <div class="tooltip-arrow"></div>
          </div>
          
          <div class="ripple-effect"></div>
        </button>
        
        <div class="actions-dropdown" v-if="secondaryActions.length > 0">
          <button 
            ref="dropdownButton"
            class="dropdown-toggle"
            @click="toggleDropdown"
            :class="{ active: showDropdown }"
          >
            <span class="dropdown-icon">⋯</span>
          </button>
        </div>
      </div>
      
      <div class="action-status" v-if="props.isEditing">
        <div class="status-dot editing"></div>
        <span class="status-text">Édition</span>
      </div>
    </div>
    
    <Teleport to="body">
      <div 
        ref="dropdownMenu"
        class="dropdown-menu" 
        :class="{ show: showDropdown }"
        v-if="showDropdown && secondaryActions.length > 0"
      >
        <button
          v-for="action in secondaryActions"
          :key="action.key"
          class="dropdown-item"
          :class="`item-${action.variant}`"
          @click="handleAction(action)"
          :disabled="isActionProcessing !== null"
        >
          <span class="item-icon">{{ action.icon }}</span>
          <span class="item-label">{{ action.label }}</span>
        </button>
      </div>
    </Teleport>
  </td>
</template>

<style scoped>
.modern-actions {
  padding: 0.75rem 1rem !important;
  vertical-align: middle;
  position: relative;
  width: 460px;
}

.actions-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-height: 2.5rem;
  transition: all 0.3s ease;
}

.actions-container.editing {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.1), rgba(239, 68, 68, 0.1));
  border-radius: 8px;
  padding: 0.5rem;
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.actions-primary {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  position: relative;
}

.action-button {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  backdrop-filter: blur(10px);
}

.action-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.action-button:active {
  transform: scale(0.95);
}

.action-primary {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: white;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.action-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb, #1e40af);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.4);
}

.action-success {
  background: linear-gradient(135deg, #10b981, #047857);
  color: white;
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3);
}

.action-success:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669, #065f46);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(16, 185, 129, 0.4);
}

.action-danger {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3);
}

.action-danger:hover:not(:disabled) {
  background: linear-gradient(135deg, #dc2626, #b91c1c);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(239, 68, 68, 0.4);
}

.action-icon {
  display: inline-block;
  transition: transform 0.25s ease;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2));
}

.action-icon.spinning {
  animation: spin 1s linear infinite;
}

.actions-dropdown {
  position: relative;
  display: inline-block;
}

.dropdown-toggle {
  background: linear-gradient(135deg, #6b7280, #4b5563);
  border: none;
  color: white;
  width: 2rem;
  height: 2rem;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  font-weight: bold;
  transition: all 0.25s ease;
  box-shadow: 0 2px 4px rgba(107, 114, 128, 0.3);
}

.dropdown-toggle:hover {
  background: linear-gradient(135deg, #4b5563, #374151);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(107, 114, 128, 0.4);
}

.dropdown-toggle.active {
  background: linear-gradient(135deg, #374151, #1f2937);
}

.dropdown-icon {
  line-height: 1;
}

.dropdown-menu {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  z-index: 9999;
  min-width: 180px;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-10px) scale(0.95);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
}

.dropdown-menu.show {
  opacity: 1;
  visibility: visible;
  transform: translateY(0) scale(1);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  transition: all 0.15s ease;
  border-radius: 0;
}

.dropdown-item:first-child {
  border-top-left-radius: 6px;
  border-top-right-radius: 6px;
}

.dropdown-item:last-child {
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 6px;
}

.dropdown-item:hover:not(:disabled) {
  background: #f3f4f6;
  color: #1f2937;
}

.dropdown-item:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.dropdown-item.item-info:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(8, 145, 178, 0.1));
  color: #0891b2;
}

.dropdown-item.item-secondary:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(107, 114, 128, 0.1), rgba(75, 85, 99, 0.1));
  color: #4b5563;
}

.item-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.item-label {
  flex-grow: 1;
}

.action-tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.9);
  color: white;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 1001;
  backdrop-filter: blur(10px);
}

.action-button.tooltip-visible .action-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(-2px);
}

.tooltip-arrow {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 4px solid rgba(0, 0, 0, 0.9);
}

.ripple-effect {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: all 0.3s ease;
  pointer-events: none;
}

.action-button:active .ripple-effect {
  width: 100%;
  height: 100%;
}

.action-status {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.5rem;
  background: rgba(251, 191, 36, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.status-dot.editing {
  background: #f59e0b;
}

.status-text {
  font-size: 0.65rem;
  font-weight: 600;
  color: #92400e;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

</style>