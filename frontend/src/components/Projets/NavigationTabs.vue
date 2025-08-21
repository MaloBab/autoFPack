<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount, watch } from 'vue'

const props = defineProps({
  activeTab: {
    type: String,
    required: true
  }
})

defineEmits(['tab-change'])

const tabs = [
  { key: 'stats', label: 'Statistiques', icon: '📊' },
  { key: 'projets', label: 'Projets', icon: '📁' }
]

const indicatorStyle = ref({
  transform: 'translateX(0px)',
  width: '0px'
})

const updateIndicator = async () => {
  await nextTick()
  const container = document.querySelector('.tabs-wrapper')
  const activeButton = document.querySelector('.tab-button.active')
  
  if (container && activeButton) {
    const containerRect = container.getBoundingClientRect()
    const buttonRect = activeButton.getBoundingClientRect()
    
    const translateX = buttonRect.left - containerRect.left
    const width = buttonRect.width
    
    indicatorStyle.value = {
      transform: `translateX(${translateX}px)`,
      width: `${width}px`
    }
  }
}

watch(() => props.activeTab, updateIndicator)

onMounted(() => {
  updateIndicator()
  window.addEventListener('resize', updateIndicator) 
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateIndicator)
})
</script>

<template>
  <nav class="navigation-tabs">
    <div class="tabs-container">
      <div class="tabs-wrapper">
        <button 
          v-for="tab in tabs" 
          :key="tab.key"
          :class="['tab-button', { active: activeTab === tab.key }]"
          @click="$emit('tab-change', tab.key)"
          :disabled="tab.disabled"
        >
          <div class="tab-content">
            <div class="tab-icon" v-html="tab.icon"></div>
            <span class="tab-text">{{ tab.label }}</span>
          </div>
          <div class="tab-indicator"></div>
        </button>
      </div>
      
      <!-- Indicateur de fond mobile -->
      <div 
        class="background-indicator"
        :style="indicatorStyle"
      ></div>
    </div>
  </nav>
</template>



<style scoped>
.navigation-tabs {
  padding: 0;
}

.tabs-container {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 1px;
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.tabs-wrapper {
  display: flex;
  position: relative;
  z-index: 2;
}

.background-indicator {
  width: calc(100% / 2);
  position: absolute;
  top: 6px;
  bottom: 6px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
  z-index: 1;
}

.tab-button {
  flex: 1;
  background: none;
  border: none;
  padding: 16px 24px;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  z-index: 2;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 600;
}

.tab-button:hover:not(.active) {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.1);
}

.tab-button.active {
  color: #ffffff;
}

.tab-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tab-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  position: relative;
}

.tab-icon {
  font-size: 1.2rem;
  transition: transform 0.3s ease;
}

.tab-button.active .tab-icon {
  transform: scale(1.1);
}

.tab-text {
  font-size: 0.95rem;
  white-space: nowrap;
}



.tab-indicator {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  width: 6px;
  height: 6px;
  background: #ffffff;
  border-radius: 50%;
  opacity: 0;
  transition: all 0.3s ease;
}

.tab-button.active .tab-indicator {
  opacity: 1;
  transform: translateX(-50%) scale(1);
}

</style>