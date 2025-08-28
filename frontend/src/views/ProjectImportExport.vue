<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import ImportSection from '../components/ImportExport/ImportSection.vue'
import ExportSection from '../components/ImportExport/ExportSection.vue'
import NotificationContainer from '../components/ImportExport/NotificationContainer.vue'
import { useNotifications } from '../composables/useNotifications'

interface Selection {
  groupe_id: number
  groupe_nom: string
  type_item: string
  ref_id: number
  item_nom: string
}

interface SousProjetFpack {
  id: number
  nom: string
  fpack_abbr: string
  FPack_number: string
  Robot_Location_Code: string
  contractor?: string
  required_delivery_time?: string
  delivery_site?: string
  tracking?: string
  selections?: Selection[]
}

interface ProjetGlobal {
  id: number
  projet: string
  client: number
  sous_projets?: SousProjet[]
}

interface SousProjet {
  id: number
  id_global: number
  nom: string
  fpacks?: SousProjetFpack[]
}

const activeTab = ref<'import' | 'export'>('import')
const projetsGlobaux = ref<ProjetGlobal[]>([])
const clients = ref<any[]>([])
const fpackTemplates = ref<any[]>([]) 

const { notifications, addNotification, removeNotification, getNotificationIcon } = useNotifications()

const importProps = ref({
  step: 1,
  active: true,
  completed: false,
  visible: true,
  previewData: [] as any[],
  previewColumns: [] as string[],
  fpackList: [] as any[],
  allFPacksConfigured: false
})

const loadData = async () => {
  try {
    const response = await axios.get('http://localhost:8000/projets_globaux')
      projetsGlobaux.value = response.data

    const resClient = await axios.get('http://localhost:8000/clients')
    clients.value = resClient.data

    const resTemplates = await axios.get('http://localhost:8000/import/fpack-templates')
    fpackTemplates.value = resTemplates.data

  } catch (error) {
    console.error('Erreur lors du chargement des projets:', error)
    addNotification('error', 'Erreur lors du chargement des projets')
  }
}


onMounted(async () => {
  await loadData()
})
</script>

<template>
  <div class="project-import-export">
    <div class="header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="title">Import / Export de F-Pack</h1>
        </div>
        <div class="tabs">
          <button 
            class="tab"
            :class="{ active: activeTab === 'import' }"
            @click="activeTab = 'import'"
          >
            <div class="tab-icon">📥</div>
            <span>Import</span>
          </button>
          <button 
            class="tab"
            :class="{ active: activeTab === 'export' }"
            @click="activeTab = 'export'"
          >
            <div class="tab-icon">📤</div>
            <span>Export</span>
          </button>
        </div>
      </div>
    </div>

    <ImportSection 
      v-if="activeTab === 'import'"
      :step="importProps.step"
      :active="importProps.active"
      :completed="importProps.completed"
      :visible="importProps.visible"
      :preview-data="importProps.previewData"
      :preview-columns="importProps.previewColumns"
      :clients="clients"
      :fpack-list="importProps.fpackList"
      :projets-globaux="projetsGlobaux"
      :fpack-templates="fpackTemplates"
      :all-f-packs-configured="importProps.allFPacksConfigured"
    />
    
    <ExportSection 
      v-if="activeTab === 'export'"
      :clients="clients"
      :projets-globaux="projetsGlobaux"
      @add-notification="addNotification"
    />

    <NotificationContainer 
      :notifications="notifications"
      @remove-notification="removeNotification"
      :get-notification-icon="getNotificationIcon"
    />
  </div>
</template>

<style scoped>
.project-import-export {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  line-height: 1.6;
  color: #2c3e50;
  background: #f7f7f7;
  height: 90vh;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.project-import-export * {
  box-sizing: border-box;
}

.header {
  backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.95);
  border-bottom: 1px solid rgba(52, 73, 94, 0.1);
  box-shadow: 0 4px 20px rgba(52, 73, 94, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  flex: 1;
}

.title {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #3498db 0%, #9b59b6 50%, #e74c3c 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
  line-height: 1.1;
  letter-spacing: -0.025em;
}

.tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: rgba(236, 240, 241, 0.8);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  box-shadow: inset 0 1px 3px rgba(52, 73, 94, 0.1);
  position: relative;
}

.tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  color: #7f8c8d;
  position: relative;
  z-index: 2;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  transform-origin: center;
}

.tab:hover {
  color: #34495e;
  transform: translateY(-1px);
}

.tab.active {
  color: #ffffff;
  background: linear-gradient(135deg, #3498db 0%, #9b59b6 100%);
  box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
  transform: translateY(-2px);
}

.tab-icon {
  font-size: 1.1rem;
  transition: all 0.3s ease;
}

.tab.active .tab-icon {
  transform: scale(1.1);
}
</style>