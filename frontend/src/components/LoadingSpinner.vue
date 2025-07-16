<script setup lang="ts">
import { useLoading } from '../composables/useLoading'
const { isLoading } = useLoading()
</script>

<template>
  <transition name="fade">
    <div v-if="isLoading" class="spinner-container">
      <div class="spinner"></div>
    </div>
  </transition>
</template>

<style scoped>
.spinner-container {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 9999;
  width: 100vw;
  height: 100vh;
  background: rgba(255, 255, 255, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid #ccc;
  border-top: 5px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
