<script setup>
import { ref, computed, watch } from 'vue'
import CounterAnimation from './CounterAnimation.vue'
import ProjectsTreeView from './ProjectsTreeView.vue'

const props = defineProps({
  projets: {
    type: Array,
    default: () => []
  },
  clients: {
    type: Array,
    default: () => []
  },
  fpacks: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'create-project',
  'edit-project',
  'delete-project',
  'create-subproject',
  'edit-subproject', 
  'delete-subproject',
  'associate-fpack',
  'remove-fpack',
  'complete-fpack'
])

const isFullscreen = ref(false)

const handleDeleteProject = (projectId) => {
  emit('delete-project', projectId)
}

const handleDeleteSubproject = (subprojectId) => {
  emit('delete-subproject', subprojectId)
}

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
}

const handleCompleteFpack = (sousProjetId, fpackId) => {
  emit('complete-fpack', sousProjetId, fpackId)
}
</script>

<template>
  <div class="projects-view" :class="{ 'fullscreen': isFullscreen }">
    <div class="view-header">
      <div class="header-left">
        <h2 class="view-title">Projets</h2>
        <div class="projects-count">
          <CounterAnimation :value="projets.length" />
          <span class="count-label">projets</span>
        </div>
      </div>
      
      <div class="header-actions">
        <button @click="toggleFullscreen" 
                class="fullscreen-btn" 
                :title="isFullscreen ? 'Quitter le plein écran' : 'Plein écran'">
          <span :class="['fullscreen-icon', isFullscreen ? 'minimized' : 'full']">⛶</span>
        </button>
        
        <button @click="$emit('create-project')" class="create-btn">
          <div class="btn-icon">+</div>
          <span>Nouveau Projet</span>
        </button>
      </div>
    </div>

    <div class="content-area">
      <template v-if="loading">
        <div class="loading-state">
          <div class="loading-spinner"></div>
          <p>Chargement des projets...</p>
        </div>
      </template>

      <template v-else-if="projets.length === 0">
        <div class="empty-state">
          <div class="empty-icon">📁</div>
          <h3>Aucun projet</h3>
          <p>Créez votre premier projet pour commencer</p>
          <button @click="$emit('create-project')" class="empty-action-btn">
            Créer un projet
          </button>
        </div>
      </template>

      <template v-else>
        <div class="tree-view-container">
          <ProjectsTreeView
            :projets="projets"
            :clients="clients"
            :fpacks="fpacks"
            :loading="loading"
            @edit-project="$emit('edit-project', $event)"
            @delete-project="handleDeleteProject"
            @create-subproject="$emit('create-subproject', $event)"
            @edit-subproject="$emit('edit-subproject', $event)"
            @delete-subproject="handleDeleteSubproject"
            @associate-fpack="$emit('associate-fpack', $event)"
            @remove-fpack="$emit('remove-fpack', $event)"
            @complete-fpack="handleCompleteFpack"
          />
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.projects-view {
  height: 85%;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 30px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;
  z-index: 1;
}

.projects-view.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  height: 100vh;
  border-radius: 0;
  padding: 20px;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(30px);
  box-shadow: none;
  border: none;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(102, 126, 234, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-title {
  font-size: 2rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  background: linear-gradient(135deg, #161616, #787878);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.projects-count {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(86, 110, 219, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(9, 48, 223, 0.2);
}

.count-label {
  font-size: 0.875rem;
  color: #898989;
  font-weight: 500;
}

.fullscreen-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: #f7f7f7;
  border: 2px solid #646464;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #181818;
  position: relative;
  overflow: hidden;
}

.fullscreen-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.1), transparent);
  transition: left 0.5s;
}

.fullscreen-btn:hover::before {
  left: 100%;
}

.fullscreen-btn:hover {
  background: #383838;
  color: white;
  border-color: #888888;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(62, 62, 62, 0.3);
}

.fullscreen-icon {
  display: inline-block;;
  transition: all 0.3s ease;
  line-height: 1.1;
}

.fullscreen-icon.full {
  font-size: 20px;
  width: 20px;
  height: 20px;
}

.fullscreen-icon.minimized {
  font-size: 28px;
  width: 28px;
  height: 28px;
}

.fullscreen-btn:hover .fullscreen-icon {
  transform: scale(1.1);
}

.create-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #161616, #787878);
  color: white;
  border: none;
  border-radius: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
  position: relative;
  overflow: hidden;
}

.create-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.create-btn:hover::before {
  left: 100%;
}

.create-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(102, 126, 234, 0.4);
}

.btn-icon {
  width: 20px;
  height: 20px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
}

.content-area {
  flex: 1;
  min-height: 0;
  position: relative;
}

.tree-view-container {
  height: 100%;
  border-radius: 16px;
  overflow: hidden;
}

.projects-view.fullscreen .tree-view-container {
  border-radius: 12px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  gap: 16px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e2e8f0;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-state p {
  color: #64748b;
  font-weight: 500;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  text-align: center;
  gap: 16px;
}

.empty-icon {
  font-size: 4rem;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 1.5rem;
  color: #334155;
  margin: 0;
}

.empty-state p {
  color: #64748b;
  margin: 0;
  max-width: 300px;
}

.empty-action-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #3b82f6, #06b6d4);
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 8px;
}

.empty-action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

@keyframes fullscreenEnter {
  from {
    transform: scale(0.95);
    opacity: 0.9;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
.projects-view.fullscreen {
  animation: fullscreenEnter 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}
</style>