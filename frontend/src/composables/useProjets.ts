import {computed, reactive } from 'vue'
import axios from 'axios'
import { showToast } from './useToast'

export interface ProjetGlobal {
  id: number
  projet: string
  sous_projet?: string
  client: number
  client_nom: string
  projets: Sous_Projet[]
  stats?: {
    nb_projets: number
    nb_projets_complets: number
    nb_projets_en_cours: number
    progression_globale: number
    total_groupes: number
    total_selections: number
  }
}

export interface Sous_Projet {
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

function isValidProjet(projet: any): projet is Sous_Projet {
  return projet && 
         typeof projet === 'object' && 
         typeof projet.id === 'number' && 
         typeof projet.nom === 'string' &&
         typeof projet.complet === 'boolean'
}

function isValidProjetGlobal(pg: any): pg is ProjetGlobal {
  return pg && 
         typeof pg === 'object' && 
         typeof pg.id === 'number' && 
         Array.isArray(pg.projets)
}

const state = reactive({
  projetsGlobaux: [] as ProjetGlobal[],
  loading: false,
  currentProjetId: null as number | null,
  lastFetch: null as Date | null,
  error: null as string | null
})

export function useProjets() {
  const baseUrl = 'http://localhost:8000'

  const allProjets = computed(() => {
    try {
      return state.projetsGlobaux
        .filter(isValidProjetGlobal)
        .flatMap(pg => pg.projets?.filter(isValidProjet) || [])
    } catch (error) {
      console.error('Error in allProjets computed:', error)
      return []
    }
  })

  const currentProjet = computed(() => {
    try {
      const projets = allProjets.value
      return projets.find(p => p?.id === state.currentProjetId) || null
    } catch (error) {
      return null
    }
  })

  const projetsParClient = computed(() => {
    try {
      const map = new Map<number, Sous_Projet[]>()
      const validProjetsGlobaux = state.projetsGlobaux.filter(isValidProjetGlobal)
      
      for (const pg of validProjetsGlobaux) {
        if (typeof pg.client === 'number') {
          if (!map.has(pg.client)) map.set(pg.client, [])
          const validProjets = pg.projets?.filter(isValidProjet) || []
          map.get(pg.client)?.push(...validProjets)
        }
      }
      return map
    } catch (error) {
      console.error('Error in projetsParClient computed:', error)
      return new Map()
    }
  })

  const projetsByStatus = computed(() => {
    try {
      const projets = allProjets.value
      return {
        complets: projets.filter(p => isValidProjet(p) && p.complet === true),
        enCours: projets.filter(p => isValidProjet(p) && p.complet === false),
        total: projets.length
      }
    } catch (error) {
      console.error('Error in projetsByStatus computed:', error)
      return {
        complets: [],
        enCours: [],
        total: 0
      }
    }
  })

  const globalStats = computed(() => {
    try {
      const validProjetsGlobaux = state.projetsGlobaux.filter(isValidProjetGlobal)
      const projets = allProjets.value
      
      const stats = {
        nb_projets_globaux: validProjetsGlobaux.length,
        nb_projets_total: projets.length,
        nb_projets_complets: 0,
        progression_moyenne: 0
      }

      if (projets.length > 0) {
        stats.nb_projets_complets = projets.filter(p => 
          isValidProjet(p) && p.complet === true
        ).length
        
        const totalProgression = projets.reduce((sum, p) => {
          if (isValidProjet(p) && typeof p.progression_percent === 'number') {
            return sum + p.progression_percent
          }
          return sum
        }, 0)
        
        stats.progression_moyenne = Math.round(totalProgression / projets.length)
      }

      return stats
    } catch (error) {
      console.error('Error in globalStats computed:', error)
      return {
        nb_projets_globaux: 0,
        nb_projets_total: 0,
        nb_projets_complets: 0,
        progression_moyenne: 0
      }
    }
  })

  const updateLoadingState = async <T>(operation: () => Promise<T>): Promise<T> => {
    state.loading = true
    state.error = null
    try {
      const result = await operation()
      state.lastFetch = new Date()
      return result
    } catch (error: any) {
      state.error = error?.message || 'Une erreur est survenue'
      console.error('Operation error:', error)
      throw error
    } finally {
      state.loading = false
    }
  }

  async function fetchProjetsGlobaux(force = false) {
    if (!force && state.lastFetch && (Date.now() - state.lastFetch.getTime()) < 20000) {
      return state.projetsGlobaux
    }

    return updateLoadingState(async () => {
      try {
        const response = await axios.get(`${baseUrl}/sous_projets/tree`)
        const projetsGlobauxData = response.data?.projets_global
        
        if (!Array.isArray(projetsGlobauxData)) {
          console.warn('Invalid data structure received:', response.data)
          state.projetsGlobaux = []
          return []
        }

        const cleanedData = projetsGlobauxData.map((pg: any) => ({
          ...pg,
          projets: Array.isArray(pg.sous_projets)
            ? pg.sous_projets.map((sp: any) => ({
                id: sp.id,
                nom: sp.nom,
                fpack_id: sp.fpack_id,
                id_global: sp.id_global,
                fpack_nom: sp.fpack_nom,
                client_nom: sp.client_nom,
                complet: sp.complet,
                nb_selections: sp.nb_selections,
                nb_groupes_attendus: sp.nb_groupes_attendus,
                progression_percent: sp.nb_groupes_attendus
                  ? Math.round((sp.nb_selections / sp.nb_groupes_attendus) * 100)
                  : 0
              }))
            : []
        }))

        state.projetsGlobaux = cleanedData.filter(isValidProjetGlobal)
        return state.projetsGlobaux
      } catch (error) {
        console.error('Error fetching projets globaux:', error)
        throw error
      }
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
      const response = await axios.post(`${baseUrl}/sous_projets`, data)
      showToast('Projet créé avec succès', '#10b981')
      await fetchProjetsGlobaux(true)
      return response.data
    })
  }

  async function updateProjetGlobal(id: number, data: {
    projet: string
    sous_projet?: string
    client: number | null
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
      const projetGlobal = state.projetsGlobaux.find(pg => pg?.id === id)
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
      
      const response = await axios.delete(`${baseUrl}/sous_projets/${id}`)
      
      const selectionsMsg = response.data?.selections_supprimees > 0 
        ? ` (${response.data.selections_supprimees} sélections supprimées)` 
        : ''
      
      showToast(`Projet "${nom}" supprimé${selectionsMsg}`, '#10b981')
      await fetchProjetsGlobaux(true)
      
      if (state.currentProjetId === id) {
        state.currentProjetId = null
      }
      
      return response.data
    })
  }

  async function getProjetDetails(id: number): Promise<ProjetDetails> {
    return updateLoadingState(async () => {
      const response = await axios.get(`${baseUrl}/sous_projets/${id}/details`)
      return response.data
    })
  }

  async function saveProjetSelections(id: number, selections: any[]) {
    return updateLoadingState(async () => {
      const response = await axios.put(`${baseUrl}/sous_projets/${id}/selections`, {
        selections
      })
      
      showToast(
        `${response.data?.nouveau_nombre || 0} sélections enregistrées`, 
        '#10b981'
      )
      
      await fetchProjetsGlobaux(true)
      return response.data
    })
  }

  async function getProjetFacture(id: number) {
    return updateLoadingState(async () => {
      const response = await axios.get(`${baseUrl}/sous_projets/${id}/facture`)
      return response.data
    })
  }

  function setCurrentProjet(id: number | null) {
    state.currentProjetId = id
  }

  function getProjetById(id: number): Sous_Projet | undefined {
    try {
      return allProjets.value.find(p => isValidProjet(p) && p.id === id)
    } catch (error) {
      console.error('Error in getProjetById:', error)
      return undefined
    }
  }

  function getProjetGlobalById(id: number): ProjetGlobal | undefined {
    try {
      return state.projetsGlobaux.find(pg => isValidProjetGlobal(pg) && pg.id === id)
    } catch (error) {
      console.error('Error in getProjetGlobalById:', error)
      return undefined
    }
  }

  function getProjetsOfGlobal(globalId: number): Sous_Projet[] {
    try {
      const projetGlobal = getProjetGlobalById(globalId)
      return projetGlobal?.projets?.filter(isValidProjet) || []
    } catch (error) {
      console.error('Error in getProjetsOfGlobal:', error)
      return []
    }
  }

  function searchProjets(query: string): Sous_Projet[] {
    try {
      if (!query?.trim()) return allProjets.value
      
      const searchLower = query.toLowerCase()
      return allProjets.value.filter(projet => {
        if (!isValidProjet(projet)) return false
        
        return projet.nom?.toLowerCase().includes(searchLower) ||
               projet.fpack_nom?.toLowerCase().includes(searchLower) ||
               projet.client_nom?.toLowerCase().includes(searchLower)
      })
    } catch (error) {
      console.error('Error in searchProjets:', error)
      return []
    }
  }

  function searchProjetsGlobaux(query: string): ProjetGlobal[] {
    try {
      if (!query?.trim()) return state.projetsGlobaux
      
      const searchLower = query.toLowerCase()
      return state.projetsGlobaux.filter(pg => {
        if (!isValidProjetGlobal(pg)) return false
        
        return pg.projet?.toLowerCase().includes(searchLower) ||
               pg.sous_projet?.toLowerCase().includes(searchLower) ||
               pg.client_nom?.toLowerCase().includes(searchLower) ||
               pg.projets?.some(p => 
                 isValidProjet(p) && (
                   p.nom?.toLowerCase().includes(searchLower) ||
                   p.fpack_nom?.toLowerCase().includes(searchLower)
                 )
               )
      })
    } catch (error) {
      console.error('Error in searchProjetsGlobaux:', error)
      return []
    }
  }

  function resetState() {
    state.projetsGlobaux = []
    state.currentProjetId = null
    state.lastFetch = null
    state.error = null
    state.loading = false
  }

  return {
    projetsGlobaux: computed(() => state.projetsGlobaux),
    loading: computed(() => state.loading),
    error: computed(() => state.error),
    lastFetch: computed(() => state.lastFetch),
    allProjets,
    projetsParClient,
    currentProjet,
    projetsByStatus,
    globalStats,
    fetchProjetsGlobaux,
    createProjetGlobal,
    createProjet,
    updateProjetGlobal,
    deleteProjetGlobal,
    deleteProjet,
    getProjetDetails,
    saveProjetSelections,
    getProjetFacture,
    setCurrentProjet,
    getProjetById,
    getProjetGlobalById,
    getProjetsOfGlobal,
    searchProjets,
    searchProjetsGlobaux,
    resetState
  }
}
