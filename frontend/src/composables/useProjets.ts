// composables/useProjets.ts - Version optimisée et maintenable
import {computed, reactive } from 'vue'
import axios from 'axios'
import { showToast } from './useToast'

// Types étendus avec nouvelles propriétés
export interface ProjetGlobal {
  id: number
  projet: string
  sous_projet?: string
  client: number
  client_nom: string
  projets: Projet[]
  stats?: {
    nb_projets: number
    nb_projets_complets: number
    nb_projets_en_cours: number
    progression_globale: number
    total_groupes: number
    total_selections: number
  }
}

export interface Projet {
  id: number
  nom: string
  fpack_id: number
  id_global: number
  fpack_nom: string
  client_nom: string
  complet: boolean
  nb_selections: number
  nb_groupes_attendus: number
  progression_percent: number
}

export interface ProjetDetails {
  projet: {
    id: number
    nom: string
    fpack_id: number
    id_global: number
  }
  projet_global?: {
    id: number
    projet: string
    sous_projet?: string
    client: number
  }
  fpack?: {
    id: number
    nom: string
    fpack_abbr: string
    client: number
  }
  client?: {
    id: number
    nom: string
  }
  config_columns: number
  selections: Array<{
    projet_id: number
    groupe_id: number
    type_item: string
    ref_id: number
    groupe_nom: string
    item_nom: string
  }>
  complet: boolean
  progression_percent: number
}

// État réactif centralisé
const state = reactive({
  projetsGlobaux: [] as ProjetGlobal[],
  loading: false,
  currentProjetId: null as number | null,
  lastFetch: null as Date | null,
  error: null as string | null
})

export function useProjets() {
  const baseUrl = 'http://localhost:8000'

  // === Getters computed optimisés ===
  const allProjets = computed(() => 
    state.projetsGlobaux.flatMap(pg => pg.projets)
  )

  const currentProjet = computed(() => 
    allProjets.value.find(p => p.id === state.currentProjetId) || null
  )

  const projetsParClient = computed(() => {
    const map = new Map<number, Projet[]>()
    for (const pg of state.projetsGlobaux) {
      if (!map.has(pg.client)) map.set(pg.client, [])
      map.get(pg.client)?.push(...pg.projets)
    }
    return map
  })

  const projetsByStatus = computed(() => ({
    complets: allProjets.value.filter(p => p.complet),
    enCours: allProjets.value.filter(p => !p.complet),
    total: allProjets.value.length
  }))

  const globalStats = computed(() => {
    const stats = {
      nb_projets_globaux: state.projetsGlobaux.length,
      nb_projets_total: allProjets.value.length,
      nb_projets_complets: 0,
      progression_moyenne: 0
    }

    if (allProjets.value.length > 0) {
      stats.nb_projets_complets = allProjets.value.filter(p => p.complet).length
      const totalProgression = allProjets.value.reduce((sum, p) => sum + p.progression_percent, 0)
      stats.progression_moyenne = Math.round(totalProgression / allProjets.value.length)
    }

    return stats
  })


  const updateLoadingState = async <T>(operation: () => Promise<T>): Promise<T> => {
    state.loading = true
    state.error = null
    try {
      const result = await operation()
      state.lastFetch = new Date()
      return result
    } catch (error: any) {
      throw error
    } finally {
      state.loading = false
    }
  }

  // === Actions principales ===
  async function fetchProjetsGlobaux(force = false) {
    // Cache simple : ne recharge que si nécessaire
    if (!force && state.lastFetch && (Date.now() - state.lastFetch.getTime()) < 30000) {
      return state.projetsGlobaux
    }

    return updateLoadingState(async () => {
      const response = await axios.get(`${baseUrl}/projets/tree`)
      state.projetsGlobaux = response.data.projets_global
      return state.projetsGlobaux
    })
  }

  async function createProjetGlobal(data: {
    projet: string
    sous_projet: string
    client?: number | null
  }) {
    return updateLoadingState(async () => {
      const response = await axios.post(`${baseUrl}/projets-global`, data)
      showToast('Projet global créé avec succès', '#10b981')
      await fetchProjetsGlobaux(true)
      return response.data
    })
  }

  async function createProjet(data: {
    nom: string
    fpack_id?: number | null
    id_global?: number | null
  }) {
    return updateLoadingState(async () => {
      const response = await axios.post(`${baseUrl}/projets`, data)
      showToast('Projet créé avec succès', '#10b981')
      await fetchProjetsGlobaux(true)
      return response.data
    })
  }

  async function updateProjetGlobal(id: number, data: {
    projet: string
    sous_projet?: string
    client: number
  }) {
    return updateLoadingState(async () => {
      const response = await axios.put(`${baseUrl}/projets-global/${id}`, data)
      showToast('Projet global mis à jour', '#10b981')
      await fetchProjetsGlobaux(true)
      return response.data
    })
  }

  async function deleteProjetGlobal(id: number) {
    return updateLoadingState(async () => {
      const projetGlobal = state.projetsGlobaux.find(pg => pg.id === id)
      const nom = projetGlobal?.projet || `Projet ${id}`
      
      await axios.delete(`${baseUrl}/projets-global/${id}`)
      showToast(`Projet global "${nom}" supprimé`, '#10b981')
      await fetchProjetsGlobaux(true)
    })
  }

  async function deleteProjet(id: number) {
    return updateLoadingState(async () => {
      const projet = getProjetById(id)
      const nom = projet?.nom || `Projet ${id}`
      
      const response = await axios.delete(`${baseUrl}/projets/${id}`)
      
      // Message personnalisé avec info sur les sélections supprimées
      const selectionsMsg = response.data.selections_supprimees > 0 
        ? ` (${response.data.selections_supprimees} sélections supprimées)` 
        : ''
      
      showToast(`Projet "${nom}" supprimé${selectionsMsg}`, '#10b981')
      await fetchProjetsGlobaux(true)
      
      // Si c'était le projet courant, le déselectionner
      if (state.currentProjetId === id) {
        state.currentProjetId = null
      }
      
      return response.data
    })
  }

  async function getProjetDetails(id: number): Promise<ProjetDetails> {
    return updateLoadingState(async () => {
      const response = await axios.get(`${baseUrl}/projets/${id}/details`)
      return response.data
    })
  }

  async function saveProjetSelections(id: number, selections: any[]) {
    return updateLoadingState(async () => {
      const response = await axios.put(`${baseUrl}/projets/${id}/selections`, {
        selections
      })
      
      showToast(
        `${response.data.nouveau_nombre} sélections enregistrées`, 
        '#10b981'
      )
      
      // Rafraîchir les données pour mettre à jour les stats
      await fetchProjetsGlobaux(true)
      return response.data
    })
  }

  async function getProjetFacture(id: number) {
    return updateLoadingState(async () => {
      const response = await axios.get(`${baseUrl}/projets/${id}/facture`)
      return response.data
    })
  }

  // === Actions utilitaires ===
  function setCurrentProjet(id: number | null) {
    state.currentProjetId = id
  }

  function getProjetById(id: number): Projet | undefined {
    return allProjets.value.find(p => p.id === id)
  }

  function getProjetGlobalById(id: number): ProjetGlobal | undefined {
    return state.projetsGlobaux.find(pg => pg.id === id)
  }

  function getProjetsOfGlobal(globalId: number): Projet[] {
    const projetGlobal = getProjetGlobalById(globalId)
    return projetGlobal?.projets || []
  }

  function searchProjets(query: string): Projet[] {
    if (!query.trim()) return allProjets.value
    
    const searchLower = query.toLowerCase()
    return allProjets.value.filter(projet => 
      projet.nom.toLowerCase().includes(searchLower) ||
      projet.fpack_nom?.toLowerCase().includes(searchLower) ||
      projet.client_nom?.toLowerCase().includes(searchLower)
    )
  }

  function searchProjetsGlobaux(query: string): ProjetGlobal[] {
    if (!query.trim()) return state.projetsGlobaux
    
    const searchLower = query.toLowerCase()
    return state.projetsGlobaux.filter(pg => 
      pg.projet.toLowerCase().includes(searchLower) ||
      pg.sous_projet?.toLowerCase().includes(searchLower) ||
      pg.client_nom.toLowerCase().includes(searchLower) ||
      pg.projets.some(p => 
        p.nom.toLowerCase().includes(searchLower) ||
        p.fpack_nom?.toLowerCase().includes(searchLower)
      )
    )
  }

  // Reset des données (utile pour les tests ou déconnexion)
  function resetState() {
    state.projetsGlobaux = []
    state.currentProjetId = null
    state.lastFetch = null
    state.error = null
    state.loading = false
  }

  return {
    // État
    projetsGlobaux: computed(() => state.projetsGlobaux),
    loading: computed(() => state.loading),
    error: computed(() => state.error),
    lastFetch: computed(() => state.lastFetch),
    
    // Computed
    allProjets,
    projetsParClient,
    currentProjet,
    projetsByStatus,
    globalStats,
    
    // Actions principales
    fetchProjetsGlobaux,
    createProjetGlobal,
    createProjet,
    updateProjetGlobal,
    deleteProjetGlobal,
    deleteProjet,
    getProjetDetails,
    saveProjetSelections,
    getProjetFacture,
    
    // Actions utilitaires
    setCurrentProjet,
    getProjetById,
    getProjetGlobalById,
    getProjetsOfGlobal,
    searchProjets,
    searchProjetsGlobaux,
    resetState
  }
}

