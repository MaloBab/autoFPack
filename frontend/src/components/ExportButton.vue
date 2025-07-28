<script setup>
import { ref } from 'vue'

const props = defineProps({
  exportUrl: { type: String, required: true },
  label: { type: String, default: 'Exporter' },
})

const isExporting = ref(false)

function exportFile() {
  if (isExporting.value) return

  isExporting.value = true

  fetch(props.exportUrl)
    .then(response => {
      if (!response.ok) throw new Error('Erreur lors de l’export')
      return response.blob()
    })
    .then(blob => {
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = props.label.toLowerCase().replace(/\s+/g, '-') + '.xlsx'
      a.click()
      window.URL.revokeObjectURL(url)
    })
    .catch(err => {
      alert(err.message || 'Erreur réseau')
    })
    .finally(() => {
      isExporting.value = false
    })
}
</script>

<template>
  <button
    :disabled="isExporting"
    class="ExportButton"
    @click="exportFile"
  >
    {{ label }}
    <span v-if="isExporting" class="loader"></span>
  </button>
</template>

<style scoped>
.ExportButton {
  margin-left: 2%;
  position: relative;
  overflow: hidden;
  background: linear-gradient(45deg, #28a745, #2ecc71);
  color: white;
  font-weight: 700;
  font-size: 16px;
  padding: 12px 28px;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  box-shadow: 0 8px 15px rgba(62, 252, 37, 0.3);
  transition: box-shadow 0.3s ease, transform 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 1px;
  user-select: none;
  z-index: 0;
}

.ExportButton::before {
  content: "";
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(60deg, #28a745, #2ecc71, #28a745, #2ecc71);
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

.ExportButton:hover {
  box-shadow: 0 12px 25px rgba(37, 252, 116, 0.7);
  transform: translateY(-3px);
}

.ExportButton:active {
  box-shadow: 0 6px 12px rgba(37, 252, 116, 0.7);
  transform: translateY(1px);
}

.ExportButton:disabled {
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