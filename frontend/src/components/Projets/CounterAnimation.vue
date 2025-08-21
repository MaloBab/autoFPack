<template>
  <span class="counter">{{ displayValue }}</span>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'

const props = defineProps({
  value: {
    type: Number,
    default: 0
  },
  duration: {
    type: Number,
    default: 1000
  }
})

const displayValue = ref(0)

const animateValue = (start, end, duration) => {
  const startTime = Date.now()
  
  const animate = () => {
    const now = Date.now()
    const elapsed = now - startTime
    const progress = Math.min(elapsed / duration, 1)
    
    // Easing function (ease-out)
    const easedProgress = 1 - Math.pow(1 - progress, 3)
    
    displayValue.value = Math.round(start + (end - start) * easedProgress)
    
    if (progress < 1) {
      requestAnimationFrame(animate)
    }
  }
  
  requestAnimationFrame(animate)
}

onMounted(() => {
  animateValue(0, props.value, props.duration)
})

watch(() => props.value, (newValue, oldValue) => {
  animateValue(oldValue || 0, newValue, props.duration)
})
</script>

<style scoped>
.counter {
  display: inline-block;
  font-variant-numeric: tabular-nums;
}
</style>