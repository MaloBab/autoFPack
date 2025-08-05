<script setup lang="ts">
import { ref, computed, defineEmits } from 'vue'

interface Produit {
  id: number
  nom: string
  type: string
  fournisseur_id: number
  reference: string
  fournisseur: string
}
interface Fournisseur {
  id: number
  nom: string
}

const emit = defineEmits(['add', 'close'])

const props = defineProps<{
  produits: Produit[]
  fournisseurs: Fournisseur[]
}>()

const search = ref('')
const filters = ref({ fournisseur: '', type: '' })

const types = computed(() => [...new Set(props.produits.map(p => p.type))])
props.fournisseurs.map(f => f.nom)

const enrichedProduits = computed(() =>
  props.produits.map(p => ({ ...p,fournisseur: props.fournisseurs.find(f => f.id === p.fournisseur_id)?.nom || '' }))
)

const produitsFiltres = computed(() =>
  enrichedProduits.value.filter(p =>
    (p.nom.toLowerCase().includes(search.value.toLowerCase()) || (p.fournisseur.toLowerCase().includes(search.value.toLowerCase())) || (p.reference.toLowerCase().includes(search.value.trim().toLowerCase()) && search.value.trim() !== '') || (p.reference.toLowerCase().includes(search.value.trim().toLowerCase()) && search.value.trim() !== ' '))
     && (!filters.value.fournisseur || p.fournisseur === filters.value.fournisseur) &&
        (!filters.value.type || p.type === filters.value.type)
  )
)

function ajouterProduit(p: Produit) {
  emit('add', p)
  emit('close')
}
</script>

<template>
  <div class="modal">
    <div class="modal-content">
      <div class="modal-header">
        <h3>Ajouter un produit</h3>
        <button @click="$emit('close')" class="close-button">✕</button>
      </div>

      <div class="search-bar">
        <input
          v-model="search"
          type="text"
          placeholder="Rechercher un produit..."
          class="search-input"
        />
      </div>

      <div class="filters">
        <div class="filter-group">
          <label>Fournisseur</label>
          <select v-model="filters.fournisseur" class="filter-select">
            <option value="">Tous</option>
            <option v-for="f in props.fournisseurs" :key="f.id" :value="f.nom">{{ f.nom }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label>Type</label>
          <select v-model="filters.type" class="filter-select">
            <option value="">Tous</option>
            <option v-for="t in types" :key="t">{{ t }}</option>
          </select>
        </div>
      </div>

      <div class="results">
        <div
          v-for="produit in produitsFiltres"
          :key="produit.id"
          class="result-item"
        >
          <div class="item-info">
            <div class="item-name">{{ produit.nom }}  |  <span class="item-ref">{{ produit.reference }}</span></div>
            <div class="item-details">
              <span>{{ produit.fournisseur }}</span> • <span>{{ produit.type }}</span>
            </div>
          </div>
          <button class="add-button" @click.stop="ajouterProduit(produit)">Ajouter</button>
        </div>
        <div v-if="produitsFiltres.length === 0" class="no-results">
          Aucun produit trouvé.
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
.filters {
  display: flex;
  gap: 1rem;
}
.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.filter-group label {
  font-weight: 600;
  color: #475569;
}
.filter-select {
  padding: 0.55rem 1rem;
  border-radius: 10px;
  border: 1.5px solid #cbd5e1;
  appearance: none;
  cursor: pointer;
}
.results {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  background-color: #f3faff;
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
  box-shadow: 0 5px 15px rgba(248, 
113, 113, 0.4);
  transition: background-color 0.25s ease, box-shadow 0.25s ease;
}
.btn-cancel:hover {
  background-color: #dc2626;
  box-shadow: 0 8px 20px rgba(220, 38, 38, 0.6);
}
</style>
