<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  show: Boolean,
  subproject: Object,
  availableFpacks: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  clientName: String
})

const emit = defineEmits(['save', 'close'])

const formData = ref({
  fpack_id: '',
  FPack_number: '',
  Robot_Location_Code: '',
  contractor: '',
  required_delivery_time: '',
  delivery_site: '',
  tracking: ''
})

const selectedFpack = computed(() => {
  if (!formData.value.fpack_id) return null
  return props.availableFpacks.find(f => f.id === formData.value.fpack_id)
})

const handleSubmit = () => {
  if (formData.value.fpack_id) {
    emit('save', { ...formData.value })
  }
}

const handleOverlayClick = () => {
  emit('close')
}

watch(() => props.show, (show) => {
  if (!show) {
    setTimeout(() => {
      formData.value = {
        fpack_id: '',
        FPack_number: '',
        Robot_Location_Code: '',
        contractor: '',
        required_delivery_time: '',
        delivery_site: '',
        tracking: ''
      }
    }, 300)
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="show" class="modal-overlay" @click="handleOverlayClick">
        <div class="modal-container" @click.stop>
          <div class="modal-content">
            <!-- Header avec icône animée -->
            <div class="modal-header">
              <div class="header-content">
                <div class="header-icon">
                  <div class="icon-container">
                    📦
                    <div class="icon-ripple"></div>
                  </div>
                </div>
                <div class="header-text">
                  <h3>Associer un FPack</h3>
                  <p v-if="subproject">
                    au sous-projet <strong>{{ subproject.nom }}</strong>
                  </p>
                </div>
              </div>
              <button @click="$emit('close')" class="close-btn">
                <span class="close-icon">✕</span>
              </button>
            </div>

            <!-- Corps du modal avec formulaire élégant -->
            <form @submit.prevent="handleSubmit" class="modal-body">
              <!-- Sélection FPack avec recherche -->
              <div class="form-section">
                <label class="form-label">
                  <span class="label-icon">📦</span>
                  <span class="label-text">Sélectionner un FPack</span>
                </label>
                
                <div class="select-container">
                  <select 
                    v-model="formData.fpack_id" 
                    required 
                    class="form-select"
                    :class="{ 'has-value': formData.fpack_id }"
                  >
                    <option value="">Choisissez un FPack disponible</option>
                    <option 
                      v-for="fpack in availableFpacks" 
                      :key="fpack.id" 
                      :value="fpack.id"
                    >
                      {{ fpack.nom }}
                    </option>
                  </select>
                </div>

                <div v-if="availableFpacks.length === 0" class="no-fpacks-warning">
                  <div class="warning-icon">⚠️</div>
                  <div class="warning-text">
                    <strong>Aucun FPack disponible</strong>
                    <p>Il n'y a pas de FPack disponible pour ce client.</p>
                  </div>
                </div>
              </div>

              <!-- Champs de base avec design moderne -->
              <div class="form-section">
                <div class="form-grid">
                  <div class="field-group">
                    <label for="fpack-number" class="form-label optional">
                      <span class="label-icon">#</span>
                      <span class="label-text">Numéro FPack</span>
                    </label>
                    <div class="input-container">
                      <input
                        id="fpack-number"
                        v-model="formData.FPack_number"
                        type="text"
                        class="form-input"
                      >
                      <div class="input-focus-border"></div>
                    </div>
                  </div>

                  <div class="field-group">
                    <label for="robot-location" class="form-label optional">
                      <span class="label-icon">📍</span>
                      <span class="label-text">Robot Location Code</span>
                    </label>
                    <div class="input-container">
                      <input
                        id="robot-location"
                        v-model="formData.Robot_Location_Code"
                        type="text"
                        class="form-input"
                      >
                      <div class="input-focus-border"></div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Nouveaux champs de livraison -->
              <div class="form-section">
                <h4 class="section-title">
                  <span class="section-icon">🚚</span>
                  Informations générales
                </h4>
                
                <div class="form-grid">
                  <div class="field-group">
                    <label for="contractor" class="form-label optional">
                      <span class="label-icon">👷</span>
                      <span class="label-text">Entrepreneur</span>
                    </label>
                    <div class="input-container">
                      <input
                        id="contractor"
                        v-model="formData.contractor"
                        type="text"
                        class="form-input"
                      >
                      <div class="input-focus-border"></div>
                    </div>
                  </div>

                  <div class="field-group">
                    <label for="required-delivery-time" class="form-label optional">
                      <span class="label-icon">⏰</span>
                      <span class="label-text">Temps de livraison requis</span>
                    </label>
                    <div class="input-container">
                      <input
                        id="required-delivery-time"
                        v-model="formData.required_delivery_time"
                        type="text"
                        class="form-input"
                      >
                      <div class="input-focus-border"></div>
                    </div>
                  </div>

                  <div class="field-group">
                    <label for="delivery-site" class="form-label optional">
                      <span class="label-icon">🏢</span>
                      <span class="label-text">Site de livraison</span>
                    </label>
                    <div class="input-container">
                      <input
                        id="delivery-site"
                        v-model="formData.delivery_site"
                        type="text"
                        class="form-input"
                      >
                      <div class="input-focus-border"></div>
                    </div>
                  </div>

                  <div class="field-group">
                    <label for="tracking" class="form-label optional">
                      <span class="label-icon">📊</span>
                      <span class="label-text">Suivi</span>
                    </label>
                    <div class="input-container">
                      <input
                        id="tracking"
                        v-model="formData.tracking"
                        type="text"
                        class="form-input"
                      >
                      <div class="input-focus-border"></div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="selectedFpack" class="fpack-preview">
                <div class="preview-header">
                  <h4>Aperçu du FPack sélectionné</h4>
                </div>
                <div class="preview-card">
                  <div class="preview-icon">📦</div>
                  <div class="preview-details">
                    <div class="preview-name">{{ selectedFpack.nom }}</div>
                    <div class="preview-meta">
                      <span class="meta-item">
                        <span class="meta-icon">👤</span>
                        Client: {{ clientName || 'Non spécifié' }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Actions -->
              <div class="modal-actions">
                <button type="button" @click="$emit('close')" class="btn btn-secondary">
                  <span class="btn-icon">↶</span>
                  <span class="btn-text">Annuler</span>
                </button>
                <button 
                  type="submit" 
                  class="btn btn-primary"
                  :disabled="!formData.fpack_id || loading"
                  :class="{ 'loading': loading }"
                >
                  <span v-if="loading" class="btn-spinner">
                    <svg class="spinner" width="16" height="16" viewBox="0 0 24 24">
                      <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="32" stroke-dashoffset="32">
                        <animate attributeName="stroke-dasharray" dur="2s" values="0 32;16 16;0 32;0 32" repeatCount="indefinite"/>
                        <animate attributeName="stroke-dashoffset" dur="2s" values="0;-16;-32;-32" repeatCount="indefinite"/>
                      </circle>
                    </svg>
                  </span>
                  <span v-else class="btn-icon">📦</span>
                  <span class="btn-text">{{ loading ? 'Association...' : 'Associer' }}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* Transitions */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-from .modal-container,
.modal-fade-leave-to .modal-container {
  transform: scale(0.9) translateY(-50px);
}

/* Modal Structure */
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
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.modal-content {
  background: white;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 
    0 32px 64px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(255, 255, 255, 0.05);
}

/* Header */
.modal-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 24px;
  color: white;
  position: relative;
  overflow: hidden;
}

.modal-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 20"><defs><radialGradient id="a"><stop offset="20%" stop-color="%23ffffff" stop-opacity="0.1"/><stop offset="100%" stop-color="%23ffffff" stop-opacity="0"/></radialGradient></defs><rect fill="url(%23a)" width="100" height="20"/></svg>') repeat-x;
  opacity: 0.1;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  z-index: 1;
}

.header-icon {
  position: relative;
}

.icon-container {
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  position: relative;
  backdrop-filter: blur(10px);
}

.icon-ripple {
  position: absolute;
  inset: -8px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  animation: ripple 2s ease-in-out infinite;
}

@keyframes ripple {
  0% {
    transform: scale(0.8);
    opacity: 1;
  }
  100% {
    transform: scale(1.2);
    opacity: 0;
  }
}

.header-text h3 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
}

.header-text p {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.close-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 36px;
  height: 36px;
  border: none;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
  z-index: 2;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.1);
}

.close-icon {
  font-size: 16px;
  font-weight: 300;
}

/* Form Body */
.modal-body {
  padding: 32px 24px;
  max-height: calc(90vh - 140px);
  overflow-y: auto;
}

.form-section {
  margin-bottom: 32px;
}

.form-section:last-child {
  margin-bottom: 0;
}

/* Section Title */
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #334155;
  padding-bottom: 8px;
  border-bottom: 2px solid #f1f5f9;
}

.section-icon {
  font-size: 18px;
}

/* Form Labels */
.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: #334155;
  font-size: 14px;
  cursor: pointer;
}

.form-label.optional {
  color: #64748b;
}

.label-icon {
  font-size: 16px;
}

/* Grid Layout */
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.field-group {
  width: 100%;
}

/* Select Field */
.select-container {
  position: relative;
}

.form-select {
  width: 100%;
  padding: 16px 48px 16px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  font-size: 15px;
  background: white;
  outline: none;
  transition: all 0.3s ease;
  appearance: none;
  cursor: pointer;
  box-sizing: border-box;
}

.form-select:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.form-select.has-value {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.02);
}

/* Input Fields */
.input-container {
  position: relative;
  width: 100%;
}

.form-input {
  width: 100%;
  padding: 16px;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  font-size: 15px;
  background: white;
  outline: none;
  transition: all 0.3s ease;
  box-sizing: border-box;
  position: relative;
  z-index: 1;
}

.form-input:focus {
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
}

.input-focus-border {
  position: absolute;
  inset: 0;
  border: 2px solid transparent;
  border-radius: 16px;
  background: linear-gradient(135deg, #667eea, #764ba2) border-box;
  mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  mask-composite: xor;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
  z-index: 0;
}

.form-input:focus + .input-focus-border {
  opacity: 0.3;
}

/* Warning */
.no-fpacks-warning {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(251, 146, 60, 0.05);
  border: 1px solid rgba(251, 146, 60, 0.2);
  border-radius: 12px;
  margin-top: 12px;
}

.warning-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.warning-text strong {
  display: block;
  color: #ea580c;
  font-weight: 600;
  margin-bottom: 4px;
}

.warning-text p {
  margin: 0;
  color: #9a3412;
  font-size: 14px;
}

/* FPack Preview */
.fpack-preview {
  background: rgba(102, 126, 234, 0.03);
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 16px;
  padding: 20px;
}

.preview-header h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #475569;
}

.preview-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.preview-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
  flex-shrink: 0;
}

.preview-details {
  flex: 1;
}

.preview-name {
  font-weight: 600;
  color: #334155;
  margin-bottom: 4px;
}

.preview-meta {
  display: flex;
  gap: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #64748b;
}

.meta-icon {
  font-size: 14px;
}

/* Actions */
.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 24px;
  border-top: 1px solid #f1f5f9;
  margin-top: 24px;
}

.btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f8fafc;
  color: #475569;
  border: 1px solid #e2e8f0;
}

.btn-secondary:hover:not(:disabled) {
  background: #f1f5f9;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.btn-primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.btn-primary.loading {
  background: linear-gradient(135deg, #94a3b8, #64748b);
}

.btn-icon {
  font-size: 16px;
}

.btn-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.modal-body::-webkit-scrollbar {
  width: 6px;
}

.modal-body::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.modal-body::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>