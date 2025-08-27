<script>
export default {
  name: 'FPackMappingEditor',
  data() {
    return {
      mappingData: null,
      isDarkMode: false,
      justCopied: false,
      toasts: [],
      toastId: 0
    }
  },
  mounted() {
    this.createNewMapping()
    
    // Load dark mode preference
    const darkMode = localStorage.getItem('darkMode') === 'true'
    this.isDarkMode = darkMode
  },
  methods: {
    createNewMapping() {
      this.mappingData = {
        name: "Mapping Config",
        subproroject_columns: {
          fpack_number: "FPack Number",
          robot_location_code: "Robot location code",
          contractor: "Contractor",
          required_delivery_time: "Required Delivery time (YYwWW)",
          delivery_site: "Delivery site (Contractor / VCC)",
          tracking: "Tracking"
        },
        groups: []
      }
      this.showToast('Nouveau mapping créé', 'success', '✨')
    },
    
    addGroup() {
      this.mappingData.groups.push({
        group_name: "",
        excel_column: ""
      })
      this.showToast('Groupe ajouté', 'success', '➕')
    },
    
    removeGroup(index) {
      this.mappingData.groups.splice(index, 1)
      this.showToast('Groupe supprimé', 'info', '🗑️')
    },
    
    loadMappingFile(event) {
      const file = event.target.files[0]
      if (file) {
        const reader = new FileReader()
        reader.onload = (e) => {
          try {
            this.mappingData = JSON.parse(e.target.result)
            this.showToast('Mapping chargé avec succès', 'success', '📁')
          } catch (error) {
            this.showToast('Erreur lors du chargement', 'error', '❌')
          }
        }
        reader.readAsText(file)
        event.target.value = null
      }
    },
    
    saveMappingFile() {
      const dataStr = JSON.stringify(this.mappingData, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      
      const link = document.createElement('a')
      link.href = URL.createObjectURL(dataBlob)
      link.download = `${this.mappingData.name.replace(/\s+/g, '_')}.json`
      link.click()
      
      this.showToast('Mapping sauvegardé', 'success', '💾')
    },
    
    toggleDarkMode() {
      this.isDarkMode = !this.isDarkMode
      localStorage.setItem('darkMode', this.isDarkMode.toString())
    },
    
    async copyToClipboard() {
      try {
        await navigator.clipboard.writeText(JSON.stringify(this.mappingData, null, 2))
        this.justCopied = true
        setTimeout(() => this.justCopied = false, 2000)
        this.showToast('JSON copié', 'success', '📋')
      } catch (err) {
        this.showToast('Erreur lors de la copie', 'error', '❌')
      }
    },
    
    showToast(message, type = 'info', icon = 'ℹ️') {
      const toast = {
        id: this.toastId++,
        message,
        type,
        icon
      }
      
      this.toasts.push(toast)
      
      setTimeout(() => {
        this.toasts = this.toasts.filter(t => t.id !== toast.id)
      }, 3000)
    },
    
    getSubprorojectFieldLabel(key) {
      const labels = {
        fpack_number: "FPack Number",
        robot_location_code: "Robot Location Code",
        contractor: "Contractor",
        required_delivery_time: "Required Delivery Time",
        delivery_site: "Delivery Site",
        tracking: "Tracking"
      }
      return labels[key] || key
    },
    
    getSubprorojectFieldPlaceholder(key) {
      const placeholders = {
        fpack_number: "Ex: FPack Number",
        robot_location_code: "Ex: Robot location code",
        contractor: "Ex: Contractor",
        required_delivery_time: "Ex: Required Delivery time (YYwWW)",
        delivery_site: "Ex: Delivery site (Contractor / VCC)",
        tracking: "Ex: Tracking"
      }
      return placeholders[key] || "Nom de la colonne Excel"
    }
  }
}
</script>

<template>
  <div class="mapping-editor" :class="{ 'dark-mode': isDarkMode }">
    <!-- Header simplifié -->
    <div class="header">
      <div class="title-section">
        <h1 class="main-title">📝 Éditeur de Mapping F-Pack</h1>
        <p class="subtitle">Configuration des mappings JSON</p>
      </div>
      
      <div class="file-controls">
        <input 
          type="file" 
          ref="fileInput" 
          @change="loadMappingFile" 
          accept=".json"
          style="display: none"
        >
        
        <button class="mode-toggle" @click="toggleDarkMode">
          {{ isDarkMode ? '☀️' : '🌙' }}
        </button>

        <button @click="$refs.fileInput.click()" class="btn btn-secondary">
          📁 Charger
        </button>
        
        <button @click="saveMappingFile" class="btn btn-primary">
          💾 Sauvegarder
        </button>
        
        <button @click="createNewMapping" class="btn btn-success">
          ✨ Nouveau
        </button>
      </div>
    </div>

    <!-- Content avec animation simple -->
    <transition name="fade" mode="out-in">
      <div class="mapping-content" v-if="mappingData" key="content">
        
        <!-- Configuration générale -->
        <div class="section">
          <h3 class="section-title">🎯 Configuration générale</h3>
          <div class="form-group">
            <label>Nom du mapping</label>
            <input 
              v-model="mappingData.name" 
              type="text" 
              placeholder="Ex: Mapping Config"
              class="input-field"
            >
          </div>
        </div>

        <!-- Colonnes système -->
        <div class="section">
          <h3 class="section-title">🔧 Colonnes Sous-projet</h3>
          <div class="subproroject-columns">
            <div 
              class="column-row" 
              v-for="(columnName, key) in mappingData.subproroject_columns" 
              :key="key"
            >
              <label class="field-label">{{ getSubprorojectFieldLabel(key) }}</label>
              <input 
                v-model="mappingData.subproroject_columns[key]" 
                type="text" 
                :placeholder="getSubprorojectFieldPlaceholder(key)"
                class="input-field"
              >
            </div>
          </div>
        </div>

        <!-- Groupes -->
        <div class="section">
          <div class="section-header">
            <h3 class="section-title">👥 Groupes</h3>
            <span class="badge" v-if="mappingData.groups.length">{{ mappingData.groups.length }}</span>
          </div>
          
          <div class="groups-container">
            <transition-group name="group" tag="div" class="groups-list">
              <div 
                v-for="(group, index) in mappingData.groups" 
                :key="`group-${index}`"
                class="group-row"
              >
                <div class="group-number">{{ index + 1 }}</div>
                
                <div class="group-fields">
                  <div class="field">
                    <label>Nom du groupe (template)</label>
                    <input 
                      v-model="group.group_name" 
                      type="text" 
                      placeholder="Ex: Robot"
                      class="input-field"
                    >
                  </div>
                  
                  <div class="field">
                    <label>Colonne Excel</label>
                    <input 
                      v-model="group.excel_column" 
                      type="text" 
                      placeholder="Ex: Mechanical Unit"
                      class="input-field"
                    >
                  </div>
                  
                  <button @click="removeGroup(index)" class="btn-remove" title="Supprimer ce groupe">🗑️</button>
                </div>
              </div>
            </transition-group>
            
            <button @click="addGroup" class="btn-add-group">
              ➕ Ajouter un groupe
            </button>
          </div>
        </div>

        <!-- Prévisualisation JSON -->
        <div class="section">
          <div class="section-header">
            <h3 class="section-title">👁️ Prévisualisation JSON</h3>
            <button 
              @click="copyToClipboard" 
              class="btn-copy"
              :class="{ copied: justCopied }"
            >
              {{ justCopied ? '✅ Copié' : '📋 Copier' }}
            </button>
          </div>
          
          <div class="json-preview">
            <pre>{{ JSON.stringify(mappingData, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </transition>

    <!-- Toast notifications simples -->
    <transition-group name="toast" tag="div" class="toast-container">
      <div 
        v-for="toast in toasts" 
        :key="toast.id"
        class="toast"
        :class="toast.type"
      >
        <span>{{ toast.icon }} {{ toast.message }}</span>
      </div>
    </transition-group>
  </div>
</template>


<style scoped>
.mapping-editor {
  min-height: 100vh;
  background: #f7f7f7;
  font-family: -apple-subproroject, BlinkMacSubprorojectFont, 'Segoe UI', Roboto, sans-serif;
  padding: 20px;
  border-radius: 15px;
  max-width: 1000px;
  margin: 0 auto;
  transition: all 0.3s ease;
}

.mapping-editor.dark-mode {
  background: #1a1a1a;
  color: #e0e0e0;
}

/* Mode Toggle */
.mode-toggle {
  border: none;
  border-radius: 60%;
  background:  #2c3e50;
  font-size: 15px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transition: all 0.3s ease;
  z-index: 100;
}

.dark-mode .mode-toggle {
  background: white;
}

.mode-toggle:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(0,0,0,0.2);
}

.mode-toggle:focus {
  outline: none;
}

/* Header */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 30px;
  background: white;
  border-radius: 15px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.dark-mode .header {
  background: #2c3e50;
}

.main-title {
  font-size: 2rem;
  margin: 0 0 5px 0;
  color: #2c3e50;
}

.dark-mode .main-title {
  color: #ecf0f1;
}

.subtitle {
  color: #7f8c8d;
  margin: 0;
}

.file-controls {
  display: flex;
  gap: 10px;
}

/* Buttons */
.btn {
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 5px;
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn-success {
  background: #2ecc71;
  color: white;
}

/* Sections */
.section {
  margin-bottom: 25px;
  background: white;
  border-radius: 15px;
  padding: 25px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.08);
  transition: all 0.3s ease;
}

.dark-mode .section {
  background: #2c3e50;
}

.section:hover {
  box-shadow: 0 6px 25px rgba(0,0,0,0.12);
  transform: translateY(-2px);
}

.section-title {
  margin: 0 0 20px 0;
  font-size: 1.3rem;
  font-weight: 600;
  color: #2c3e50;
}

.dark-mode .section-title {
  color: #ecf0f1;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.section-header .section-title {
  margin: 0;
  flex: 1;
}

.badge {
  background: #e74c3c;
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

/* Form Elements */
.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #34495e;
}

.dark-mode .form-group label {
  color: #bdc3c7;
}

.input-field {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #ecf0f1;
  color: #000;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s ease;
  background: white;
}

.dark-mode .input-field {
  background: #34495e;
  border-color: #4a6741;
  color: #ecf0f1;
}

.input-field:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

/* Subproroject Columns */
.subproroject-columns {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.column-row {
  display: grid;
  grid-template-columns: 200px 1fr;
  align-items: center;
  gap: 20px;
  padding: 15px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.column-row:hover {
  background: rgba(52, 152, 219, 0.05);
}

.field-label {
  font-weight: 500;
  color: #2c3e50;
}

.dark-mode .field-label {
  color: #bdc3c7;
}

/* Groups */
.groups-container {
  position: relative;
}

.groups-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
}

.group-row {
  display: flex;
  gap: 15px;
  align-items: flex-start;
  padding: 20px;
  background: #f8f9fa;
  border: 2px solid #ecf0f1;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.dark-mode .group-row {
  background: #34495e;
  border-color: #4a6741;
}

.group-row:hover {
  border-color: #3498db;
  box-shadow: 0 4px 15px rgba(52, 152, 219, 0.1);
}

.group-number {
  width: 30px;
  height: 30px;
  background: #3498db;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.group-fields {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 15px;
  flex: 1;
  align-items: end;
}

.field {
  display: flex;
  flex-direction: column;
}

.field label {
  margin-bottom: 5px;
  font-size: 13px;
  font-weight: 500;
  color: #7f8c8d;
}

.btn-remove {
  width: 40px;
  height: 40px;
  border: none;
  background: #e74c3c;
  color: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.btn-remove:hover {
  background: #c0392b;
  transform: scale(1.05);
}

.btn-add-group {
  width: 100%;
  padding: 15px;
  border: 2px dashed #3498db;
  background: rgba(52, 152, 219, 0.05);
  color: #3498db;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-add-group:hover {
  background: rgba(52, 152, 219, 0.1);
  border-style: solid;
}

/* JSON Preview */
.json-preview {
  background: #2d3748;
  border-radius: 8px;
  padding: 20px;
  max-height: 400px;
  overflow: auto;
}

.json-preview pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #e2e8f0;
}

.btn-copy {
  background: none;
  border: 1px solid #3498db;
  color: #3498db;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s ease;
}

.btn-copy:hover {
  background: #3498db;
  color: white;
}

.btn-copy.copied {
  background: #2ecc71;
  border-color: #2ecc71;
  color: white;
}

/* Toast Notifications */
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toast {
  background: white;
  padding: 12px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.15);
  font-size: 14px;
  font-weight: 500;
  min-width: 250px;
}

.toast.success {
  border-left: 4px solid #2ecc71;
}

.toast.error {
  border-left: 4px solid #e74c3c;
}

.toast.info {
  border-left: 4px solid #3498db;
}

.dark-mode .toast {
  background: #2c3e50;
  color: #ecf0f1;
}

/* Animations */
.fade-enter-active, .fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.group-enter-active {
  transition: all 0.3s ease;
}

.group-leave-active {
  transition: all 0.2s ease;
}

.group-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.group-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.group-move {
  transition: transform 0.3s ease;
}

.toast-enter-active {
  transition: all 0.3s ease;
}

.toast-leave-active {
  transition: all 0.2s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

</style>