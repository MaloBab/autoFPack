<script setup>
import { computed } from 'vue'

const props = defineProps({
  notifications: {
    type: Array,
    default: () => []
  }
})



const SuccessIcon = {
  template: `
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="m9 12 2 2 4-4"/>
      <circle cx="12" cy="12" r="9"/>
    </svg>
  `
}

const ErrorIcon = {
  template: `
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="9"/>
      <line x1="15" y1="9" x2="9" y2="15"/>
      <line x1="9" y1="9" x2="15" y2="15"/>
    </svg>
  `
}

const WarningIcon = {
  template: `
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
      <line x1="12" y1="9" x2="12" y2="13"/>
      <path d="m12 17.02.01 0"/>
    </svg>
  `
}

const InfoIcon = {
  template: `
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="9"/>
      <line x1="12" y1="8" x2="12" y2="12"/>
      <path d="m12 16.02.01 0"/>
    </svg>
  `
}

const getIconComponent = (type) => {
  switch (type) {
    case 'success':
      return SuccessIcon
    case 'error':
      return ErrorIcon
    case 'warning':
      return WarningIcon
    default:
      return InfoIcon
  }
}

const getTypeLabel = (type) => {
  switch (type) {
    case 'success':
      return 'Succès'
    case 'error':
      return 'Erreur'
    case 'warning':
      return 'Attention'
    default:
      return 'Information'
  }
}

</script>

<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast" tag="div" class="toast-wrapper">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          :class="['toast', `toast-${notification.type}`]"
          @click="removeNotification(notification.id)"
        >
          <!-- Indicateur visuel et icône -->
          <div class="toast-indicator" :class="`indicator-${notification.type}`">
            <div class="toast-icon">
              <component :is="getIconComponent(notification.type)" />
            </div>
          </div>

          <!-- Contenu du toast -->
          <div class="toast-content">
            <div class="toast-title">
              {{ getTypeLabel(notification.type) }}
            </div>
            <div class="toast-message">
              {{ notification.message }}
            </div>
          </div>

          <!-- Barre de progression -->
          <div class="toast-progress" :class="`progress-${notification.type}`">
            <div class="progress-bar"></div>
          </div>
          <div class="toast-background-effect"></div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>


<style scoped>
.toast-container {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 9999;
  max-width: 400px;
  width: 100%;
  pointer-events: none;
}

.toast-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Toast Base */
.toast {
  position: relative;
  background: white;
  border-radius: 16px;
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.1),
    0 0 0 1px rgba(255, 255, 255, 0.05);
  border-left: 4px solid;
  cursor: pointer;
  pointer-events: auto;
  backdrop-filter: blur(20px);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.toast:hover {
  transform: translateX(-8px) scale(1.02);
  box-shadow: 
    0 25px 50px rgba(0, 0, 0, 0.15),
    0 0 0 1px rgba(255, 255, 255, 0.1);
}

/* Types de toast */
.toast-success {
  border-left-color: #10b981;
  background: rgba(255, 255, 255, 0.95);
}

.toast-error {
  border-left-color: #ef4444;
  background: rgba(255, 255, 255, 0.95);
}

.toast-warning {
  border-left-color: #f59e0b;
  background: rgba(255, 255, 255, 0.95);
}

.toast-info {
  border-left-color: #3b82f6;
  background: rgba(255, 255, 255, 0.95);
}

/* Indicateur et icône */
.toast-indicator {
  position: relative;
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.indicator-success {
  background: linear-gradient(135deg, #10b981, #059669);
}

.indicator-error {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}
.indicator-warning {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}
.indicator-info {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
}

.toast-icon {
  width: 24px;
  height: 24px;
  color: white;
}
</style>