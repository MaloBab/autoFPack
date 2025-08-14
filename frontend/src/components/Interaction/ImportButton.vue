<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { showToast } from '../../composables/useToast'

const props = defineProps({
  addUrl: { type: String, required: true },
  label: { type: String, default: 'Importer' },
})

const emit = defineEmits(['import-success'])

const isImporting = ref(false)
const showOptions = ref(false)
const selectedFile = ref<File | null>(null)
const wrapper = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

function onChooseFile(url: string) {
  showOptions.value = false
  selectedFile.value = null
  nextTick(() => {
    if (fileInput.value) {
      fileInput.value.setAttribute('data-url', url)
      fileInput.value.value = ''
      fileInput.value.click()
    }
  })
}

async function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const url = target.getAttribute('data-url')

  if (target.files && target.files.length > 0 && url) {
    selectedFile.value = target.files[0]
    isImporting.value = true

    const formData = new FormData()
    formData.append('file', selectedFile.value)

    const res = await fetch(url, {
      method: 'POST',
      body: formData,
    })
    isImporting.value = false
    selectedFile.value = null
    target.removeAttribute('data-url')

    if (res.ok) {
        emit('import-success')
        showToast('Import terminé avec succès', "#4ade80")
        } else {
        const err = await res.json()
        showToast(`Erreur : ${err.detail}`, "#f87171")
        }
  }
}
</script>

<template>
  <div ref="wrapper" class="import-button-wrapper" style="position: relative; display: inline-block;">
    <button
      :disabled="isImporting"
      class="ImportButton"
      @click="onChooseFile(props.addUrl)"
    >
      {{ label }}
      <span v-if="isImporting" class="loader"></span>
    </button>

    <input
      type="file"
      accept=".xlsx"
      ref="fileInput"
      style="display:none"
      @change="onFileChange"
    />
  </div>
</template>

<style scoped>

.ImportButton {
  margin-left: 3%;
  position: relative;
  overflow: hidden;
  background: linear-gradient(45deg, #4396e9, #38d7f9);
  color: white;
  font-weight: 700;
  font-size: 16px;
  padding: 12px 28px;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  box-shadow: 0 8px 15px rgba(56, 123, 233, 0.5);
  transition: box-shadow 0.3s ease, transform 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 1px;
  user-select: none;
  z-index: 0;
}

.ImportButton::before {
  content: "";
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(60deg, #4396e9, #38d7f9, #4396e9, #38d7f9);
  background-size: 400% 400%;
  animation: gradientShift 8s ease infinite;
  opacity: 0.6;
  filter: blur(10px);
  z-index: -1;
  border-radius: 12px;
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.ImportButton:hover {
  box-shadow: 0 12px 25px rgba(56, 123, 233, 0.7);
  transform: translateY(-3px);
}

.ImportButton:active {
  box-shadow: 0 6px 12px rgba(56, 123, 233, 0.4);
  transform: translateY(1px);
}

.ImportButton:disabled {
  cursor: not-allowed;
  opacity: 0.6;
  box-shadow: none;
  transform: none;
}

.loader {
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top: 3px solid white;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  animation: spin 1s linear infinite;
  margin-left: 12px;
  display: inline-block;
  vertical-align: middle;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

</style>