<script setup lang="ts">
const props = defineProps<{
  step: number
  active: boolean
  completed: boolean
  visible: boolean
  mappingConfig: Record<string, any>
  previewColumns: string[]
  mappedColumnsCount: number
  uniqueProjectCount: number
}>()

const emit = defineEmits<{
  mappingConfigured: []
  previousStep: []
}>()
</script>

<template>
  <div class="step-container" :class="{ active, completed }">
    <div class="step-header">
      <div class="step-indicator">
        <div class="step-number">{{ step }}</div>
        <div class="step-line"></div>
      </div>
      <div class="step-content-header">
        <h3>🔗 Configuration du mapping</h3>
        <p class="step-description">Configuration automatique basée sur les standards F-Pack Matrix</p>
      </div>
    </div>
    
    <div class="step-body" v-show="visible">
      <div class="mapping-overview">
        <div class="mapping-stats">
          <div class="stat-card">
            <div class="stat-value">{{ mappedColumnsCount }}</div>
            <div class="stat-label">Colonnes mappées</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ previewColumns.length }}</div>
            <div class="stat-label">Colonnes détectées</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ uniqueProjectCount }}</div>
            <div class="stat-label">Projets concernés</div>
          </div>
        </div>
        
        <div class="mapping-preview">
          <h5>🎯 Mapping automatique configuré</h5>
          <div class="mapping-list-compact">
            <div v-for="(config, column) in mappingConfig.excel_columns" :key="column" class="mapping-item-compact">
              <span class="column-name">{{ column }}</span>
              <span class="arrow">→</span>
              <span class="target-name" :class="config.type">
                {{ config.target === 'selection' ? `📋 ${config.groupe_nom}` : `📝 ${config.target.split('.')[1]}` }}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="step-actions">
        <button class="btn btn-secondary" @click="emit('previousStep')">
          ← Retour
        </button>
        <button class="btn btn-primary" @click="emit('mappingConfigured')">
          👁️ Prévisualiser l'import
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Conteneur principal avec animation */
.step-container {
  background: #ffffff;
  border-radius: 16px;
  margin-bottom: 24px;
  overflow: hidden;
  box-shadow: 0 6px 25px rgba(52, 73, 94, 0.08);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  transform: translateY(10px);
  opacity: 0;
  animation: slideInUp 0.5s ease-out forwards;
  position: relative;
  border: 1px solid rgba(189, 195, 199, 0.2);
}

.step-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3498db, #9b59b6, #e74c3c);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.5s ease-out;
}

.step-container.active::before {
  transform: scaleX(1);
}

.step-container.active {
  box-shadow: 0 12px 35px rgba(52, 152, 219, 0.12);
  transform: translateY(-2px);
}

.step-container.completed {
  background: linear-gradient(135deg, rgba(46, 204, 113, 0.02) 0%, rgba(39, 174, 96, 0.02) 100%);
  border: 1px solid rgba(46, 204, 113, 0.2);
}

@keyframes slideInUp {
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* En-tête d'étape */
.step-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 28px;
  background: linear-gradient(135deg, #fcfcfc 0%, #f8f9fa 100%);
  border-bottom: 1px solid rgba(189, 195, 199, 0.15);
  position: relative;
  overflow: hidden;
}

.step-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-number {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #3498db 0%, #9b59b6 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.1rem;
  box-shadow: 0 4px 15px rgba(52, 152, 219, 0.25);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.step-container.active .step-number {
  transform: scale(1.05) rotate(360deg);
  box-shadow: 0 6px 20px rgba(52, 152, 219, 0.3);
}

.step-container.completed .step-number {
  background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
  box-shadow: 0 4px 15px rgba(39, 174, 96, 0.25);
}

.step-line {
  width: 60px;
  height: 2px;
  background: #ecf0f1;
  border-radius: 1px;
  position: relative;
  overflow: hidden;
}

.step-line::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 0;
  background: linear-gradient(90deg, #3498db, #9b59b6);
  border-radius: 1px;
  transition: width 0.6s ease-out 0.2s;
}

.step-container.active .step-line::before {
  width: 100%;
}

.step-container.completed .step-line::before {
  background: linear-gradient(90deg, #27ae60, #2ecc71);
  width: 100%;
}

.step-content-header h3 {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 10px;
}

.step-description {
  margin: 4px 0 0 0;
  color: #7f8c8d;
  font-size: 0.95rem;
  font-weight: 500;
}

/* Corps de l'étape */
.step-body {
  padding: 28px;
  animation: fadeIn 0.4s ease-out 0.2s both;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Vue d'ensemble du mapping */
.mapping-overview {
  margin-bottom: 28px;
}

.mapping-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 28px;
}

.stat-card {
  background: #ffffff;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 4px 20px rgba(52, 73, 94, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  border: 1px solid #ecf0f1;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3498db, #9b59b6, #e74c3c);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.5s ease-out;
}

.stat-card:hover {
  box-shadow: 0 8px 25px rgba(52, 73, 94, 0.1);
  transform: translateY(-3px);
}

.stat-card:hover::before {
  transform: scaleX(1);
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #3498db 0%, #9b59b6 50%, #e74c3c 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 6px;
  line-height: 1.1;
}
.stat-label {
  font-size: 1rem;
  color: #7f8c8d;
  font-weight: 600;
}
.mapping-preview h5 {
  margin: 0 0 12px 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
}
.mapping-list-compact {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #ecf0f1;
  border-radius: 10px;
  padding: 12px;
  background: #fafafa;
}
.mapping-item-compact {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #ecf0f1;
}
.mapping-item-compact:last-child {
  border-bottom: none;
}
.column-name {
  font-weight: 600;
  color: #34495e;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.arrow {
  color: #bdc3c7;
}
.target-name {
  font-weight: 600;
  flex: 1;
  text-align: right;
}
.target-name.selection {
  color: #27ae60;
}
.target-name.fpack {
  color: #2980b9;
}
.target-name.unknown {
  color: #7f8c8d;
}
.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px solid #ecf0f1;
}
.btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 14px 28px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.btn-primary {
  background: linear-gradient(135deg, #3498db 0%, #9b59b6 100%);
  color: white;
  border: none;
  box-shadow: 0 6px 20px rgba(52, 152, 219, 0.3);
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
}
.btn-secondary {
  background: #ecf0f1;
  color: #34495e;
  border: none;
}
.btn-secondary:hover {
  background: #d0d7de;
  transform: translateY(-1px);
}
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}
@keyframes slideInUp {
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>