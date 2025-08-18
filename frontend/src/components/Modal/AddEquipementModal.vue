<script setup lang="ts">
import { ref, computed, defineEmits } from 'vue'


interface Equipement {
  id: number
  reference: string
  nom: string
  equipement_produit?: { equipement_id: number; produit_id: number; quantite: number }[]
}

const props = defineProps<{
  equipements: Equipement[]
}>()

const emit = defineEmits(['add', 'close'])
const search = ref('')

const enrichedEquipements = computed(() =>
  props.equipements.map(e => ({
    ...e,
    produits_count: e.equipement_produit?.reduce((sum, ep) => sum + (ep.quantite || 0), 0) ?? 0
  }))
)

const equipementsFiltres = computed(() =>
  enrichedEquipements.value.filter(e =>
    e.nom.toLowerCase().includes(search.value.trim().toLowerCase()) ||
    e.reference.toLowerCase().includes(search.value.trim().toLowerCase())
  )
)

function ajouterEquipement(e: Equipement) {
  emit('add', e)
  emit('close')
}

</script>

<template>
  <div class="modal">
    <div class="modal-content">
      <div class="modal-header">
        <h3>Ajouter un équipement</h3>
        <button @click="$emit('close')" class="close-button">✕</button>
      </div>

      <div class="search-bar">
        <input
          v-model="search"
          type="text"
          placeholder="Rechercher équipement..."
          class="search-input"
        />
      </div>

      <div class="results">
        <div
          v-for="e in equipementsFiltres"
          :key="e.id"
          class="result-item"
        >
          <div class="item-info">
            <div class="item-name">
              {{ e.nom }}  |  <span class="item-ref">{{ e.reference }}</span>
            </div>
            <div class="item-details">
              <span>{{ e.produits_count }} produit(s)</span>
            </div>
          </div>
          <button class="add-button" @click.stop="ajouterEquipement(e)">Ajouter</button>
        </div>
        <div v-if="equipementsFiltres.length === 0" class="no-results">
          Aucun équipement trouvé.
        </div>
      </div>

      <div class="actions">
        <button @click="$emit('close')" class="btn-cancel">Annuler</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal {
  position: fixed;
  inset: 0;
  background: rgba(30, 41, 59, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  backdrop-filter: blur(6px);
  z-index: 1000;
}
.modal-content {
  background: #ffffff;
  border-radius: 16px;
  width: 480px;
  max-height: 90vh;
  overflow-y: auto;
  padding: 2rem;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal-header h3 {
  font-size: 1.8rem;
  color: #1e293b;
}
.close-button {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  color: #475569;
  cursor: pointer;
}
.search-bar {
  display: flex;
}
.search-input {
  width: 100%;
  padding: 0.6rem 1rem;
  border: 1.5px solid #cbd5e1;
  border-radius: 10px;
  font-size: 1rem;
  outline-offset: 2px;
  outline: none;
}
.search-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 8px #bfdbfeaa;
}
.results {
  flex: 1;
  overflow-y: auto;
  border-top: 1px solid #e2e8f0;
  padding-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  transition: background-color 0.15s ease;
  cursor: pointer;
}
.result-item:hover {
  background-color: #e0e7ff;
}
.item-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.item-name {
  font-weight: 700;
  color: #1e293b;
}
.item-details {
  font-size: 0.875rem;
  color: #6b7280;
}
.item-ref {
  font-size: 0.80rem;
  color: #c5c5c5;
}
.add-button {
  background-color: #3b82f6;
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  box-shadow: 0 5px 15px rgba(59, 130, 246, 0.4);
  transition: background-color 0.25s ease, box-shadow 0.25s ease;
}
.add-button:hover {
  background-color: #2563eb;
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.6);
}
.no-results {
  text-align: center;
  color: #94a3b8;
  padding: 1rem;
}
.actions {
  display: flex;
  justify-content: flex-end;
}
.btn-cancel {
  background-color: #f87171;
  color: white;
  padding: 0.65rem 1.6rem;
  border-radius: 10px;
  font-weight: 600;
  border: none;
  box-shadow: 0 5px 15px rgba(248, 113, 113, 0.4);
  transition: background-color 0.25s ease, box-shadow 0.25s ease;
}
.btn-cancel:hover {
  background-color: #dc2626;
  box-shadow: 0 8px 20px rgba(220, 38, 38, 0.6);
}
</style>