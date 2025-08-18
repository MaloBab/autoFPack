<script setup lang="ts">
import { useToastStore } from '../../composables/useToast'

const { visible, message, color } = useToastStore()
</script>

<template>
  <transition name="fade">
    <div v-if="visible" class="toast" :style="{ backgroundColor: color }">
      {{ message }}
    </div>
  </transition>
</template>

<style scoped>
.toast {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  color: white;
  padding: 1rem 2rem;
  border-radius: 8px;
  box-shadow: 0 0 10px rgba(0,0,0,0.3);
  z-index: 9999;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
