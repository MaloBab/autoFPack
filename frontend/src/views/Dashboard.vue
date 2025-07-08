<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

interface DashboardStats {
  produits: number
  equipements: number
  robots: number
  clients: number
  fournisseurs: number
  fpacks: number
  groupes: number
  relations: number
  config_columns: number
}

const stats = ref<DashboardStats | null>(null)
const isLoading = ref(true)
const error = ref('')

function getLabel(key: string): string {
  const labels: Record<string, string> = {
    produits: '🧩 Produits',
    equipements: '🔧 Équipements',
    robots: '🤖 Robots',
    clients: '👥 Clients',
    fournisseurs: '🏭 Fournisseurs',
    fpacks: '📦 F-Packs'
  }
  return labels[key] || key
}

async function fetchStats() {
  try {
    const res = await axios.get('http://localhost:8000/dashboard/stats')
    stats.value = res.data
  } catch (err) {
    error.value = 'Erreur lors du chargement des statistiques.'
  } finally {
    isLoading.value = false
  }
}

onMounted(fetchStats)
</script>

<template>
  <div class="dashboard">
    <h1>📊 Tableau de bord</h1>

    <div v-if="isLoading">Chargement...</div>
    <div v-else-if="error">{{ error }}</div>

    <div v-else class="stats-grid">
      <div class="card" v-for="(val, key) in stats" :key="key">
        <h3>{{ getLabel(key) }}</h3>
        <p>{{ val }}</p>
      </div>
    </div>

    <div class="guide">
      <h2>📘 Utilisation</h2>
      <ol>
        <li>🧩 Créez des <strong>produits</strong> et <strong>équipements</strong> via leurs pages respectives.</li>
        <li>👥 Ajoutez des <strong>clients</strong> et des <strong>robots</strong>.</li>
        <li>📦 Créez un <strong>F-Pack</strong> pour un client.</li>
        <li>⚙️ Allez dans <strong>Configure F-Pack</strong> pour ajouter de nouvelles colonnes.</li>
        <li>Ecrire suite plus tard</li>
      </ol>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 1rem;
  font-family: 'Segoe UI', sans-serif;
}

h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.stats-grid {
  display: flex;
  flex-wrap: nowrap;
  justify-content: space-between;
  gap: 1rem;
}

.card {
  flex: 1 1 0;
  min-width: 0;
  background: #e4e9f9;
  padding: 1rem;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s ease;
}
.card:hover {
  transform: translateY(-3px);
}
.card h3 {
  margin: 0;
  font-size: 1rem;
  color: #475569;
}
.card p {
  font-size: 2rem;
  font-weight: bold;
  margin: 0.5rem 0 0;
  color: #2563eb;
}

.guide {
  background: #ffffff;
  padding: 2rem;
  border-radius: 12px;
  margin-top: 2%;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
}

.guide h2 {
  font-size: 1.4rem;
  color: #1e293b;
  margin-bottom: 1rem;
}

.guide ol {
  padding-left: 1.5rem;
  margin-bottom: 1.5rem;
}

.guide ol li {
  margin-bottom: 0.75rem;
  line-height: 1.4;
}

.tips {
  list-style: square;
  padding-left: 1.5rem;
  color: #334155;
}
</style>