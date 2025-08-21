<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  text: {
    type: String,
    default: 'Chargement en cours'
  },
  showProgress: {
    type: Boolean,
    default: false
  },
  progress: {
    type: Number,
    default: 0
  }
})


const loadingText = ref('Chargement en cours')

// Style des particules
const getParticleStyle = (index) => {
  const angle = (index * 30) - 90
  const distance = 80 + (index % 3) * 20
  const x = Math.cos(angle * Math.PI / 180) * distance
  const y = Math.sin(angle * Math.PI / 180) * distance
  const delay = index * 0.1
  
  return {
    '--x': `${x}px`,
    '--y': `${y}px`,
    '--delay': `${delay}s`,
    '--duration': `${2 + (index % 3) * 0.5}s`
  }
}

onMounted(() => {
  if (props.show) {
    setTimeout(animateLoadingText, 2000)
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="overlay-fade">
      <div v-if="show" class="loading-overlay" @click.prevent>
        <div class="overlay-background"></div>
        <div class="loading-container">
          <div class="loading-spinner-container">
            <div class="spinner-rings">
              <div class="ring ring-1"></div>
              <div class="ring ring-2"></div>
              <div class="ring ring-3"></div>
            </div>
            
            <!-- Icône centrale -->
            <div class="spinner-icon">
              ⏳
            </div>
            
            <!-- Particules flottantes -->
            <div class="particles">
              <div v-for="i in 12" :key="i" class="particle" :style="getParticleStyle(i)"></div>
            </div>
          </div>
          
          <!-- Texte de chargement -->
          <div class="loading-content">
            <h3 class="loading-title">
              <span class="loading-text">{{ loadingText }}</span>
              <span class="loading-dots">
                <span>.</span>
                <span>.</span>
                <span>.</span>
              </span>
            </h3>
          </div>
          
          <!-- Barre de progression (optionnelle) -->
          <div v-if="showProgress" class="progress-container">
            <div class="progress-bar">
              <div class="progress-fill" :style="`width: ${progress}%`"></div>
              <div class="progress-glow"></div>
            </div>
            <div class="progress-text">{{ Math.round(progress) }}%</div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>


<style scoped>
/* Overlay principal */
.loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.overlay-background {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

/* Animations d'entrée/sortie */
.overlay-fade-enter-active,
.overlay-fade-leave-active {
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.overlay-fade-enter-from,
.overlay-fade-leave-to {
  opacity: 0;
}

.overlay-fade-enter-from .loading-container,
.overlay-fade-leave-to .loading-container {
  transform: scale(0.8) translateY(40px);
}

/* Conteneur principal */
.loading-container {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 48px 40px;
  box-shadow: 
    0 32px 64px rgba(0, 0, 0, 0.1),
    0 0 0 1px rgba(255, 255, 255, 0.2);
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  z-index: 10;
}

/* Spinner principal */
.loading-spinner-container {
  position: relative;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Anneaux animés */
.spinner-rings {
  position: absolute;
  width: 100%;
  height: 100%;
}

.ring {
  position: absolute;
  border: 2px solid transparent;
  border-radius: 50%;
  animation-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}

.ring-1 {
  width: 100%;
  height: 100%;
  border-top: 2px solid #eacb66;
  border-right: 2px solid #eac266;
  animation: spin 2s linear infinite;
}

.ring-2 {
  width: 80%;
  height: 80%;
  top: 10%;
  left: 10%;
  border-bottom: 2px solid #a24b4b;
  border-left: 2px solid #a24b4b;
  animation: spin 1.5s linear infinite reverse;
}

.ring-3 {
  width: 60%;
  height: 60%;
  top: 20%;
  left: 20%;
  border-top: 2px solid #3e3f3f;
  border-right: 2px solid #1a1a1a;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Icône centrale */
.spinner-icon {
  font-size: 2.5rem;
  position: relative;
  z-index: 2;
  animation: flip-snap 2s ease-in-out infinite;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));
}

@keyframes flip-snap{
  0%   { transform: rotate(0deg); }
  50%  { transform: rotate(180deg); }
  100% { transform: rotate(360deg); }
}


/* Particules */
.particles {
  position: absolute;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: linear-gradient(45deg, #3b3b3c, #1a191a);
  border-radius: 50%;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: particleFloat var(--duration) ease-in-out var(--delay) infinite;
}

@keyframes particleFloat {
  0%, 100% {
    transform: translate(-50%, -50%) translate(0, 0) scale(0.5);
    opacity: 0.3;
  }
  25% {
    transform: translate(-50%, -50%) translate(var(--x), var(--y)) scale(1);
    opacity: 1;
  }
  75% {
    transform: translate(-50%, -50%) translate(calc(var(--x) * 0.5), calc(var(--y) * 0.5)) scale(0.8);
    opacity: 0.6;
  }
}

/* Contenu texte */
.loading-content {
  text-align: center;
  max-width: 300px;
}

.loading-title {
  margin: 0 0 12px 0;
  font-size: 20px;
  font-weight: 700;
  color: #334155;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.loading-text {
  transition: all 0.3s ease;
}

.loading-dots {
  display: flex;
  gap: 2px;
}

.loading-dots span {
  animation: dots 1.4s ease-in-out infinite;
  color: #030617;
  font-weight: bold;
}

.loading-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.loading-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dots {
  0%, 20%, 80%, 100% {
    transform: scale(1);
    opacity: 0.3;
  }
  50% {
    transform: scale(1.5);
    opacity: 1;
  }
}


/* Barre de progression */
.progress-container {
  width: 100%;
  max-width: 280px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-bar {
  position: relative;
  height: 8px;
  background: rgba(100, 116, 139, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-glow {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 100px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent);
  animation: progressGlow 2s ease-in-out infinite;
}

@keyframes progressGlow {
  0% { transform: translateX(-100px); }
  100% { transform: translateX(300px); }
}

.progress-text {
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: #667eea;
}



.overlay-fade-enter-active .ring-1 {
  animation: spin 2s linear infinite, scaleIn 0.6s ease-out;
}

.overlay-fade-enter-active .ring-2 {
  animation: spin 1.5s linear infinite reverse, scaleIn 0.6s ease-out 0.1s both;
}

.overlay-fade-enter-active .ring-3 {
  animation: spin 1s linear infinite, scaleIn 0.6s ease-out 0.2s both;
}

.overlay-fade-enter-active .loading-content {
  animation: fadeInUp 0.6s ease-out 0.4s both;
}

.overlay-fade-enter-active .progress-container {
  animation: fadeInUp 0.6s ease-out 0.5s both;
}

@keyframes scaleIn {
  from {
    transform: scale(0);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.loading-container {
  animation: containerPulse 4s ease-in-out infinite;
}

@keyframes containerPulse {
  0%, 100% {
    box-shadow: 
      0 32px 64px rgba(0, 0, 0, 0.1),
      0 0 0 1px rgba(255, 255, 255, 0.2);
  }
  50% {
    box-shadow: 
      0 40px 80px rgba(0, 0, 0, 0.15),
      0 0 0 1px rgba(255, 255, 255, 0.3),
      0 0 40px rgba(102, 126, 234, 0.1);
  }
}


</style>