<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  show: Boolean,
  project: Object,
  clients: Array,
  loading: Boolean
})

const emit = defineEmits(['close', 'save'])

// Données du formulaire
const formData = ref({
  projet: '',
  client: ''
})

// Gestion des erreurs
const errors = ref({
  projet: '',
  client: ''
})

// Références
const projectNameInput = ref(null)

// Computed
const isFormValid = computed(() => {
  return formData.value.projet.trim() && formData.value.client && !Object.values(errors.value).some(error => error)
})

// Watchers
watch(() => props.show, (newValue) => {
  if (newValue) {
    resetForm()
    if (props.project) {
      formData.value = {
        projet: props.project.projet || '',
        client: props.project.client || ''
      }
    }
    
    // Focus sur le premier champ après ouverture
    nextTick(() => {
      if (projectNameInput.value) {
        projectNameInput.value.focus()
      }
    })
  }
})

// Méthodes
const resetForm = () => {
  formData.value = {
    projet: '',
    client: ''
  }
  errors.value = {
    projet: '',
    client: ''
  }
}

const validateForm = () => {
  errors.value = {
    projet: '',
    client: ''
  }

  if (!formData.value.projet.trim()) {
    errors.value.projet = 'Le nom du projet est requis'
  } else if (formData.value.projet.trim().length < 3) {
    errors.value.projet = 'Le nom doit contenir au moins 3 caractères'
  }

  if (!formData.value.client) {
    errors.value.client = 'Veuillez sélectionner un client'
  }

  return !Object.values(errors.value).some(error => error)
}

const handleSubmit = () => {
  if (validateForm()) {
    emit('save', { ...formData.value })
  }
}

const handleOverlayClick = (e) => {
  if (e.target === e.currentTarget) {
    emit('close')
  }
}

const getCompletionPercentage = (project) => {
  if (!project.sous_projets?.length) return 0
  const completed = project.sous_projets.filter(sp => sp.complet).length
  return Math.round((completed / project.sous_projets.length) * 100)
}

onMounted(() => {
  if (props.show) {
    document.body.style.overflow = 'hidden'
  }
})

const cleanup = () => {
  document.body.style.overflow = ''
}

// Gérer la fermeture avec Escape
const handleKeydown = (e) => {
  if (e.key === 'Escape' && props.show) {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  cleanup()
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal" appear>
      <div v-if="show" class="modal-overlay" @click="handleOverlayClick">
        <div class="modal-container" @click.stop>
          <!-- Header avec gradient -->
          <div class="modal-header">
            <div class="header-content">
              <div class="modal-icon">
                <div class="icon-wrapper">
                  {{ project ? '✏️' : '➕' }}
                </div>
              </div>
              <div class="header-text">
                <h2 class="modal-title">
                  {{ project ? 'Modifier le projet' : 'Nouveau projet' }}
                </h2>
                <p class="modal-subtitle">
                  {{ project ? 'Modifiez les informations du projet' : 'Créez un nouveau projet pour votre équipe' }}
                </p>
              </div>
            </div>
            <button @click="$emit('close')" class="close-btn">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <!-- Formulaire -->
          <form @submit.prevent="handleSubmit" class="modal-form">
            <div class="form-content">
              <!-- Nom du projet -->
              <div class="form-group">
                <label class="form-label">
                  <span class="label-text">Nom du projet</span>
                  <span class="label-required">*</span>
                </label>
                <div class="input-wrapper">
                  <div class="input-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                      <path d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" stroke="currentColor" stroke-width="1.5"/>
                    </svg>
                  </div>
                  <input
                    ref="projectNameInput"
                    v-model="formData.projet"
                    type="text"
                    class="form-input"
                    placeholder="Entrez le nom de votre projet..."
                    required
                    :class="{ error: errors.projet }"
                  >
                </div>
                <div v-if="errors.projet" class="error-message">
                  {{ errors.projet }}
                </div>
              </div>

              <!-- Client -->
              <div class="form-group">
                <label class="form-label">
                  <span class="label-text">Client</span>
                  <span class="label-required">*</span>
                </label>
                <div class="select-wrapper">
                  <div class="select-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                      <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z" stroke="currentColor" stroke-width="1.5"/>
                    </svg>
                  </div>
                  <select
                    v-model="formData.client"
                    class="form-select"
                    required
                    :class="{ error: errors.client }"
                  >
                    <option value="">Sélectionnez un client...</option>
                    <option v-for="client in clients" :key="client.id" :value="client.id">
                      {{ client.nom }}
                    </option>
                  </select>
                  <div class="select-arrow">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                      <path d="M7 10l5 5 5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                </div>
                <div v-if="errors.client" class="error-message">
                  {{ errors.client }}
                </div>
              </div>

              <!-- Informations supplémentaires si édition -->
              <div v-if="project" class="info-section">
                <div class="info-header">
                  <h3>Informations du projet</h3>
                </div>
                <div class="info-grid">
                  <div class="info-item">
                    <div class="info-label">Sous-projets</div>
                    <div class="info-value">{{ project.sous_projets?.length || 0 }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Progression</div>
                    <div class="info-value">{{ getCompletionPercentage(project) }}%</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Status</div>
                    <div class="info-badge" :class="project.sous_projets?.every(sp => sp.complet) ? 'complete' : 'active'">
                      {{ project.sous_projets?.every(sp => sp.complet) ? 'Terminé' : 'En cours' }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Footer avec actions -->
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
                  {{ project ? 'Modifier' : 'Créer' }} le projet
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
  max-width: 520px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.1);
}

/* Header */
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

/* Formulaire */
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

.label-required {
  color: #ef4444;
  font-size: 14px;
}

/* Input wrapper */
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

/* Select wrapper */
.select-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.select-icon {
  position: absolute;
  left: 16px;
  z-index: 1;
  color: #9ca3af;
  transition: color 0.2s ease;
}

.form-select {
  width: 100%;
  padding: 16px 48px 16px 48px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 16px;
  background: #f9fafb;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
  appearance: none;
  cursor: pointer;
}

.form-select:focus {
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.form-select:focus + .select-icon {
  color: #667eea;
}

.form-select.error {
  border-color: #ef4444;
  background: #fef2f2;
}

.select-arrow {
  position: absolute;
  right: 16px;
  color: #9ca3af;
  pointer-events: none;
  transition: transform 0.2s ease;
}

.form-select:focus ~ .select-arrow {
  transform: rotate(180deg);
  color: #667eea;
}

.error-message {
  color: #ef4444;
  font-size: 14px;
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Section d'informations */
.info-section {
  background: #f8fafc;
  border-radius: 12px;
  padding: 20px;
  margin-top: 24px;
}

.info-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 16px 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
}

.info-item {
  text-align: center;
}

.info-label {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.info-value {
  font-size: 18px;
  font-weight: 700;
  color: #374151;
}

.info-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-badge.complete {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.info-badge.active {
  background: rgba(59, 130, 246, 0.1);
  color: #2563eb;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

/* Footer */
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

.btn-spinner svg {
  width: 16px;
  height: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Transitions */
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

/* Responsive */
@media (max-width: 640px) {
  .modal-container {
    margin: 20px;
    max-width: calc(100vw - 40px);
  }
  
  .modal-header {
    padding: 24px;
  }
  
  .form-content {
    padding: 24px;
  }
  
  .modal-footer {
    padding: 20px 24px;
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>