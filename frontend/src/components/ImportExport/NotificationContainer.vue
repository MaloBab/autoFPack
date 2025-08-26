<script setup lang="ts">
interface Notification {
  id: number
  type: 'success' | 'warning' | 'error' | 'info'
  message: string
}

defineProps<{
  notifications: Notification[]
  getNotificationIcon: (type: string) => string
}>()

defineEmits<{
  removeNotification: [id: number]
}>()
</script>

<template>
  <div class="notifications" v-if="notifications.length > 0">
    <transition-group name="notification" tag="div">
      <div 
        v-for="notification in notifications" 
        :key="notification.id"
        class="notification"
        :class="notification.type"
      >
        <div class="notification-icon">
          {{ getNotificationIcon(notification.type) }}
        </div>
        <div class="notification-content">
          <span>{{ notification.message }}</span>
        </div>
        <button class="notification-close" @click="$emit('removeNotification', notification.id)">
          ❌
        </button>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
.notifications {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
}

.notification {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border-radius: 10px;
  color: white;
  font-weight: 600;
  min-width: 280px;
  max-width: 420px;
  backdrop-filter: blur(20px);
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.15);
  transform: translateX(100%);
  animation: slideInNotification 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards;
  pointer-events: all;
  position: relative;
  overflow: hidden;
}

.notification::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  background: rgba(255, 255, 255, 0.3);
}

@keyframes slideInNotification {
  to {
    transform: translateX(0);
  }
}

.notification-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.notification-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.notification-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.notification-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.notification.success {
  background: linear-gradient(135deg, rgba(39, 174, 96, 0.95) 0%, rgba(46, 204, 113, 0.95) 100%);
}

.notification.warning {
  background: linear-gradient(135deg, rgba(243, 156, 18, 0.95) 0%, rgba(230, 126, 34, 0.95) 100%);
}

.notification.error {
  background: linear-gradient(135deg, rgba(231, 76, 60, 0.95) 0%, rgba(192, 57, 43, 0.95) 100%);
}

.notification.info {
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.95) 0%, rgba(155, 89, 182, 0.95) 100%);
}

.notification-icon {
  font-size: 1.1rem;
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
  font-size: 0.9rem;
  line-height: 1.3;
}

.notification-close {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  padding: 3px;
  border-radius: 3px;
  transition: all 0.3s ease;
  font-size: 0.9rem;
  flex-shrink: 0;
}

.notification-close:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  transform: scale(1.05);
}
</style>