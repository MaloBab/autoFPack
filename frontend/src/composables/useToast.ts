// src/composables/useToast.ts
import { ref } from 'vue'

const visible = ref(false)
const message = ref('')
const color = ref('#1e293b')

let timeoutId: ReturnType<typeof setTimeout> | null = null

function showToast(msg: string, bgColor = '#1e293b', duration = 3000) {
  // Reset timer si un toast est déjà en cours
  if (timeoutId) {
    clearTimeout(timeoutId)
    timeoutId = null
  }

  message.value = msg
  color.value = bgColor
  visible.value = true

  timeoutId = setTimeout(() => {
    visible.value = false
    timeoutId = null
  }, duration)
}

export function useToastStore() {
  return {
    visible,
    message,
    color,
    showToast,
  }
}

export { showToast }
