import { ref } from 'vue'

interface Notification {
  id: number
  type: 'success' | 'warning' | 'error' | 'info'
  message: string
}

let notificationId = 0

export function useNotifications() {
  const notifications = ref<Notification[]>([])

  const addNotification = (type: 'success' | 'warning' | 'error' | 'info', message: string) => {
    const id = ++notificationId
    notifications.value.push({ id, type, message })
    
    setTimeout(() => {
      removeNotification(id)
    }, 5000)
  }

  const removeNotification = (id: number) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }

  const getNotificationIcon = (type: string): string => {
    switch (type) {
      case 'success': return '✅'
      case 'warning': return '⚠️'
      case 'error': return '❌'
      case 'info': return 'ℹ️'
      default: return 'ℹ️'
    }
  }

  return {
    notifications,
    addNotification,
    removeNotification,
    getNotificationIcon
  }
}