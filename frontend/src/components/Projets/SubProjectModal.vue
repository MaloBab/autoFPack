<script setup>
import { ref, computed, watch, onMounted, nextTick, onUnmounted } from 'vue'

const props = defineProps({
  show: Boolean,
  subproject: Object,
  project: Object,
  loading: Boolean
})

const emit = defineEmits(['close', 'save'])

const formData = ref({
  nom: '',
  id_global: ''
})

const errors = ref({
  nom: ''
})

const subprojectNameInput = ref(null)

const isFormValid = computed(() => {
  return formData.value.nom.trim() && !Object.values(errors.value).some(error => error)
})

watch(() => props.show, (newValue) => {
  if (newValue) {
    resetForm()
    if (props.subproject) {
      formData.value = {
        nom: props.subproject.nom || '',
        id_global: props.subproject.id_global || (props.project?.id || '')
      }
    } else if (props.project) {
      formData.value.id_global = props.project.id
    }
    
    nextTick(() => {
      if (subprojectNameInput.value) {
        subprojectNameInput.value.focus()
      }
    })
  }
})

const resetForm = () => {
  formData.value = {
    nom: '',
    id_global: ''
  }
  errors.value = {
    nom: ''
  }
}


const handleSubmit = () => {
  emit('save', { ...formData.value })
}

const handleOverlayClick = (e) => {
  if (e.target === e.currentTarget) {
    emit('close')
  }
}
const handleKeydown = (e) => {
  if (e.key === 'Escape' && props.show) {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  if (props.show) {
    document.body.style.overflow = 'hidden'
  }
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal" appear>
      <div v-if="show" class="modal-overlay" @click="handleOverlayClick">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <div class="header-content">
              <div class="modal-icon">
                <div class="icon-wrapper">
                  {{ subproject ? '✏️' : '📋' }}
                </div>
              </div>
              <div class="header-text">
                <h2 class="modal-title">
                  {{ subproject ? 'Modifier le sous-projet' : 'Nouveau sous-projet' }}
                </h2>
                <p class="modal-subtitle">
                  {{ project ? `Pour le projet "${project.projet}"` : 'Organisez votre travail en sous-projets' }}
                </p>
              </div>
            </div>
            <button @click="$emit('close')" class="close-btn">X</button>
          </div>
          <form @submit.prevent="handleSubmit" class="modal-form">
            <div class="form-content">
              <div v-if="project" class="project-context">
                <div class="context-header">
                  <div class="context-icon">🎯</div>
                  <div class="context-info">
                    <h3 class="context-title">{{ project.projet }}</h3>
                  </div>
                  <div class="context-stats">
                    <div class="stat-item">
                      <span class="stat-value">{{ project.sous_projets?.length || 0 }}</span>
                      <span class="stat-label">Sous-projets</span>
                    </div>
                  </div>
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">
                  <span class="label-text">Nom du sous-projet</span>
                </label>
                <div class="input-wrapper">
                  <div class="input-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                      <path d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" stroke="currentColor" stroke-width="1.5"/>
                    </svg>
                  </div>
                  <input
                    ref="subprojectNameInput"
                    v-model="formData.nom"
                    type="text"
                    class="form-input"
                    :class="{ error: errors.nom }"
                    placeholder="Entrez le nom de votre sous-projet..."
                    required
                  >
                </div>
                <div v-if="errors.nom" class="error-message">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                    <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2"/>
                    <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  {{ errors.nom }}
                </div>
              </div>

              <div v-if="subproject" class="info-section">
                <div class="info-header">
                  <h3>Informations du sous-projet</h3>
                </div>
                <div class="info-grid">
                  <div class="info-card" :class="{ complete: subproject.complet, pending: !subproject.complet }">
                    <div class="info-icon">
                      {{ subproject.complet ? '✅' : '⏳' }}
                    </div>
                    <div class="info-content">
                      <div class="info-value">
                        {{ subproject.complet ? 'Terminé' : 'En cours' }}
                      </div>
                      <div class="info-label">Status</div>
                    </div>
                  </div>
                  <div class="info-card">
                    <div class="info-icon">📅</div>
                    <div class="info-content">
                      <div class="info-value">{{ subproject.id || 'Auto' }}</div>
                      <div class="info-label">ID</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button 
                type="button" 
                @click="$emit('close')" 
                class="btn btn-secondary"
                :disabled="loading"
              >
                <span>Annuler</span>
              </button>
              <button 
                type="submit" 
                class="btn btn-primary"
                :disabled="loading || !isFormValid"
              >
                <div v-if="loading" class="btn-spinner">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" opacity="0.25"/>
                    <path d="M12 2a10 10 0 0110 10" stroke="currentColor" stroke-width="4"/>
                  </svg>
                </div>
                <span v-else>
                  {{ subproject ? 'Modifier' : 'Créer' }} le sous-projet
                </span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-container {
  background: white;
  border-radius: 24px;
  width: 100%;
  max-width: 580px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.1);
}

.modal-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 32px;
  position: relative;
  color: white;
}

.header-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.modal-icon {
  flex-shrink: 0;
}

.icon-wrapper {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  backdrop-filter: blur(10px);
}

.header-text {
  flex: 1;
}

.modal-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: white;
}

.modal-subtitle {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
  line-height: 1.5;
}

.close-btn {
  position: absolute;
  top: 24px;
  right: 24px;
  width: 40px;
  height: 40px;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}

.modal-form {
  display: flex;
  flex-direction: column;
  height: calc(100% - 120px);
}

.form-content {
  flex: 1;
  padding: 32px;
  overflow-y: auto;
}

.project-context {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 24px;
  border: 1px solid #e2e8f0;
}

.context-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.context-icon {
  font-size: 24px;
  filter: grayscale(0.2);
}

.context-info {
  flex: 1;
}

.context-title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 4px 0;
}

.context-stats {
  display: flex;
  align-items: center;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: #667eea;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 8px;
  font-weight: 600;
  color: #374151;
}

.label-text {
  font-size: 14px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 16px;
  z-index: 1;
  color: #9ca3af;
  transition: color 0.2s ease;
}

.form-input {
  width: 100%;
  color: #000;
  padding: 16px 16px 16px 48px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 16px;
  background: #f9fafb;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
}

.form-input:focus {
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.form-input:focus + .input-icon {
  color: #667eea;
}

.form-input.error {
  border-color: #ef4444;
  background: #fef2f2;
}

.error-message {
  color: #ef4444;
  font-size: 14px;
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.info-section {
  background: #f8fafc;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
}

.info-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 16px 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.info-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-card:hover {
  border-color: #d1d5db;
  transform: translateY(-1px);
}

.info-card.complete {
  background: rgba(16, 185, 129, 0.05);
  border-color: rgba(16, 185, 129, 0.2);
}

.info-card.pending {
  background: rgba(251, 146, 60, 0.05);
  border-color: rgba(251, 146, 60, 0.2);
}

.info-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.info-content {
  flex: 1;
}

.info-value {
  font-size: 18px;
  font-weight: 700;
  color: #374151;
  margin-bottom: 2px;
}

.info-label {
  font-size: 12px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.modal-footer {
  padding: 24px 32px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn {
  padding: 12px 24px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: none;
  min-width: 120px;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.btn-secondary {
  background: white;
  color: #6b7280;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover:not(:disabled) {
  background: #f3f4f6;
  color: #374151;
  transform: translateY(-1px);
}

.btn-primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  box-shadow: 0 4px 14px rgba(102, 126, 234, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.btn-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95) translateY(20px);
}
</style>