<script setup lang="ts">
import { ref, watch, nextTick, defineProps, defineEmits } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    required: false, 
    default: ''           
  },
  suggestions: {
    type: Array as () => string[],
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

const inputValue = ref(String(props.modelValue ?? ''))
const inputRef = ref<HTMLInputElement | null>(null)
const isUserTyping = ref(true) 
const lastKey = ref<string>('')


function completeInput(userInput: string) {
    if (typeof props.modelValue === 'number') {
      inputValue.value = userInput
      emit('update:modelValue', userInput)
      return
  }

  const match = props.suggestions.find(s => typeof s === 'string' && 
    s.toLowerCase().startsWith(userInput.toLowerCase()) &&
    s.length > userInput.length
  )

  if (match && inputRef.value) {
    const preservedUserInput = userInput

    const completion = match.slice(userInput.length)

    const finalText = preservedUserInput + completion
    inputRef.value.value = finalText
    inputValue.value = finalText
    emit('update:modelValue', finalText)

    nextTick(() => {
      inputRef.value?.setSelectionRange(preservedUserInput.length, finalText.length)
    })
  } else {
    inputValue.value = userInput
    emit('update:modelValue', userInput)
  }
}


function onKeyDown(e: KeyboardEvent) {
  lastKey.value = e.key

  if (e.key === 'Tab' && inputRef.value) {
    if (inputRef.value.selectionStart !== inputRef.value.selectionEnd) {
      e.preventDefault()
      isUserTyping.value = false
      inputRef.value.setSelectionRange(inputRef.value.value.length, inputRef.value.value.length)
      emit('update:modelValue', inputRef.value.value)
    }
  } else if (e.key === 'Escape') {
    e.preventDefault()
    isUserTyping.value = true
    if (inputRef.value) {
      const val = inputValue.value
      const pos = inputRef.value.selectionStart ?? val.length
      inputValue.value = val.slice(0, pos)
      emit('update:modelValue', inputValue.value)
      nextTick(() => {
        inputRef.value?.setSelectionRange(inputValue.value.length, inputValue.value.length)
      })
    }
  }
}

function onInput(e: Event) {
  const val = (e.target as HTMLInputElement).value
  isUserTyping.value = true

  if (lastKey.value === 'Backspace' || lastKey.value === 'Delete') {
    inputValue.value = val
    emit('update:modelValue', val)
    return
  }

  completeInput(val)
}

watch(() => props.modelValue, (val) => {
  if (!isUserTyping.value) {
    inputValue.value = String(val)
  }
})
</script>

<template>
  <input
    ref="inputRef"
    type="text"
    :value="inputValue"
    @input="onInput"
    @keydown="onKeyDown"
    autocomplete="off"
  />
</template>

<style scoped>
input {
  border: 1px solid #bbb;
  border-radius: 4px;
  padding: 0.3rem 0.5rem;
  font-size: 1rem;
  margin-top: 1%;
  font-family: inherit;
  background: #f9fafb;
  color: #222;
  outline: none;
  transition: border 0.2s;
  width: 90%;
  min-width: 60px;
  max-width: 200px;
}
input:focus{
  border: 1.5px solid #2563eb;
  background: #fff;
}
</style>