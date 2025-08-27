<script>
export default {
  name: 'FPackMappingEditor',
  data() {
    return {
      mappingData: null
    }
  },
  mounted() {
    this.createNewMapping()
  },
  methods: {
    createNewMapping() {
      this.mappingData = {
        name: "Mapping Config",
        system_columns: {
          fpack_number: "FPack Number",
          robot_location_code: "Robot location code",
          contractor: "Contractor",
          required_delivery_time: "Required Delivery time (YYwWW)",
          delivery_site: "Delivery site (Contractor / VCC)",
          tracking: "Tracking"
        },
        groups: []
      }
    },
    
    addGroup() {
      this.mappingData.groups.push({
        group_name: "",
        excel_column: ""
      })
    },
    
    removeGroup(index) {
      this.mappingData.groups.splice(index, 1)
    },
    
    loadMappingFile(event) {
      const file = event.target.files[0]
      if (file) {
        const reader = new FileReader()
        reader.onload = (e) => {
          try {
            this.mappingData = JSON.parse(e.target.result)
          } catch (error) {
            alert('Erreur lors du chargement du fichier JSON: ' + error.message)
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
    },
    
    getSystemFieldLabel(key) {
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
    
    getSystemFieldPlaceholder(key) {
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
  <div class="mapping-editor">
    <div class="header">
      <h2>Éditeur de Mapping F-Pack</h2>
      <div class="file-controls">
        <input 
          type="file" 
          ref="fileInput" 
          @change="loadMappingFile" 
          accept=".json"
          style="display: none"
        >
        <button @click="$refs.fileInput.click()" class="btn btn-secondary">
          Charger un mapping existant
        </button>
        <button @click="saveMappingFile" class="btn btn-primary">
          Sauvegarder le mapping
        </button>
        <button @click="createNewMapping" class="btn btn-success">
          Nouveau mapping
        </button>
      </div>
    </div>

    <div class="mapping-content" v-if="mappingData">
      <!-- Configuration générale -->
      <div class="section">
        <h3>Configuration générale</h3>
        <div class="form-group">
          <label>Nom du mapping :</label>
          <input 
            v-model="mappingData.name" 
            type="text" 
            placeholder="Ex: Mapping Config"
          >
        </div>
      </div>

      <!-- Colonnes système -->
      <div class="section">
        <h3>Colonnes Sous-projet</h3>
        <div class="system-columns">
          <div class="column-row" v-for="(columnName, key) in mappingData.system_columns" :key="key">
            <label class="field-label">{{ getSystemFieldLabel(key) }} :</label>
            <input 
              v-model="mappingData.system_columns[key]" 
              type="text" 
              :placeholder="getSystemFieldPlaceholder(key)"
            >
          </div>
        </div>
      </div>

      <!-- Groupes -->
      <div class="section">
        <h3>Groupes</h3>
        <div class="groups-container">
          <div 
            v-for="(group, index) in mappingData.groups" 
            :key="index" 
            class="group-row"
          >
            <div class="group-fields">
              <div class="field">
                <label>Nom du groupe (template) :</label>
                <input 
                  v-model="group.group_name" 
                  type="text" 
                  placeholder="Ex: Robot"
                >
              </div>
              
              <div class="field">
                <label>Colonne Excel :</label>
                <input 
                  v-model="group.excel_column" 
                  type="text" 
                  placeholder="Ex: Mechanical Unit"
                >
              </div>
              
              <button @click="removeGroup(index)" class="btn btn-danger btn-sm">
                Supprimer
              </button>
            </div>
          </div>
          
          <button @click="addGroup" class="btn btn-primary">
            Ajouter un groupe
          </button>
        </div>
      </div>

      <!-- Prévisualisation JSON -->
      <div class="section">
        <h3>Prévisualisation JSON</h3>
        <div class="json-preview">
          <pre>{{ JSON.stringify(mappingData, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>



<style scoped>
.mapping-editor {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
}

.header h2 {
  margin: 0;
  color: #333;
}

.file-controls {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #545b62;
}

.btn-success {
  background-color: #28a745;
  color: white;
}

.btn-success:hover {
  background-color: #1e7e34;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn-danger:hover {
  background-color: #c82333;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}

.section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.section h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
  border-bottom: 1px solid #ccc;
  padding-bottom: 10px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #555;
}

.form-group input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.system-columns {
  display: grid;
  gap: 15px;
}

.column-row {
  display: grid;
  grid-template-columns: 200px 1fr;
  align-items: center;
  gap: 15px;
}

.field-label {
  font-weight: bold;
  color: #555;
}

.groups-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.group-row {
  border: 1px solid #ccc;
  border-radius: 8px;
  padding: 15px;
  background-color: white;
}

.group-fields {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  align-items: end;
  gap: 15px;
}

.field label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #555;
  font-size: 14px;
}

.field input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.json-preview {
  background-color: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 15px;
  max-height: 400px;
  overflow: auto;
}

.json-preview pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>