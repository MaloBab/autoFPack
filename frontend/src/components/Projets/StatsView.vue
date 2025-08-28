<script setup>
import { computed } from 'vue'
import CounterAnimation from './CounterAnimation.vue'

const props = defineProps({
  stats: Object,
  loading: Boolean,
  projets: Array
})

const metricsData = computed(() => {
  if (!props.stats) return []
  
  return [
    {
      key: 'projects',
      icon: '📁',
      value: props.stats.nb_projets_globaux,
      label: 'Projets',
      type: 'primary',
      visual: [60, 80, 45, 90, 75, 95, 70, 85, 100]
    },
    {
      key: 'subprojects',
      icon: '📋',
      value: props.stats.nb_sous_projets,
      label: 'Sous-projets',
      type: 'infos',
      visual: [45, 65, 80, 55, 70, 85, 90, 75, 60]
    },
    {
      key: 'completed',
      icon: '🎯',
      value: props.stats.sous_projets_complets,
      label: 'Terminés',
      type: 'success',
      visual: [30, 50, 70, 85, 90, 95, 100, 90, 80]
    }
  ]
})

const clientsData = computed(() => {
  if (!props.stats?.projets_par_client) return []
  
  const colors = [
    { color: '#667eea', colorEnd: '#764ba2' },
    { color: '#f093fb', colorEnd: '#f5576c' },
    { color: '#4facfe', colorEnd: '#00f2fe' },
    { color: '#43e97b', colorEnd: '#38f9d7' },
    { color: '#fa709a', colorEnd: '#fee140' }
  ]
  
  const total = props.stats.projets_par_client.reduce((sum, client) => sum + client.count, 0)
  
  let currentOffset = 0
  
  return props.stats.projets_par_client.map((client, index) => {
    const percentage = Math.round((client.count / total) * 100)
    const dashArray = (client.count / total) * 440
    const offset = -currentOffset
    
    currentOffset += dashArray
    
    return {
      ...client,
      percentage,
      dashArray,
      offset,
      ...colors[index % colors.length]
    }
  })
})

const animateCard = (event) => {
  const card = event.currentTarget
  card.style.transform = 'scale(1.05) rotateY(5deg)'
  setTimeout(() => {
    card.style.transform = 'scale(1) rotateY(0deg)'
  }, 300)
}
</script>

<template>
  <div class="stats-view">
    <div v-if="stats" class="stats-content">
      <div class="metrics-grid">
        <div 
          v-for="metric in metricsData" 
          :key="metric.key"
          class="metric-card"
          :class="metric.type"
          @mouseenter="animateCard($event)"
        >
          <div class="metric-header">
            <div class="metric-icon">{{ metric.icon }}</div>
          </div>
          
          <div class="metric-value">
            <CounterAnimation :value="metric.value" :duration="1000" />
            <span class="metric-unit" v-if="metric.unit">{{ metric.unit }}</span>
          </div>
          
          <div class="metric-label">{{ metric.label }}</div>
          
          <div class="metric-visual" v-if="metric.visual">
            <div class="mini-chart">
              <div 
                v-for="(bar, index) in metric.visual" 
                :key="index"
                class="chart-bar":class="metric.type"
                :style="`height: ${bar}%; animation-delay: ${index * 0.1}s`"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <div class="client-section">
        <div class="section-header">
          <h3>Répartition par Client</h3>
        </div>
        
        <div class="client-visualization">
          <div class="bars-chart">
            <div 
              v-for="(client, index) in clientsData" 
              :key="client.client"
              class="client-bar-container"
              :style="`animation-delay: ${index * 0.1}s`"
            >
              <div class="client-info">
                <div class="client-avatar">{{ client.client.charAt(0).toUpperCase() }}{{ client.client.charAt(1).toLowerCase() }}</div>
                <div class="client-details">
                  <div class="client-name">{{ client.client }}</div>
                  <div class="client-count">{{ client.count }} projets</div>
                </div>
              </div>
              
              <div class="bar-container">
                <div 
                  class="bar-fill animated" 
                  :style="`width: ${client.percentage}%`"
                ></div>
                <div class="bar-percentage">{{ client.percentage }}%</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-illustration">📊</div>
      <h3>Aucune donnée disponible</h3>
      <p>Les statistiques apparaîtront ici une fois que vous aurez des projets.</p>
    </div>
  </div>
</template>

<style scoped>
.stats-view {
  height: 85%;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 30px;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.1);
}

.stats-content {
  display: flex;
  flex-direction: column;
  gap: 30px;
  height: 100%;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.metric-card {
  background: white;
  border-radius: 12px;
  padding: 15px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.metric-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #7c66ea, #d72fe0);
}

.metric-card.success::before {
  background: linear-gradient(90deg, #10b981, #34d399);
}

.metric-card.infos::before {
  background: linear-gradient(90deg, #3be3f6, #5ca4f6);
}

.metric-card:hover {
  transform: translateY(-5px) scale(1.02);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.metric-icon {
  font-size: 1.8rem;
  padding: 10px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 12px;
}

.metric-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: #1f2937;
  display: flex;
  align-items: baseline;
  gap: 5px;
}

.metric-unit {
  font-size: 1rem;
  color: #6b7280;
  font-weight: 500;
}

.metric-label {
  color: #6b7280;
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 5px;
}

.metric-visual {
  height: 40px;
  display: flex;
  align-items: end;
}

.mini-chart {
  display: flex;
  gap: 3px;
  height: 100%;
  width: 100%;
}

.chart-bar {
  flex: 1;
  border-radius: 2px 2px 0 0;
  min-height: 4px;
  animation: growUp 1s ease-out forwards;
  transform-origin: bottom;
  transform: scaleY(0);
}

.chart-bar.primary {
  background: linear-gradient(to top, #7c66ea, #d72fe0);
}

.chart-bar.infos {
  background: linear-gradient(to top, #3be3f6, #5ca4f6);
}

.chart-bar.success {
  background: linear-gradient(to top, #10b981, #34d399);
}

@keyframes growUp {
  to { transform: scaleY(1); }
}

.client-section {
  background: white;
  border-radius: 20px;
  padding: 25px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-header h3 {
  font-size: 1.3rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.bars-chart {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.client-bar-container {
  animation: slideInLeft 0.6s ease-out forwards;
  opacity: 0;
  transform: translateX(-30px);
}

@keyframes slideInLeft {
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.client-info {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}

.client-avatar {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #f59e0b, #ecc547);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 1.2rem;
}

.client-details {
  flex: 1;
}

.client-name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 2px;
}

.client-count {
  font-size: 0.9rem;
  color: #6b7280;
}

.bar-container {
  display: flex;
  align-items: center;
  gap: 15px;
  height: 12px;
  background: #f3f4f6;
  border-radius: 6px;
  position: relative;
  overflow: hidden;
}

.bar-percentage {
  font-size: 0.75rem;
  font-weight: 900;
  color: #222222; 
  text-shadow: 0 1px 2px rgba(0,0,0,0.5); 
  position: absolute;
  right: 10px;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(135deg, #f59e0b, #fcd34d);
}
</style>