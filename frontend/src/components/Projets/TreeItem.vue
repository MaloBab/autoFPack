<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  density: {
    type: String,
    default: 'normal'
  }
})

const emit = defineEmits([
  'toggle-expand',
  'edit',
  'delete',
  'create-subproject',
  'edit-subproject',
  'delete-subproject',
  'associate-fpack',
  'remove-fpack',
  'complete-fpack'
])

const showActions = ref(false)
const actionsDropdown = ref(null)

const hasChildren = computed(() => {
  if (props.item.type === 'project') {
    return props.item.data.sous_projets && props.item.data.sous_projets.length > 0
  }
  if (props.item.type === 'subproject') {
    return props.item.data.fpacks && Array.isArray(props.item.data.fpacks) && props.item.data.fpacks.length > 0
  }
  return false
})

const itemTitle = computed(() => {
  switch (props.item.type) {
    case 'project':
      return props.item.data.projet
    case 'subproject':
      return props.item.data.nom
    case 'fpack':
      return props.item.data.FPack_number || 'FPack sans numéro'
    default:
      return ''
  }
})

const itemSubtitle = computed(() => {
  switch (props.item.type) {
    case 'project':
      return `${props.item.data.sous_projets.length} sous-projets`
    case 'subproject':
      return `${props.item.data.nb_selections || 0}/${props.item.data.nb_groupes_attendus || 0} sélections`
    case 'fpack':
      return props.item.data.fpack_nom || ''
    default:
      return ''
  }
})

const progressValue = computed(() => {
  if (props.item.type === 'project') {
    const sousProjects = props.item.data.sous_projets
    if (!sousProjects || !sousProjects.length) return 0
    let totalProgress = 0
    
    sousProjects.forEach(sousProject => {
      if (sousProject.complet) {
        totalProgress += 100
      } else {
        const total = sousProject.nb_groupes_attendus || 1
        const current = sousProject.nb_selections || 0
        const subProgress = Math.round((current / total) * 100)
        totalProgress += Math.min(subProgress, 100)
      }
    })
    
    return Math.round(totalProgress / sousProjects.length)
  }
  
  if (props.item.type === 'subproject') {
    const total = props.item.data.nb_groupes_attendus || 1
    const current = props.item.data.nb_selections || 0
    return Math.min(Math.round((current / total) * 100), 100)
  }

  if (props.item.type === 'fpack') {
    const total = props.item.data.nb_groupes_attendus || 1
    const current = props.item.data.nb_selections || 0
    return Math.min(Math.round((current / total) * 100), 100)
  }
  
  return 0
})

const progressClass = computed(() => {
  const value = progressValue.value
  if (value === 100) return 'complete'
  if (value >= 75) return 'high'
  if (value >= 50) return 'medium'
  if (value >= 25) return 'low'
  return 'none'
})

const isComplete = computed(() => {
  if (props.item.type === 'project') {
    const sousProjects = props.item.data.sous_projets
    return sousProjects.length > 0 && sousProjects.every(sp => sp.complet)
  }
  if (props.item.type === 'subproject') {
    return props.item.data.complet
  }
  if (props.item.type === 'fpack') {
    return props.item.data.complet
  }
  return false
})

const isInProgress = computed(() => {
  if (props.item.type === 'project') {
    const sousProjects = props.item.data.sous_projets
    return sousProjects.some(sp => sp.complet) && !sousProjects.every(sp => sp.complet)
  }
  if (props.item.type === 'subproject') {
    return (props.item.data.fpacks && props.item.data.fpacks.length > 0) && !props.item.data.complet
  }
  if (props.item.type === 'fpack') {
    return (props.item.data.nb_selections || 0) > 0 && !props.item.data.complet
  }
  return false
})

const statusClass = computed(() => {
  if (isComplete.value) return 'complete'
  if (isInProgress.value) return 'in-progress'
  return 'pending'
})

const handleItemClick = () => {
  if (hasChildren.value) {
    emit('toggle-expand', props.item.uniqueId)
  }
}

const toggleActions = () => {
  showActions.value = !showActions.value
}

const handleEdit = () => {
  showActions.value = false
  if (props.item.type === 'project') {
    emit('edit', props.item.data)
  } else if (props.item.type === 'subproject') {
    emit('edit-subproject', props.item.data)
  }
}

const handleDelete = () => {
  showActions.value = false
  if (props.item.type === 'project') {
    emit('delete', props.item.data.id)
  } else if (props.item.type === 'subproject') {
    emit('delete-subproject', props.item.data.id)
  }
}

const handleCreateSubproject = () => {
  showActions.value = false
  emit('create-subproject', props.item.data)
}

const handleAssociateFpack = () => {
  showActions.value = false
  emit('associate-fpack', props.item.data)
}

const handleRemoveFpack = () => {
  showActions.value = false
  emit('remove-fpack', props.item.data.id) 
}

const handleCompleteFpack = () => {
  showActions.value = false
  console.log('-- Completing FPack:', props.item.data.id, 'for Sous-Projet:', props.item.data.sous_projet_id)
  emit('complete-fpack', props.item.data.id) 
}

const closeActions = (event) => {
  if (actionsDropdown.value && !actionsDropdown.value.contains(event.target)) {
    showActions.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', closeActions)
})

onUnmounted(() => {
  document.removeEventListener('click', closeActions)
})
</script>

<template>
  <div 
    :class="[
      'tree-item',
      `tree-item--${item.type}`,
      `tree-item--level-${item.level}`,
      `tree-item--${density}`,
      {
        'tree-item--expanded': item.expanded,
        'tree-item--has-children': hasChildren,
        'tree-item--complete': isComplete,
        'tree-item--in-progress': isInProgress
      }
    ]"
  >
    <div class="tree-line" v-if="item.level > 0"></div>
    <div class="tree-content">
      <div class="tree-indent" :style="`width: ${item.level * 24}px`">
        <button 
          v-if="hasChildren"
          @click="$emit('toggle-expand', item.uniqueId)"
          class="expand-button"
          :class="[{ expanded: item.expanded }, item.type]"
        >
        </button>
      </div>

      <div class="item-icon">
        <div v-if="item.type === 'project'" class="project-icon">
          <span class="icon-letter">{{ item.data.projet.charAt(0).toUpperCase() }}</span>
        </div>

        <div v-else-if="item.type === 'subproject'" class="subproject-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2">
                <circle cx="12" cy="6" r="2" fill="#e0f2fe" stroke="#3b82f6"/>
                <circle cx="6" cy="18" r="2" fill="#e0f2fe" stroke="#3b82f6"/>
                <circle cx="18" cy="18" r="2" fill="#e0f2fe" stroke="#3b82f6"/>
                <line x1="12" y1="8" x2="6" y2="16" stroke="#3b82f6"/>
                <line x1="12" y1="8" x2="18" y2="16" stroke="#3b82f6"/>
            </svg>
        </div>
    <div v-else-if="item.type === 'fpack'" class="fpack-icon">
      <svg viewBox="0 0 60 46" fill="none" stroke="#064e3b" stroke-width="2">
        <circle cx="32" cy="8" r="4.5" fill="#e0f2fe" stroke="#064e3b"/>
        <circle cx="16" cy="24" r="4.5" fill="#e0f2fe" stroke="#064e3b"/>
        <circle cx="48" cy="24" r="4.5" fill="#e0f2fe" stroke="#064e3b"/>
        <circle cx="8" cy="40" r="4.5" fill="#e0f2fe" stroke="#064e3b"/>
        <circle cx="24" cy="40" r="4.5" fill="#e0f2fe" stroke="#064e3b"/>
        <circle cx="40" cy="40" r="4.5" fill="#e0f2fe" stroke="#064e3b"/>
        <circle cx="56" cy="40" r="4.5" fill="#e0f2fe" stroke="#064e3b"/>
        <line x1="32" y1="12" x2="16" y2="24" stroke="#064e3b"/>
        <line x1="32" y1="12" x2="48" y2="24" stroke="#064e3b"/>
        <line x1="16" y1="28" x2="8" y2="40" stroke="#064e3b"/>
        <line x1="16" y1="28" x2="24" y2="40" stroke="#064e3b"/>
        <line x1="48" y1="28" x2="40" y2="40" stroke="#064e3b"/>
        <line x1="48" y1="28" x2="56" y2="40" stroke="#064e3b"/>
      </svg>
    </div>
      </div>

      <div class="item-info" @click="handleItemClick">
        <div class="primary-info">
          <h3 class="item-title">{{ itemTitle }}</h3>
          <p v-if="itemSubtitle" class="item-subtitle">{{ itemSubtitle }}</p>
        </div>

        <div class="secondary-info">
          <div class="item-badges">
            <span v-if="item.type === 'project'" class="badge badge-client">
              <svg class="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              {{ item.data.client_nom }}
            </span>

            <span v-if="item.type === 'project'" class="badge badge-count">
              <svg class="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M3 3h18v18H3zM9 9h6v6H9z"/>
              </svg>
              {{ item.data.sous_projets.length }} sous-projets
            </span>

            <span v-if="item.type === 'subproject'" class="badge badge-progress">
              <svg class="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
              </svg>
              {{ item.data.nb_selections || 0 }}/{{ item.data.nb_groupes_attendus || 0 }}
            </span>

            <span v-if="item.type === 'subproject' && item.data.fpacks" class="badge badge-count">
              <svg class="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
              </svg>
              {{ item.data.fpacks.length }} FPacks
            </span>

            <span v-if="item.type === 'fpack' && item.data.FPack_number" class="badge badge-number">
              # {{ item.data.FPack_number }}
            </span>

            <span v-if="item.type === 'fpack' && item.data.Robot_Location_Code" class="badge badge-location">
              <svg class="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                <circle cx="12" cy="10" r="3"/>
              </svg>
              {{ item.data.Robot_Location_Code }}
            </span>

            <span v-if="item.type === 'fpack'" class="badge badge-contractor">
              <svg class="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              {{ item.data.contractor }}
            </span>

            <span v-if="item.type === 'fpack'" class="badge badge-delivery-time">
              <svg class="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12,6 12,12 16,14"/>
              </svg>
              {{ item.data.required_delivery_time }}
            </span>

            <span v-if="item.type === 'fpack'" class="badge badge-delivery-site">
              <svg class="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                <polyline points="9,22 9,12 15,12 15,22"/>
              </svg>
              {{ item.data.delivery_site }}
            </span>

            <span v-if="item.type === 'fpack'" class="badge badge-tracking">
              <svg class="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M9 12l2 2 4-4"/>
                <path d="M21 12c.552 0 1-.448 1-1V5c0-.552-.448-1-1-1H3c-.552 0-1 .448-1 1v6c0 .552.448 1 1 1"/>
                <path d="M3 12v7c0 .552.448 1 1 1h16c.552 0 1-.448 1-1v-7"/>
              </svg>
              {{ item.data.tracking }}
            </span>

            <span v-if="item.type === 'fpack'" class="badge badge-progress">
              <svg class="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
              </svg>
              {{ item.data.nb_selections || 0 }}/{{ item.data.nb_groupes_attendus || 0 }}
            </span>
          </div>

          <div v-if="item.type !== 'fpack' || (item.type === 'fpack' && (item.data.nb_groupes_attendus > 0))" class="progress-indicator">
            <div class="progress-ring" :class="progressClass">
              <svg viewBox="0 0 36 36">
                <path 
                  class="ring-bg"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path 
                  class="ring-progress"
                  :style="`stroke-dasharray: ${progressValue}, 100`"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <span class="progress-text">{{ progressValue }}%</span>
            </div>
          </div>
        </div>
      </div>

      <div class="item-actions" @click.stop>
        <div class="actions-dropdown" ref="actionsDropdown">
          <button 
            @click="toggleActions"
            class="actions-trigger"
            :class="{ active: showActions }"
          >
           ⋮
          </button>

          <Transition name="actions-slide">
            <div v-if="showActions" class="actions-menu">
              <template v-if="item.type === 'project'">
                <button @click="handleEdit" class="action-item action-edit">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                  <span>Modifier</span>
                </button>
                
                <button @click="handleCreateSubproject" class="action-item action-add">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <line x1="12" y1="5" x2="12" y2="19"/>
                    <line x1="5" y1="12" x2="19" y2="12"/>
                  </svg>
                  <span>Ajouter sous-projet</span>
                </button>
                
                <div class="action-divider"></div>
                
                <button @click="handleDelete" class="action-item action-delete">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <polyline points="3,6 5,6 21,6"/>
                    <path d="M19,6v14a2,2 0 0,1 -2,2H7a2,2 0 0,1 -2,-2V6m3,0V4a2,2 0 0,1 2,-2h4a2,2 0 0,1 2,2v2"/>
                  </svg>
                  <span>Supprimer</span>
                </button>
              </template>

              <template v-else-if="item.type === 'subproject'">
                <button @click="handleEdit" class="action-item action-edit">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                  <span>Modifier</span>
                </button>
                
                <button @click="handleAssociateFpack" class="action-item action-associate">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                  </svg>
                  <span>Associer FPack</span>
                </button>
                
                <div class="action-divider"></div>
                
                <button @click="handleDelete" class="action-item action-delete">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <polyline points="3,6 5,6 21,6"/>
                    <path d="M19,6v14a2,2 0 0,1 -2,2H7a2,2 0 0,1 -2,-2V6m3,0V4a2,2 0 0,1 2,-2h4a2,2 0 0,1 2,2v2"/>
                  </svg>
                  <span>Supprimer</span>
                </button>
              </template>

              <template v-else-if="item.type === 'fpack'">
                <button @click="handleCompleteFpack" class="action-item action-complete">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91-6.91a6 6 0 0 1 7.94-7.94l3.77 3.77z"/>
                  </svg>
                  <span>Remplir FPack</span>
                </button>
                
                <button @click="handleRemoveFpack" class="action-item action-remove">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                  <span>Retirer FPack</span>
                </button>
              </template>
            </div>
          </Transition>
        </div>
      </div>

      <div class="status-indicator">
        <div :class="['status-dot', statusClass]">
          <svg v-if="isComplete" class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <polyline points="20,6 9,17 4,12"/>
          </svg>
          <svg v-else-if="isInProgress" class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 6v6l4 2"/>
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tree-item {
  position: relative;
  border-bottom: 1px solid #d5ddd7;
  transition: all 0.2s ease;
}

.tree-item:hover {
  background: #d5d8de;
}

.tree-item--complete {
  background: rgba(16, 185, 129, 0.02);
}

.tree-item--in-progress {
  background: rgba(14, 165, 233, 0.02);
}

.tree-item--compact .tree-content {
  min-height: 60px;
  padding: 8px 16px;
}

.tree-item--normal .tree-content {
  min-height: 80px;
  padding: 12px 20px;
}

.tree-item--comfortable .tree-content {
  min-height: 100px;
  padding: 16px 24px;
}

.tree-line {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(to bottom, #d1d7df, #b8c1cd);
}

.tree-item--level-1 .tree-line {
  left: 24px;
  background: linear-gradient(to bottom, #b6bfca, #8290a2);
}

.tree-item--level-2 .tree-line {
  left: 48px;
  background: linear-gradient(to bottom, #8390a3, #526072);
}

.tree-content {
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
}

.tree-indent {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.expand-button {
  width: 24px;
  height: 24px;
  border: none;
  background: #dee8f1;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.expand-button:hover {
  transform: scale(1.1);
}

.expand-button.project:hover {
  background: linear-gradient(135deg, #7c66ea, #d72fe0);
}
.expand-button.subproject:hover {
  background: linear-gradient(135deg, #3be3f6, #5ca4f6);
}

.item-icon {
  flex-shrink: 0;
}

.project-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #7c66ea, #d72fe0);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 1.2rem;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.tree-item--compact .project-icon {
  width: 32px;
  height: 32px;
  font-size: 1rem;
}

.tree-item--comfortable .project-icon {
  width: 48px;
  height: 48px;
  font-size: 1.4rem;
}

.subproject-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #3be3f6, #5ca4f6);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 3px 10px rgba(14, 165, 233, 0.3);
}

.tree-item--compact .subproject-icon {
  width: 28px;
  height: 28px;
}

.tree-item--comfortable .subproject-icon {
  width: 40px;
  height: 40px;
}

.subproject-icon svg {
  width: 18px;
  height: 18px;
}

.fpack-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #10b981, #34d399);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.tree-item--compact .fpack-icon {
  width: 24px;
  height: 24px;
}

.tree-item--comfortable .fpack-icon {
  width: 36px;
  height: 36px;
}

.fpack-icon svg {
  width: 16px;
  height: 16px;
}

.item-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  min-width: 0;
}

.primary-info {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 4px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-item--compact .item-title {
  font-size: 0.95rem;
  margin-bottom: 2px;
}

.tree-item--comfortable .item-title {
  font-size: 1.25rem;
  margin-bottom: 6px;
}

.item-subtitle {
  font-size: 0.875rem;
  color: #64748b;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-item--compact .item-subtitle {
  font-size: 0.8rem;
}

.tree-item--comfortable .item-subtitle {
  font-size: 0.95rem;
}

.secondary-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.item-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
}

.badge-icon {
  width: 12px;
  height: 12px;
}

.badge-client {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.badge-count {
  background: rgba(102, 126, 234, 0.1);
  color: #5145e2;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.badge-progress {
  background: rgba(14, 165, 233, 0.1);
  color: #0369a1;
  border: 1px solid rgba(14, 165, 233, 0.2);
}

.badge-number {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.badge-location {
  background: rgba(139, 69, 19, 0.1);
  color: #92400e;
  border: 1px solid rgba(139, 69, 19, 0.2);
}

.badge-contractor {
  background: rgba(168, 85, 247, 0.1);
  color: #7c3aed;
  border: 1px solid rgba(168, 85, 247, 0.2);
}

.badge-delivery-time {
  background: rgba(245, 11, 11, 0.1);
  color: #d90606;
  border: 1px solid rgba(245, 11, 11, 0.2);
}

.badge-delivery-site {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.badge-tracking {
  background: rgba(99, 102, 241, 0.1);
  color: #4f46e5;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.progress-indicator {
  position: relative;
}

.progress-ring {
  width: 40px;
  height: 40px;
  position: relative;
}

.tree-item--compact .progress-ring {
  width: 32px;
  height: 32px;
}

.tree-item--comfortable .progress-ring {
  width: 48px;
  height: 48px;
}

.progress-ring svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-bg {
  fill: none;
  stroke: #e2e8f0;
  stroke-width: 3;
}

.ring-progress {
  fill: none;
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray 0.6s ease;
}

.progress-ring.complete .ring-progress {
  stroke: #10b981;
}

.progress-ring.high .ring-progress {
  stroke: #0ea5e9;
}

.progress-ring.medium .ring-progress {
  stroke: #f59e0b;
}

.progress-ring.low .ring-progress {
  stroke: #ef4444;
}

.progress-ring.none .ring-progress {
  stroke: #9ca3af;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.7rem;
  font-weight: 600;
  color: #374151;
}

.tree-item--compact .progress-text {
  font-size: 0.6rem;
}

.tree-item--comfortable .progress-text {
  font-size: 0.8rem;
}

.item-actions {
  flex-shrink: 0;
  position: relative;
}

.actions-trigger {
  width: 36px;
  height: 36px;
  border: none;
  background: #f8fafc;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  transition: all 0.2s ease;
  border: 1px solid #e2e8f0;
}

.actions-trigger:hover,
.actions-trigger.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
  transform: scale(1.05);
}

.actions-trigger svg {
  width: 16px;
  height: 16px;
}

.actions-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  border: 1px solid #e2e8f0;
  overflow: hidden;
  z-index: 10;
  min-width: 180px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.875rem;
  color: #374151;
}

.action-item:hover {
  background: #f8fafc;
}

.action-item svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.action-edit:hover {
  background: rgba(14, 165, 233, 0.1);
  color: #0ea5e9;
}

.action-add:hover {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.action-associate:hover {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.action-complete:hover {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.action-remove:hover,
.action-delete:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.action-divider {
  height: 1px;
  background: #e2e8f0;
  margin: 4px 0;
}

.status-indicator {
  flex-shrink: 0;
}

.status-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.status-dot.complete {
  background: #10b981;
  color: white;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
}

.status-dot.in-progress {
  background: #0ea5e9;
  color: white;
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.2);
}

.status-dot.pending {
  background: #e2e8f0;
  color: #64748b;
}

.status-icon {
  width: 12px;
  height: 12px;
  stroke-width: 2.5;
}

.actions-slide-enter-active,
.actions-slide-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.actions-slide-enter-from,
.actions-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.95);
}
</style>