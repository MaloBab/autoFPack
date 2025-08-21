<script setup>
import { ref } from 'vue'

const props = defineProps({
  titre: {
    type: String,
    required: true
  }
})

const isHovered = ref(false)
</script>

<template>
  <div class="title-container">
    <h1 
      class="title"
      :class="{ 'hovered': isHovered }"
      @mouseenter="isHovered = true"
      @mouseleave="isHovered = false"
    >
      {{ titre }}
      
      <!-- Ligne décorative subtile -->
      <div class="underline"></div>
    </h1>
  </div>
</template>

<style scoped>
.title-container {
  position: relative;
  display: block;
  margin-top: 1%;
  margin-left: 2%;
  width: fit-content;
}

.title {
  position: relative;
  font-size: clamp(2.5rem, 5vw, 3.5rem);
  font-weight: 600;
  color: #2d3748;
  margin: 0; 
  margin-bottom: 1%;
  margin-left: 2%;
  padding: 0.5rem 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  letter-spacing: -0.02em;
  line-height: 1.2;
  
  /* Anti-aliasing pour la netteté */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Ligne décorative */
.underline {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2px;
  width: 0;
  background: linear-gradient(90deg, #4299e1, #667eea);
  border-radius: 1px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.title.hovered {
  color: #1a202c;
  transform: translateY(-1px);
}

.title.hovered .underline {
  width: 100%;
}

</style>