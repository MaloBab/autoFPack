<template>
  <div ref="container" class="inline-block w-full relative">
    <input
      ref="input"
      :value="displayValue"
      @input="onInput"
      @focus="showDropdown = true"
      @blur="handleBlur"
      @keydown.down.prevent="nextOption"
      @keydown.up.prevent="prevOption"
      @keydown.enter.prevent="selectHighlighted"
      @keydown.esc.prevent="showDropdown = false"
      @keyup.enter="$emit('keyup.enter')"
      class="styled-input"
      autocomplete="off"
      spellcheck="false"
    />

    <select ref="selectEl" v-show="false">
      <slot />
    </select>

    <Teleport to="body">
      <ul
        v-if="showDropdown && filteredOptions.length"
        class="dropdown-native-style"
        :style="dropdownStyle"
        @mousedown.prevent
      >
        <li
          v-for="(option, index) in filteredOptions"
          :key="option.value"
          :class="['dropdown-item', 
            index === highlightedIndex || index === hoveredIndex ? 'dropdown-item--active' : ''
          ]"
          @mousedown.prevent="selectOption(option)"
          @mouseenter="onMouseEnter(index, option.label)"
          @mouseleave="onMouseLeave"
        >
          {{ option.label }}
        </li>
      </ul>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'

const props = defineProps({
  modelValue: String,
})
const emit = defineEmits(['update:modelValue', 'keyup.enter'])

const search = ref('')
const displayValue = ref('')
const previousInput = ref('')
const showDropdown = ref(false)
const highlightedIndex = ref(0)
const hoveredIndex = ref(null)
const selectEl = ref(null)
const input = ref(null)

const dropdownStyle = ref({
  position: 'fixed',
  left: '0px',
  top: '0px',
  width: '0px',
  zIndex: 9999,
  display: 'none',
})

const options = ref([])

onMounted(() => {
  options.value = [...selectEl.value.options].map((opt) => ({
    value: opt.value,
    label: opt.textContent,
  }))
  const selected = options.value.find((o) => o.value === props.modelValue)
  if (selected) {
    search.value = selected.label
    displayValue.value = selected.label
  }

  updateDropdownPosition()
  window.addEventListener('scroll', updateDropdownPosition, true)
  window.addEventListener('resize', updateDropdownPosition)

  document.addEventListener('mousedown', onClickOutside)
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', updateDropdownPosition, true)
  window.removeEventListener('resize', updateDropdownPosition)
  document.removeEventListener('mousedown', onClickOutside)
})


watch(showDropdown, (visible) => {
  if (visible) {
    search.value = ''
    displayValue.value = ''
    nextTick(() => {
      updateDropdownPosition()
    })
  }
})

watch(() => props.modelValue, (val) => {
  const selected = options.value.find((o) => o.value === val)
  if (selected) {
    search.value = selected.label
    displayValue.value = selected.label
  }
})

watch(search, (val) => {
  highlightedIndex.value = 0
  if (hoveredIndex.value === null) {
    previousInput.value = val
    displayValue.value = val
  }
})

const filteredOptions = computed(() => {
  return options.value.filter((opt) =>
    opt.label.toLowerCase().includes(search.value.toLowerCase())
  )
})

function onInput(e) {
  search.value = e.target.value
  displayValue.value = e.target.value
}

function onMouseEnter(index, label) {
  hoveredIndex.value = index
  displayValue.value = label
}

function onMouseLeave() {
  hoveredIndex.value = null
  displayValue.value = previousInput.value
}

function updateDropdownPosition() {
  if (showDropdown.value && input.value) {
    const rect = input.value.getBoundingClientRect()
    dropdownStyle.value = {
      ...dropdownStyle.value,
      left: `${rect.left}px`,
      top: `${rect.bottom}px`,
      width: `${rect.width}px`,
      display: 'block',
    }
  }
}

function selectOption(option) {
  search.value = option.label
  displayValue.value = option.label
  emit('update:modelValue', option.value)
  showDropdown.value = false
}

function handleBlur() {
  setTimeout(() => (showDropdown.value = false), 100)
}

function nextOption() {
  if (highlightedIndex.value < filteredOptions.value.length - 1) {
    highlightedIndex.value++
  } else {
    highlightedIndex.value = 0
  }
  scrollToHighlighted()
}

function prevOption() {
  if (highlightedIndex.value > 0) {
    highlightedIndex.value--
  } else {
    highlightedIndex.value = filteredOptions.value.length - 1
  }
  scrollToHighlighted()
}

function selectHighlighted() {
  const option = filteredOptions.value[highlightedIndex.value]
  if (option) selectOption(option)
}

function scrollToHighlighted() {
  nextTick(() => {
    const items = document.querySelectorAll('.dropdown-item')
    const el = items[highlightedIndex.value]
    if (el) el.scrollIntoView({ block: 'nearest' })
  })
}

function onClickOutside(e) {
  const clickedInside = input.value?.contains(e.target) || 
    document.querySelector('.dropdown-native-style')?.contains(e.target)
  if (!clickedInside) {
    const valid = filteredOptions.value.some(opt => opt.label === search.value)
    if (!valid) {
      search.value = ''
      displayValue.value = ''
      emit('update:modelValue', '')
    } else {
      displayValue.value = search.value
    }
    showDropdown.value = false
  }
}
</script>

<style scoped>
.styled-input {
  border: 1px solid #bbb;
  border-radius: 4px;
  padding: 0.3rem 0.5rem;
  font-size: 1rem;
  font-family: inherit;
  background: #f9fafb;
  color: #222;
  outline: none;
  transition: border 0.2s;
  width: 100%;
  min-width: 60px;
  max-width: 200px;
  box-sizing: border-box;
}
.styled-input:focus {
  border: 1.5px solid #2563eb;
  background: #fff;
}

.dropdown-native-style {
  position: fixed;
  background: #fff;
  border: 1px solid #bbb;
  border-radius: 4px;
  max-height: 220px;
  overflow-y: auto;
  overflow-x: hidden;
  z-index: 9999;
  font-size: 1rem;
  font-family: inherit;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
  padding: 0;
  margin: 4px 0 0 0;
  list-style: none;
  white-space: nowrap;
}

.dropdown-item {
  padding: 0.4rem 0.6rem;
  white-space: nowrap;
  cursor: pointer;
  background: transparent;
  color: #222;
  transition: background-color 0.2s, color 0.2s;
  user-select: none;
}

.dropdown-item--active {
  background-color: #2563eb;
  color: white;
}
</style>
