<!-- Card.vue -->
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'

interface SpecialAction {
  label: string
  onClick: (row: Record<string, any>) => void
  icon?: string
}

const props = defineProps<{
  row: Record<string, any>
  columns: any[]
  specialActions?: SpecialAction[]
  compact?: boolean
  cardIndex?: number
  baseColor?: string // Couleur de base en HSL (ex: "210, 65, 70" pour hsl(210, 65%, 70%))
}>()

// Watcher pour forcer la mise à jour du style quand compact change
const forceUpdate = ref(0)
watch(() => props.compact, () => {
  forceUpdate.value++
}, { immediate: true })

const emit = defineEmits(['edit', 'delete', 'duplicate', 'export'])

const expanded = ref(false)
const menuOpen = ref(false)
const cardRef = ref<HTMLElement>()
const menuButtonRef = ref<HTMLElement>()
const isHovered = ref(false)
const isPressed = ref(false)
const ripples = ref<Array<{ id: number, x: number, y: number }>>([])
const rippleCounter = ref(0)
const menuPosition = ref({ top: 0, left: 0, right: 'auto' })

const mainTitle = computed(() => {
  const titleFields = ['nom', 'name', 'title']
  for (const field of titleFields) {
    if (props.row[field]) return String(props.row[field])
  }
  // Prendre la première valeur non-id
  const keys = props.columns.filter(col => col !== 'id')
  return props.row[keys[0]] || 'Sans titre'
})

const mainDescription = computed(() => {
  const descFields = ['description', 'desc', 'details', 'note', 'commentaire']
  for (const field of descFields) {
    if (props.row[field]) return String(props.row[field])
  }
  return ''
})

const primaryFields = computed(() => {
  const priorityFields = ['reference', 'nom', 'name', 'prix', 'price', 'status']
  const result = [] as any[]
  
  for (const field of priorityFields) {
    if (props.columns.includes(field) && props.row[field] != null && result.length < 4) {
      result.push({
        label: formatLabel(field),
        value: props.row[field],
        field: field
      })
    }
  }
  
  if (result.length < 4) {
    const remaining = props.columns.filter(col => 
      col !== 'id' && 
      !priorityFields.includes(col) && 
      !['description', 'desc', 'details', 'note', 'commentaire'].includes(col) &&
      props.row[col] != null
    ).slice(0, 4 - result.length)
    
    remaining.forEach(field => {
      result.push({
        label: formatLabel(field),
        value: props.row[field],
        field: field
      })
    })
  }
  
  return result
})

// Tous les champs à afficher dans la vue étendue (sauf titre et description)
const allExpandedFields = computed(() => {
  const displayed = new Set(['id'])
  const titleField = props.columns.find(col => props.row[col] === mainTitle.value)
  if (titleField) displayed.add(titleField)
  
  // Exclure aussi les champs de description
  const descFields = ['description', 'desc', 'details', 'note', 'commentaire']
  descFields.forEach(field => displayed.add(field))
  
  return props.columns
    .filter(col => !displayed.has(col) && props.row[col] != null)
    .map(col => ({
      label: formatLabel(col),
      value: props.row[col],
      field: col
    }))
})

// Déterminer si un champ doit prendre plus de place
const isWideField = (field: string): boolean => {
  const wideFields = ['url', 'email', 'adresse', 'address', 'commentaire', 'note', 'remarque']
  return wideFields.includes(field.toLowerCase()) || String(props.row[field] || '').length > 50
}

// Déterminer si une valeur est longue
const isLongValue = (value: any): boolean => {
  return String(value || '').length > 30
}

// Formatage spécial pour la vue étendue
const formatExpandedValue = (value: any, field: string): string => {
  if (value === null || value === undefined) return '—'
  
  const str = String(value)
  
  // Pour les URLs, emails, etc., on peut être plus généreux
  if (field.toLowerCase().includes('url') || field.toLowerCase().includes('email')) {
    return str.length > 80 ? str.slice(0, 80) + '…' : str
  }
  
  // Pour les champs de texte long
  if (isWideField(field)) {
    return str.length > 120 ? str.slice(0, 120) + '…' : str
  }
  
  // Pour les autres champs
  return str.length > 50 ? str.slice(0, 50) + '…' : str
}

// Couleurs variées pour les dots
const getFieldColor = (index: number): string => {
  const baseHsl = accentColor.value.match(/hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/)
  if (baseHsl) {
    const baseHue = parseInt(baseHsl[1])
    const hueShift = (index * 25) % 360
    const newHue = (baseHue + hueShift) % 360
    return `hsl(${newHue}, 60%, 65%)`
  }
  return accentColor.value
}

const avatarText = computed(() => {
  const title = mainTitle.value
  const words = title.split(' ')
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }
  return title.slice(0, 2).toUpperCase()
})

// Système de couleurs progressif et uniforme
const accentColor = computed(() => {
  const cardIndex = props.cardIndex || 0
  
  if (props.baseColor) {
    // Utiliser la couleur de base fournie en prop
    const colorParts = props.baseColor.split(',').map(part => parseFloat(part.trim()))
    if (colorParts.length === 3) {
      const [h, s, l] = colorParts
      
      // Variation progressive légère basée sur cardIndex
      const hueVariation = (cardIndex % 7) * 5 - 10 // De -10 à +20
      const finalHue = (h + hueVariation + 360) % 360
      
      // Variation très légère de saturation et luminosité
      const saturation = Math.max(20, Math.min(90, s + (cardIndex % 3) * 2 - 2)) // ±2
      const lightness = Math.max(30, Math.min(85, l + (cardIndex % 4) * 2 - 3)) // ±3
      
      return `hsl(${finalHue}, ${saturation}%, ${lightness}%)`
    }
  }
  
  // Fallback : système de couleurs par défaut (bleu)
  const baseHue = 210
  const hueVariation = (cardIndex % 7) * 8 - 24 // De -24 à +24
  const finalHue = (baseHue + hueVariation + 360) % 360
  
  const saturation = 65 + (cardIndex % 3) * 5 // 65, 70, 75
  const lightness = 68 + (cardIndex % 4) * 3 // 68, 71, 74, 77
  
  return `hsl(${finalHue}, ${saturation}%, ${lightness}%)`
})

const gradientColor = computed(() => {
  const match = accentColor.value.match(/hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/)
  if (match) {
    const h = parseInt(match[1])
    const s = parseInt(match[2])
    const l = parseInt(match[3])
    // Gradient plus subtil
    return `hsl(${(h + 15) % 360}, ${Math.max(s - 10, 45)}%, ${Math.min(l + 8, 85)}%)`
  }
  return accentColor.value
})

const formatLabel = (field: string): string => {
  return field
    .replace(/_/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

const formatValue = (value: any, maxLength = 25) => {
  if (value === null || value === undefined) return '—'
  const str = String(value)
  return str.length > maxLength ? str.slice(0, maxLength - 1) + '…' : str
}

const createRipple = (event: MouseEvent) => {
  if (!cardRef.value) return
  
  const rect = cardRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  const ripple = {
    id: rippleCounter.value++,
    x,
    y
  }
  
  ripples.value.push(ripple)
  
  setTimeout(() => {
    const index = ripples.value.findIndex(r => r.id === ripple.id)
    if (index > -1) {
      ripples.value.splice(index, 1)
    }
  }, 600)
}

const handleCardClick = (event: MouseEvent) => {
  createRipple(event)
  setTimeout(() => {
    expanded.value = !expanded.value
  }, 100)
}

const handleMouseDown = () => {
  isPressed.value = true
}

const handleMouseUp = () => {
  isPressed.value = false
}

const handleMouseEnter = () => {
  isHovered.value = true
}

const handleMouseLeave = () => {
  isHovered.value = false
  isPressed.value = false
}

const calculateMenuPosition = () => {
  if (!menuButtonRef.value) return
  
  const buttonRect = menuButtonRef.value.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  
  // Position par défaut : en dessous à droite du bouton
  let top = buttonRect.bottom + 8
  let left = buttonRect.right - 180 // 180px = largeur approximative du menu
  let right = 'auto'
  
  // Ajuster si le menu dépasse à droite
  if (left < 8) {
    left = buttonRect.left
  }
  
  // Ajuster si le menu dépasse en bas
  if (top + 200 > viewportHeight) { // 200px = hauteur approximative du menu
    top = buttonRect.top - 200 - 8
  }
  
  menuPosition.value = { top, left, right }
}

const toggleMenu = async (e: Event) => {
  e.stopPropagation()
  
  if (!menuOpen.value) {
    await nextTick()
    calculateMenuPosition()
  }
  
  menuOpen.value = !menuOpen.value
}

const handleClickOutside = (e: Event) => {
  if (menuButtonRef.value && !menuButtonRef.value.contains(e.target as Node)) {
    const menu = document.querySelector('.floating-menu') as HTMLElement
    if (menu && !menu.contains(e.target as Node)) {
      menuOpen.value = false
    }
  }
}

const handleResize = () => {
  if (menuOpen.value) {
    calculateMenuPosition()
  }
}

const handleScroll = () => {
  if (menuOpen.value) {
    menuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('resize', handleResize)
  window.addEventListener('scroll', handleScroll, true)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('scroll', handleScroll, true)
})
</script>

<template>
  <article
    ref="cardRef"
    class="modern-card"
    :class="{ 
      expanded, 
      compact: compact || forceUpdate >= 0, 
      hovered: isHovered, 
      pressed: isPressed 
    }"
    :style="{ 
      '--accent-color': accentColor,
      '--gradient-color': gradientColor,
      '--force-update': forceUpdate
    }"
    @click="handleCardClick"
    @mousedown="handleMouseDown"
    @mouseup="handleMouseUp"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <!-- Effets de ripple -->
    <div class="ripple-container">
      <div
        v-for="ripple in ripples"
        :key="ripple.id"
        class="ripple"
        :style="{ left: ripple.x + 'px', top: ripple.y + 'px' }"
      />
    </div>

    <!-- Gradient d'arrière-plan -->
    <div class="gradient-bg"></div>
    
    <!-- Particules flottantes -->
    <div class="floating-particles">
      <div class="particle" v-for="i in 6" :key="i"></div>
    </div>
    
    <!-- En-tête avec avatar flottant -->
    <header class="card-header">
      <div class="avatar-container">
        <div class="avatar">
          <span class="avatar-text">🧩</span>
          <div class="avatar-ring"></div>
        </div>
        <div class="status-dot"></div>
      </div>
      
      <div class="header-content">
        <h3 class="card-title">
          {{ formatValue(mainTitle, 40) }}
        </h3>
        <p v-if="mainDescription && !compact" class="card-description">
          {{ formatValue(mainDescription, 60) }}
        </p>
      </div>
      
      <div class="header-actions" @click.stop>
        <button 
          ref="menuButtonRef"
          class="action-btn menu-btn"
          :class="{ active: menuOpen }"
          @click="toggleMenu"
          title="Actions"
        >
          <div class="menu-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </button>
      </div>
    </header>
    
    <transition name="expand">
      <div v-if="expanded && !compact" class="expanded-section">
        <div class="glass-panel">
          <!-- Description complète si elle existe -->
          <div v-if="mainDescription" class="description-section">
            <div class="description-content">
              <div class="description-icon">📝</div>
              <p class="description-text">{{ mainDescription }}</p>
            </div>
          </div>

          <!-- Grille compacte pour tous les champs -->
          <div v-if="allExpandedFields.length" class="compact-grid">
            <div 
              v-for="(item, index) in allExpandedFields" 
              :key="item.field"
              class="field-item"
              :class="{ 'field-wide': isWideField(item.field) }"
              :style="{ '--delay': index * 0.03 + 's' }"
            >
              <div class="field-dot" :style="{ background: getFieldColor(index) }"></div>
              <div class="field-content">
                <span class="field-label">{{ item.label }}</span>
                <span class="field-value" :class="{ 'field-long': isLongValue(item.value) }">
                  {{ formatExpandedValue(item.value, item.field) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </article>

  <!-- Menu flottant détaché (Teleport vers le body) -->
  <Teleport to="body">
    <transition name="menu">
      <div 
        v-if="menuOpen" 
        class="floating-menu-overlay"
        :style="{
          top: menuPosition.top + 'px',
          left: menuPosition.left + 'px',
          right: menuPosition.right
        }"
      >
        <div class="floating-menu">
          <div class="menu-item" @click="$emit('edit', row); menuOpen = false">
            <div class="menu-icon">✨</div>
            <span>Modifier</span>
          </div>
          <div class="menu-item" @click="$emit('duplicate', row); menuOpen = false">
            <div class="menu-icon">📋</div>
            <span>Dupliquer</span>
          </div>
          <div class="menu-item" @click="$emit('export', row); menuOpen = false">
            <div class="menu-icon">🚀</div>
            <span>Exporter</span>
          </div>
          <div class="menu-divider"></div>
          <div class="menu-item danger" @click="$emit('delete', row); menuOpen = false">
            <div class="menu-icon">🗑️</div>
            <span>Supprimer</span>
          </div>
          
          <template v-if="specialActions?.length">
            <div class="menu-divider"></div>
            <div
              v-for="action in specialActions"
              :key="action.label"
              @click="action.onClick(row); menuOpen = false"
              class="menu-item special"
            >
              <div class="menu-icon">{{ action.icon || '⚡' }}</div>
              <span>{{ action.label }}</span>
            </div>
          </template>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.modern-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  overflow: hidden;
  position: relative;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 
    0 4px 20px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  max-width: 400px;
  user-select: none;
}

.modern-card.hovered {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.15),
    0 0 0 1px var(--accent-color),
    0 0 30px rgba(var(--accent-color), 0.2);
}

.modern-card.pressed {
  transform: translateY(-6px) scale(0.98);
}

.ripple-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.ripple {
  position: absolute;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--accent-color) 0%, transparent 70%);
  transform: translate(-50%, -50%);
  animation: ripple 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes ripple {
  to {
    transform: translate(-50%, -50%) scale(15);
    opacity: 0;
  }
}

.gradient-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    135deg,
    var(--accent-color) 0%,
    var(--gradient-color) 50%,
    transparent 100%
  );
  opacity: 0.03;
  transition: opacity 0.3s ease;
  z-index: 0;
}

.modern-card.hovered .gradient-bg {
  opacity: 0.08;
}

.floating-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.particle {
  position: absolute;
  width: 3px;
  height: 3px;
  background: var(--accent-color);
  border-radius: 50%;
  opacity: 0.1;
  animation: float 8s infinite linear;
}

.particle:nth-child(1) { left: 10%; animation-delay: -0s; }
.particle:nth-child(2) { left: 20%; animation-delay: -1s; }
.particle:nth-child(3) { left: 30%; animation-delay: -2s; }
.particle:nth-child(4) { left: 70%; animation-delay: -3s; }
.particle:nth-child(5) { left: 80%; animation-delay: -4s; }
.particle:nth-child(6) { left: 90%; animation-delay: -5s; }

@keyframes float {
  0% { transform: translateY(100vh) rotate(0deg); }
  100% { transform: translateY(-20px) rotate(360deg); }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  position: relative;
  z-index: 2;
}

.avatar-container {
  position: relative;
  flex-shrink: 0;
}

.avatar {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, var(--accent-color), var(--gradient-color));
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.modern-card.hovered .avatar {
  transform: rotate(5deg) scale(1.1);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
}

.avatar-text {
  color: white;
  font-weight: 700;
  font-size: 1.1rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.avatar-ring {
  position: absolute;
  inset: -4px;
  border: 2px solid transparent;
  border-radius: 20px;
  background: linear-gradient(135deg, var(--accent-color), var(--gradient-color)) border-box;
  mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  opacity: 0;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.1); }
}

.header-content {
  flex: 1;
  min-width: 0;
}

.card-title {
  margin: 0 0 6px 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.3;
  background: linear-gradient(135deg, #1f2937, var(--accent-color));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.card-description {
  margin: 0;
  font-size: 0.9rem;
  color: #6b7280;
  line-height: 1.4;
}

.header-actions {
  display: flex;
  gap: 8px;
  position: relative;
  z-index: 10;
}

.action-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.action-btn:hover {
  background: var(--accent-color);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

.menu-dots {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.menu-dots span {
  width: 4px;
  height: 4px;
  background: currentColor;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.menu-btn.active .menu-dots span {
  background: white;
}

/* Menu flottant détaché */
.floating-menu-overlay {
  position: fixed;
  z-index: 9999;
  pointer-events: none;
}

.floating-menu {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.15),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  min-width: 180px;
  overflow: hidden;
  pointer-events: auto;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
}

.menu-item:hover {
  background: rgba(var(--accent-color), 0.1);
  border-left-color: var(--accent-color);
}

.menu-item.danger:hover {
  background: rgba(239, 68, 68, 0.1);
  border-left-color: #ef4444;
  color: #ef4444;
}

.menu-item.special {
  background: linear-gradient(135deg, var(--accent-color), var(--gradient-color));
  color: white;
}

.menu-icon {
  width: 20px;
  text-align: center;
}

.menu-divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.1);
  margin: 4px 0;
}

.expanded-section {
  position: relative;
  z-index: 2;
}

.glass-panel {
  margin: 0 20px 20px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 16px;
  max-height: 400px;
  overflow-y: auto;
}

/* Section description complète */
.description-section {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
}

.description-content {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.description-icon {
  font-size: 1rem;
  opacity: 0.7;
  margin-top: 2px;
  flex-shrink: 0;
}

.description-text {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.5;
  color: #374151;
  font-weight: 500;
}

/* Grille compacte pour tous les champs */
.compact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 8px;
  align-items: start;
}

.field-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.2s ease;
  animation: fadeInUp 0.4s ease var(--delay) both;
  min-height: 44px;
}

.field-item.field-wide {
  grid-column: 1 / -1; /* Prend toute la largeur */
}

.field-item:hover {
  background: rgba(255, 255, 255, 0.7);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.field-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
  box-shadow: 0 0 6px currentColor;
}

.field-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.field-label {
  font-size: 0.7rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  line-height: 1.2;
}

.field-value {
  font-size: 0.85rem;
  font-weight: 500;
  color: #1f2937;
  line-height: 1.3;
  word-break: break-word;
}

.field-value.field-long {
  font-size: 0.8rem;
  line-height: 1.4;
}

/* Scrollbar personnalisée pour la glass-panel */
.glass-panel::-webkit-scrollbar {
  width: 4px;
}

.glass-panel::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
}

.glass-panel::-webkit-scrollbar-thumb {
  background: var(--accent-color);
  border-radius: 2px;
  opacity: 0.5;
}

.glass-panel::-webkit-scrollbar-thumb:hover {
  opacity: 0.8;
}

/* Transitions */
.menu-enter-active, .menu-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.menu-enter-from {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}

.menu-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}

.expand-enter-active, .expand-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.expand-enter-from, .expand-leave-to {
  opacity: 0;
  max-height: 0;
  transform: scaleY(0);
  transform-origin: top;
}

.expand-enter-to, .expand-leave-from {
  opacity: 1;
  max-height: 1000px;
  transform: scaleY(1);
}

/* Mode compact */
.compact {
  max-width: 280px;
}

.compact .card-header {
  padding: 16px;
}

.compact .avatar {
  width: 48px;
  height: 48px;
  border-radius: 12px;
}

.compact .card-title {
  font-size: 1.1rem;
}

.compact .action-btn {
  width: 36px;
  height: 36px;
}
</style>