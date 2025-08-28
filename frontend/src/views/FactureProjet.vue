<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { showToast } from '../composables/useToast'

const route = useRoute()
const router = useRouter()

const facture = ref<any | null>(null)
const loading = ref(true)

const totalProduit = computed(() => facture.value?.totaux?.produit ?? 0)
const totalTransport = computed(() => facture.value?.totaux?.transport ?? 0)
const totalGlobal = computed(() => facture.value?.totaux?.global ?? 0)


const exportFactureExcel = async () => {
  try {
    const projetId = route.params.id || route.params.sous_projet_fpack_id
    
    if (!projetId) {
      showToast("Aucun ID de projet trouvé", "#EE1111")
      return
    }
    
    const response = await axios.get(`http://localhost:8000/sous_projet_fpack/${projetId}/facture-excel`, {
      responseType: 'blob'
    })

    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })

    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `facture-projet-${projetId}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error("Erreur export Excel :", error)
    showToast("Erreur lors de l'export Excel - Fonctionnalité peut-être non disponible", "#EE1111")
  }
}

const exportFacturePDF = async () => {
  try {
    const projetId = route.params.id || route.params.sous_projet_fpack_id
    
    if (!projetId) {
      showToast("Aucun ID de projet trouvé", "#EE1111")
      return
    }
    
    const response = await axios.get(`http://localhost:8000/sous_projet_fpack/${projetId}/facture-pdf`, {
      responseType: 'blob'
    })

    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)

    const link = document.createElement('a')
    link.href = url
    link.download = `facture-projet-${projetId}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error("Erreur export PDF :", error)
    showToast("Erreur lors de l'export PDF - Fonctionnalité peut-être non disponible", "#EE1111")
  }
}


async function fetchFacture() {
  loading.value = true
  try {
    const id = route.params.id || route.params.sous_projet_fpack_id
    
    if (!id) {
      throw new Error('Aucun ID de projet trouvé dans la route')
    }
    
    const res = await axios.get(`http://localhost:8000/sous_projet_fpack/${id}/facture`)
    if (res.data) {
      facture.value = res.data
      console.log("Facture lignes", facture.value)
    } else {
      showToast("Aucune donnée de facture trouvée", "#EE1111")
    }
  } catch (err) {
    console.error(err)
    showToast("Erreur lors du chargement de la facture", "#EE1111")
    facture.value = null
  } finally {
    loading.value = false
  }
}

function revenir() {
  router.back()
}

onMounted(fetchFacture)
</script>

<template>
  <div class="facture-container">
    <div class="facture-header">
      <h1>🧾 Facture du Projet <span class="page-title"> {{facture?.nom_projet || '#' + (route.params.id || route.params.sous_projet_fpack_id) }}</span></h1>
      <button @click="revenir" class="btn btn-secondary">Retour</button>
    </div>

    <div v-if="loading" class="facture-loading">Chargement de la facture...</div>

    <div v-else-if="facture" class="facture-card">
      <table class="facture-table">
        <thead>
          <tr>
            <th>Produit</th>
            <th>Qté</th>
            <th>Prix unitaire €</th>
            <th>Transport unitaire €</th>
            <th>Total €</th>
            <th>Commentaire</th>
          </tr>
        </thead>
        <tbody class="scrollable-tbody">
          <tr v-for="l in facture.lines || []" :key="l.produit_id" :class="l.prix_unitaire === 0 ? 'warning-row' : ''">
            <td>{{ l.nom }}</td>
            <td>{{ l.qte }}</td>
            <td>{{ l.prix_unitaire?.toFixed(2) ?? '0.00'}}</td>
            <td>{{ l.prix_transport?.toFixed(2) ?? '0.00' }}</td>
            <td><strong>{{ l.total_ligne?.toFixed(2) ?? '0.00' }}</strong></td>
            <td>{{ l.commentaire || (l.prix_unitaire === 0 ? '⚠️ Aucun prix disponible' : '-') }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td><strong>Total</strong></td>
            <td colspan="1"></td>
            <td><strong>{{totalProduit.toFixed(2)}}</strong></td>
            <td><strong>{{totalTransport.toFixed(2)}}</strong></td>
            <td class="total-final">{{ totalGlobal.toFixed(2) }} € TTC</td>
            <td></td>
          </tr>
        </tfoot>
      </table>

      <div class="facture-actions">
        <button @click="exportFacturePDF" class="btn btn-green">Exporter en PDF</button>
        <button @click="exportFactureExcel" class="btn btn-blue">Télécharger Excel</button>
      </div>
    </div>
    
    <div v-else class="facture-error">
      <p>Aucune facture trouvée ou erreur de chargement.</p>
    </div>
  </div>
</template>

<style scoped>
.facture-container {
  max-width: 1000px;
  margin: 1rem auto 0 auto;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.facture-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  border-bottom: 3px solid #2563eb;
  padding-bottom: 1rem;
}

.facture-header h1 {
  font-size: 2rem;
  color: #1e3a8a;
}

.page-title {
  font-size: 2rem;
  color: #2563eb;
  font-weight: bold;
}

.facture-loading {
  text-align: center;
  font-size: 1.2rem;
  color: #64748b;
  padding: 2rem 0;
  animation: pulse 1s infinite;
}

.facture-error {
  text-align: center;
  font-size: 1.2rem;
  color: #dc2626;
  padding: 2rem 0;
}

.facture-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
  overflow-x: auto;
  
}

.facture-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
  
}

.facture-table thead,
.facture-table tfoot {
  display: table;
  width: 100%;
  table-layout: fixed;
}

.facture-table th {
  background: linear-gradient(to right, #3b82f6, #6366f1);
  color: white;
  padding: 0.75rem;
  text-align: center;
  font-size: 0.95rem;
}

.scrollable-tbody {
  display: block;
  max-height: 35vh;
  overflow-y: auto;
  width: 100%;
}

.scrollable-tbody tr {
  display: table;
  table-layout: fixed;
  width: 100%;
}

.facture-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.95rem;
  color: #374151;
}

.facture-table .total-final {
  font-size: 1.1rem;
  font-weight: bold;
  color: #059669;
}

.warning-row {
  background-color: #fef2f2;
  color: #991b1b;
}

.facture-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn {
  padding: 0.5rem 1.25rem;
  font-weight: 600;
  border-radius: 0.5rem;
  transition: all 0.2s;
}

.btn-secondary {
  background: #4b5563;
  color: white;
}
.btn-secondary:hover {
  background: #374151;
}

.btn-green {
  background: #10b981;
  color: white;
}
.btn-green:hover {
  background: #059669;
}

.btn-blue {
  background: #2563eb;
  color: white;
}
.btn-blue:hover {
  background: #1d4ed8;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>