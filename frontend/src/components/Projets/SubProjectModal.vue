<template>
  <Teleport to="body">
    <Transition name="modal" appear>
      <div v-if="show" class="modal-overlay" @click="handleOverlayClick">
        <div class="modal-container" @click.stop>
          <!-- Header avec design moderne -->
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
            <button @click="$emit('close')" class="close-btn">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <!-- Formulaire -->
          <form @submit.prevent="handleSubmit" class="modal-form">
            <div class="form-content">
              <!-- Preview des actions possibles -->
              <div v-if="!subproject" class="actions-preview">
                <div class="preview-header">
                  <span class="preview-title">🚀 Après création</span>
                </div>
                <div class="preview-items">
                  <div class="preview-item">
                    <div class="preview-icon">📦</div>
                    <span>Associer un FPack</span>
                  </div>
                  <div class="preview-item">
                    <div class="preview-icon">🎯</div>
                    <span>Définir les objectifs</span>
                  </div>
                  <div class="preview-item">
                    <div class="preview-icon">✅</div>
                    <span>Suivre la progression</span>
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
<script setup>
import { ref, computed, watch, onMounted, nextTick, onUnmounted } from 'vue'

const props = defineProps({
  show: Boolean,
  subproject: Object,
  project: Object,
  loading: Boolean
})

const emit = defineEmits(['close', 'save'])

// Données du formulaire
const formData = ref({
  nom: '',
  id_global: ''
})

// Gestion des erreurs
const errors = ref({
  nom: ''
})

// Références
const subprojectNameInput = ref(null)

// Suggestions de noms basées sur des patterns courants
const nameSuggestions = computed(() => {
  if (!props.project) return []
  
  const existingNames = props.project.sous_projets?.map(sp => sp.nom.toLowerCase()) || []
  const suggestions = [
    'Phase 1', 'Phase 2', 'Phase 3',
    'Module A', 'Module B', 'Module C',
    'Sprint 1', 'Sprint 2', 'Sprint 3',
    'Étape initiale', 'Développement', 'Tests',
    'Conception', 'Implémentation', 'Validation'
  ]
  
  return suggestions.filter(suggestion => 
    !existingNames.includes(suggestion.toLowerCase())
  ).slice(0, 6)
})

// Computed
const isFormValid = computed(() => {
  return formData.value.nom.trim() && !Object.values(errors.value).some(error => error)
})

// Watchers
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
    
    // Focus sur le premier champ après ouverture
    nextTick(() => {
      if (subprojectNameInput.value) {
        subprojectNameInput.value.focus()
      }
    })
  }
})

// Méthodes
const resetForm = () => {
  formData.value = {
    nom: '',
    id_global: ''
  }
  errors.value = {
    nom: ''
  }
}

const validateForm = () => {
  errors.value = {
    nom: ''
  }

  if (!formData.value.nom.trim()) {
    errors.value.nom = 'Le nom du sous-projet est requis'
  } else if (formData.value.nom.trim().length < 2) {
    errors.value.nom = 'Le nom doit contenir au moins 2 caractères'
  } else if (formData.value.nom.trim().length > 100) {
    errors.value.nom = 'Le nom ne peut pas dépasser 100 caractères'
  }

  // Vérifier les doublons si on est en création
  if (!props.subproject && props.project) {
    const existingNames = props.project.sous_projets?.map(sp => sp.nom.toLowerCase()) || []
    if (existingNames.includes(formData.value.nom.toLowerCase())) {
      errors.value.nom = 'Un sous-projet avec ce nom existe déjà'
    }
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

const getClientName = (clientId) => {
  // Cette fonction devrait idéalement recevoir la liste des clients via props
  // Pour l'instant, on retourne juste l'ID
  return `Client ${clientId}`
}

// Gérer la fermeture avec Escape
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

/* Contexte du projet */
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

.context-client {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
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

/* Form group */
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

.error-message {
  color: #ef4444;
  font-size: 14px;
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Suggestions */
.suggestions-section {
  background: #f8fafc;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
}

.suggestions-header {
  margin-bottom: 12px;
}

.suggestions-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.suggestions-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggestion-chip {
  padding: 8px 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s ease;
}

.suggestion-chip:hover {
  background: #667eea;
  color: white;
  border-color: #667eea;
  transform: translateY(-1px);
}

/* Info section */
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

.info-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-badge.complete {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.info-badge.pending {
  background: rgba(251, 146, 60, 0.1);
  color: #ea580c;
}

/* Actions preview */
.actions-preview {
  background: linear-gradient(135deg, #667eea20, #764ba220);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 8px;
}

.preview-header {
  margin-bottom: 12px;
}

.preview-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.preview-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #6b7280;
}

.preview-icon {
  font-size: 14px;
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
  
  .context-header {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
  
  .suggestions-grid {
    justify-content: center;
  }
}
</style>