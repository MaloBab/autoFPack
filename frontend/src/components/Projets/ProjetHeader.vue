<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import CounterAnimation from './CounterAnimation.vue'

const props = defineProps({
  stats: Object,
  loading: Boolean
})


const logoAnimated = ref(false)
const triggerLogoAnimation = () => {
  logoAnimated.value = true
  setTimeout(() => logoAnimated.value = false, 600)
}
const titleWords = ['Gestionnaire', 'de', 'Projets']

const particles = ref([])
const createParticles = () => {
  particles.value = Array.from({ length: 20 }, (_, i) => ({
    id: i,
    style: {
      left: Math.random() * 100 + '%',
      top: Math.random() * 100 + '%',
      animationDelay: Math.random() * 20 + 's',
      animationDuration: (15 + Math.random() * 10) + 's'
    }
  }))
}

const displayStats = computed(() => {
  if (!props.stats) return []
  
  const completionRate = props.stats.nb_sous_projets ? 
    (props.stats.sous_projets_complets / props.stats.nb_sous_projets * 100).toFixed(1) : 0
  
  return [
    {
      key: 'projects',
      icon: '📁',
      value: props.stats.nb_projets_globaux,
      label: 'Projets',
      animated: false
    },
    {
      key: 'subprojects',
      icon: '📋',
      value: props.stats.nb_sous_projets,
      label: 'Sous-projets',
      animated: false
    },
    {
      key: 'completed',
      icon: '✅',
      value: props.stats.sous_projets_complets,
      label: 'Terminés',
      progress: parseFloat(completionRate),
      animated: false
    }
  ]
})

const animateStat = (key) => {
  const stat = displayStats.value.find(s => s.key === key)
  if (stat) {
    stat.animated = true
    setTimeout(() => stat.animated = false, 600)
  }
}

onMounted(() => {
  createParticles()
})
</script>


<template>
  <header class="header-section">
    <div class="particles-container">
      <div 
        v-for="particle in particles" 
        :key="particle.id"
        class="particle"
        :style="particle.style"
      ></div>
    </div>

    <div class="header-content">
      <div class="brand-section">        
        <div class="title-section">
          <h1 class="main-title">
            <span class="title-word" v-for="(word, index) in titleWords" :key="index">
              {{ word }}
            </span>
          </h1>
        </div>
      </div>

      <div class="stats-showcase" v-if="stats">
        <div class="stats-grid">
          <div 
            class="stat-card" 
            v-for="stat in displayStats" 
            :key="stat.key"
            @mouseenter="animateStat(stat.key)"
            :class="{ animate: stat.animated }"
          >
            <div class="stat-icon">{{ stat.icon }}</div>
            <div class="stat-value">
              <CounterAnimation :value="stat.value" :duration="1000" />
            </div>
            <div class="stat-label">{{ stat.label }}</div>
            <div class="stat-progress" v-if="stat.progress">
              <div class="progress-bar">
                <div 
                  class="progress-fill" 
                  :style="`width: ${stat.progress}%`"
                ></div>
              </div>
              <span class="progress-text">{{ stat.progress }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.header-section {
  background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 10px;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.2);
  box-shadow: 0 25px 50px rgba(0,0,0,0.1);
}

.particles-container {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: rgba(255,255,255,0.6);
  border-radius: 50%;
  animation: float infinite ease-in-out;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

.header-content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.brand-section {
  display: flex;
  align-items: center;
  gap: 20px;
}


@keyframes logoSpin {
  0% { transform: rotate(0deg) scale(1); }
  50% { transform: rotate(180deg) scale(1.1); }
  100% { transform: rotate(360deg) scale(1); }
}


.title-section {
  color: white;
}

.main-title {
  font-size: 2.5vw;
  font-weight: 600;
  margin: 0;
  display: flex;
  gap: 0.3em;
}

.title-word {
  display: inline-block;
  animation: titleSlide 1s ease-out forwards;
  opacity: 0;
  transform: translateY(20px);
}

.title-word:nth-child(1) { animation-delay: 0.1s; }
.title-word:nth-child(2) { animation-delay: 0.2s; }
.title-word:nth-child(3) { animation-delay: 0.3s; }

@keyframes titleSlide {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stats-showcase {
  flex: 1;
  max-width: 600px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
}

.stat-card {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 10px;
  text-align: center;
  gap: 5px;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  border: 1px solid rgba(255,255,255,0.2);
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-5px);
  background: rgba(255,255,255,0.2);
  box-shadow: 0 15px 35px rgba(0,0,0,0.2);
}

.stat-card.animate {
  animation: statPulse 0.6s ease;
}

@keyframes statPulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.stat-icon {
  font-size: 1.2rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
}

.stat-label {
  color: rgba(255,255,255,0.9);
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.stat-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%; 
}

.progress-bar {
  flex: 0 0 70%; 
  height: 6px;
  background: rgba(255,255,255,0.2);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #34d399);
  border-radius: 3px;
  transition: width 1s ease;
}

.progress-text {
  font-size: 0.8rem;
  color: rgba(255,255,255,0.8);
  font-weight: 600;
  white-space: nowrap;
  
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>