<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const props = defineProps<{
  initialGroup?: {
    display_name: string
    group_items: {
      type: 'produit' | 'equipement' | 'robot'
      ref_id: number
      label: string
    }[]
  }
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'created', group: {
    type: 'group'
    ref_id: null
    display_name: string
    group_items: {
      type: 'produit' | 'equipement' | 'robot'
      ref_id: number
      label: string
    }[]
  }): void
}>()

const nomGroupe = ref(props.initialGroup?.display_name ?? '')
const selectedItems = ref(
  props.initialGroup?.group_items ? [...props.initialGroup.group_items] : []
)

const produits = ref<any[]>([])
const equipements = ref<any[]>([])
const robots = ref<any[]>([])

async function loadData() {
  const [prodRes, eqRes, robRes] = await Promise.all([
    axios.get('http://localhost:8000/produits'),
    axios.get('http://localhost:8000/equipements'),
    axios.get('http://localhost:8000/robots')
  ])
  produits.value = prodRes.data
  equipements.value = eqRes.data
  robots.value = robRes.data
}

onMounted(loadData)

function addItem(type: 'produit' | 'equipement' | 'robot', id: number) {
  const source = type === 'produit' ? produits.value :
                 type === 'equipement' ? equipements.value :
                 robots.value

  const item = source.find(i => i.id === id)
  if (!item) return
  const alreadyAdded = selectedItems.value.some(e => e.type === type && e.ref_id === id)
  if (!alreadyAdded) {
    selectedItems.value.push({ type, ref_id: id, label: item.nom })
  }
}

function removeItem(index: number) {
  selectedItems.value.splice(index, 1)
}

function valider() {
  if (!nomGroupe.value.trim()) {
    alert("Nom du groupe requis")
    return
  }
  emit('created', {
    type: 'group',
    ref_id: null,
    display_name: nomGroupe.value,
    group_items: [...selectedItems.value]
  })
}
</script>

<template>
  <div class="modal">
    <div class="modal-content">
      <h3>{{ props.initialGroup ? 'Modifier le groupe' : 'Créer un nouveau groupe' }}</h3>

      <label>Nom du groupe :</label>
      <input v-model="nomGroupe" placeholder="nom du groupe" />

      <div class="selectors">
        <select @change="addItem('produit', +($event.target as HTMLSelectElement).value)">
          <option value="">➕ Produit</option>
          <option v-for="p in produits" :key="p.id" :value="p.id">{{ p.nom }}</option>
        </select>
        <select @change="addItem('equipement', +($event.target as HTMLSelectElement).value)">
          <option value="">➕ Équipement</option>
          <option v-for="e in equipements" :key="e.id" :value="e.id">{{ e.nom }}</option>
        </select>
        <select @change="addItem('robot', +($event.target as HTMLSelectElement).value)">
          <option value="">➕ Robot</option>
          <option v-for="r in robots" :key="r.id" :value="r.id">{{ r.nom }}</option>
        </select>
      </div>

      <div class="preview">
        <h4>Éléments du groupe :</h4>
        <ul>
          <li v-for="(item, i) in selectedItems" :key="i">
            {{ item.label }} ({{ item.type }})
            <button @click="removeItem(i)">❌</button>
          </li>
        </ul>
      </div>

      <div class="actions">
        <button @click="valider">✅ {{ props.initialGroup ? 'Modifier' : 'Créer' }}</button>
        <button @click="$emit('close')">❌ Annuler</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal {
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.selectors {
  display: flex;
  gap: 1rem;
  justify-content: space-between;
}

.preview ul {
  list-style: none;
  padding-left: 0;
}

.preview li {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}
</style>
