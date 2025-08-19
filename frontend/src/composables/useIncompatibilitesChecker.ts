import { ref } from 'vue'
import axios from 'axios'

type GroupItem = {
  type: 'produit' | 'equipement' | 'robot'
  ref_id: number
  statut?: 'optionnel' | 'standard'
}

type ConfigColumn = {
  type: 'produit' | 'equipement' | 'group'
  ref_id: number
  ordre: number
  display_name: string
  type_detail?: string
  description?: string
  fournisseur_nom?: string
  produits_count?: number
  group_summary?: {
    produit: number
    equipement: number
    robot: number
  }
  group_items?: GroupItem[]
}

// Utilitaires
function areGroupItemsEqual(a: GroupItem[], b: GroupItem[]): boolean {
  if (a.length !== b.length) return false
  const normalize = (items: GroupItem[]) =>
    items.map(item => `${item.type}-${item.ref_id}`).sort()
  const [normA, normB] = [normalize(a), normalize(b)]
  return normA.every((val, index) => val === normB[index])
}

// Types pour les Sets optimisés
type IncompatibilityKey = string // "produit1_id-produit2_id"
type CompatibilityKey = string   // "robot_id-produit_id"

export function useIncompatibilitesChecker(columns: () => ConfigColumn[]) {
  // Stockage optimisé avec Sets pour O(1) lookup
  const produitIncompatibilites = ref<Set<IncompatibilityKey>>(new Set())
  const robotProduitCompatibilites = ref<Set<CompatibilityKey>>(new Set())
  const equipementsWithProduits = ref<Map<number, number[]>>(new Map())

  // Cache pour éviter les recalculs
  const produitsCache = ref<Map<string, number[]>>(new Map())

  async function loadIncompatibilites() {
    const [eqwithprod, prodIncomp, robotCompat] = await Promise.all([
      axios.get('http://localhost:8000/equipementproduits'),
      axios.get('http://localhost:8000/produit-incompatibilites'),
      axios.get('http://localhost:8000/robot-produit-compatibilites') 
    ])

    // Optimisation: utiliser Set et Map pour O(1) lookup
    prodIncomp.data.forEach(({ produit_id_1, produit_id_2 }: any) => {
      const key1 = `${Math.min(produit_id_1, produit_id_2)}-${Math.max(produit_id_1, produit_id_2)}`
      produitIncompatibilites.value.add(key1)
    })

    robotCompat.data.forEach(({ robot_id, produit_id }: any) => {
      robotProduitCompatibilites.value.add(`${robot_id}-${produit_id}`)
    })

    Object.entries(eqwithprod.data).forEach(([eqId, produits]: [string, any]) => {
      equipementsWithProduits.value.set(Number(eqId), produits.map((p: any) => p.produit_id))
    })

    // Clear cache when data changes
    produitsCache.value.clear()
  }

  // === UTILITAIRES DE BASE ===
  
  function getProduitsFromEquipement(eqId: number): number[] {
    return equipementsWithProduits.value.get(eqId) ?? []
  }

  function isRobotCompatibleWithProduit(robotId: number, produitId: number): boolean {
    return robotProduitCompatibilites.value.has(`${robotId}-${produitId}`)
  }

  function areProduitsIncompatible(prodId1: number, prodId2: number): boolean {
    const key = `${Math.min(prodId1, prodId2)}-${Math.max(prodId1, prodId2)}`
    return produitIncompatibilites.value.has(key)
  }

  // === EXTRACTION DE PRODUITS (avec cache) ===
  
  function getProduitsFromColumns(cols: ConfigColumn[], includeGroups = true): number[] {
    const cacheKey = JSON.stringify({ cols: cols.map(c => ({ type: c.type, ref_id: c.ref_id, group_items: c.group_items })), includeGroups })
    
    if (produitsCache.value.has(cacheKey)) {
      return produitsCache.value.get(cacheKey)!
    }

    const produits = new Set<number>()
    
    for (const col of cols) {
      if (col.type === 'produit') {
        produits.add(col.ref_id)
      } else if (col.type === 'equipement') {
        getProduitsFromEquipement(col.ref_id).forEach(p => produits.add(p))
      } else if (col.type === 'group' && includeGroups && col.group_items) {
        for (const item of col.group_items) {
          if (item.type === 'produit') {
            produits.add(item.ref_id)
          } else if (item.type === 'equipement') {
            getProduitsFromEquipement(item.ref_id).forEach(p => produits.add(p))
          }
        }
      }
    }

    const result = Array.from(produits)
    produitsCache.value.set(cacheKey, result)
    return result
  }

  function getAllProduits(cols: ConfigColumn[]): number[] {
    return getProduitsFromColumns(cols, true)
  }

  function getAllProduitsWithoutGroup(cols: ConfigColumn[]): number[] {
    return getProduitsFromColumns(cols, false)
  }

  // === COMPATIBILITÉ D'ÉLÉMENTS INDIVIDUELS ===
  
  function isItemCompatible(
    item: { type: string; ref_id: number }, 
    otherProduits: number[]
  ): boolean {
    if (otherProduits.length === 0) return true

    if (item.type === 'robot') {
      return otherProduits.every(produitId => 
        isRobotCompatibleWithProduit(item.ref_id, produitId)
      )
    }

    // Pour produits et équipements
    const itemProduits = item.type === 'produit' 
      ? [item.ref_id] 
      : getProduitsFromEquipement(item.ref_id)

    return !itemProduits.some(itemProduitId =>
      otherProduits.some(otherProduitId =>
        areProduitsIncompatible(itemProduitId, otherProduitId)
      )
    )
  }

  // === INCOMPATIBILITÉS INDIVIDUELLES ===
  
  function isProduitIncompatible(prodId: number): boolean {
    const currentProduits = getAllProduitsWithoutGroup(columns())
    return currentProduits.some(otherId => 
      otherId !== prodId && areProduitsIncompatible(prodId, otherId)
    )
  }

  function isEquipementIncompatible(eqId: number): boolean {
    const currentProduits = getAllProduitsWithoutGroup(columns())
    const eqProduits = getProduitsFromEquipement(eqId)
    return eqProduits.some(prodId =>
      currentProduits.some(otherId => areProduitsIncompatible(prodId, otherId))
    )
  }

  function isProduitIncompatibleWithGroup(prodId: number): boolean {
    const currentProduits = getAllProduits(columns())
    return currentProduits.some(otherId => 
      otherId !== prodId && areProduitsIncompatible(prodId, otherId)
    )
  }

  function isEquipementIncompatibleWithGroup(eqId: number): boolean {
    const currentProduits = getAllProduits(columns())
    const eqProduits = getProduitsFromEquipement(eqId)
    return eqProduits.some(prodId =>
      currentProduits.some(otherId => areProduitsIncompatible(prodId, otherId))
    )
  }

  function isRobotIncompatibleWithGroup(robotId: number): boolean {
    const currentProduits = getAllProduits(columns())
    return currentProduits.some(produitId => 
      !isRobotCompatibleWithProduit(robotId, produitId)
    )
  }

  // === ANALYSE DE GROUPES ===
  
  function GroupIncompatibilityLevel(groupItems: GroupItem[]): number {
    if (!groupItems.length) return 0

    const otherCols = columns().filter(col => {
      if (col.type !== 'group') return true
      return !areGroupItemsEqual(col.group_items || [], groupItems)
    })
    
    const otherProduits = getAllProduits(otherCols)
    if (!otherProduits.length) return 0
    
    return groupItems.filter(item => 
      !isItemCompatible(item, otherProduits)
    ).length
  }

  function wouldCauseOtherGroupConflicts(
    newGroupItems: GroupItem[], 
    currentEditingGroupIndex: number | null = null
  ): boolean {
    const simulatedColumns = [...columns()]
    const simulatedGroup: ConfigColumn = {
      type: 'group',
      ref_id: -1,
      ordre: simulatedColumns.length,
      display_name: 'Simulation',
      group_items: newGroupItems,
      group_summary: {
        produit: newGroupItems.filter(i => i.type === 'produit').length,
        equipement: newGroupItems.filter(i => i.type === 'equipement').length,
        robot: newGroupItems.filter(i => i.type === 'robot').length
      }
    }

    if (currentEditingGroupIndex !== null) {
      simulatedColumns[currentEditingGroupIndex] = simulatedGroup
    } else {
      simulatedColumns.push(simulatedGroup)
    }

    const conflictingGroups = getFullyConflictingGroups(simulatedColumns)
    return conflictingGroups.some(index => 
      currentEditingGroupIndex !== null 
        ? index !== currentEditingGroupIndex 
        : index < simulatedColumns.length - 1
    )
  }

  // === DÉTECTION DE CONFLITS GLOBAUX ===
  
  function getConflictingColumns(): number[] {
    const cols = columns()
    const conflicts = new Set<number>()

    // Optimisation: construire une fois les données par colonne
    const columnData = cols.map(col => ({
      produits: col.type === 'produit' ? [col.ref_id] :
                col.type === 'equipement' ? getProduitsFromEquipement(col.ref_id) :
                col.type === 'group' ? getProduitsFromColumns([col], true) : [],
      robots: col.type === 'group' ? 
        col.group_items?.filter(i => i.type === 'robot').map(i => i.ref_id) ?? [] : []
    }))

    for (let i = 0; i < cols.length; i++) {
      for (let j = i + 1; j < cols.length; j++) {
        const dataA = columnData[i]
        const dataB = columnData[j]

        // Vérifier incompatibilités produit-produit
        const hasProduitConflict = dataA.produits.some(pA =>
          dataB.produits.some(pB => areProduitsIncompatible(pA, pB))
        )

        // Vérifier incompatibilités robot-produit
        const hasRobotConflict = 
          dataA.robots.some(r => dataB.produits.some(p => !isRobotCompatibleWithProduit(r, p))) ||
          dataB.robots.some(r => dataA.produits.some(p => !isRobotCompatibleWithProduit(r, p)))

        if (hasProduitConflict || hasRobotConflict) {
          conflicts.add(i)
          conflicts.add(j)
        }
      }
    }

    return Array.from(conflicts)
  }

  // Vérifie s'il existe au moins une combinaison valide entre tous les groupes
  function hasValidCombination(groupColumns: ConfigColumn[]): boolean {
    if (groupColumns.length === 0) return true
    if (groupColumns.length === 1) {
      // Un seul groupe: valide s'il a au moins un élément utilisable
      const group = groupColumns[0]
      if (!group.group_items) return true
      return group.group_items?.some(item => item.statut !== 'optionnel') || 
             group.group_items.length > 0
    }

    // Générer toutes les combinaisons possibles entre groupes
    function generateCombinations(groups: ConfigColumn[]): GroupItem[][] {
      if (groups.length === 0) return [[]]
      
      const [firstGroup, ...restGroups] = groups
      const restCombinations = generateCombinations(restGroups)
      const combinations: GroupItem[][] = []
      
      for (const item of firstGroup.group_items || []) {
        for (const restCombination of restCombinations) {
          combinations.push([item, ...restCombination])
        }
      }
      
      return combinations
    }

    // Vérifier si une combinaison est valide
    function isCombinationValid(combination: GroupItem[]): boolean {
      const produits: number[] = []
      const robots: number[] = []
      
      // Extraire produits et robots de la combinaison
      for (const item of combination) {
        if (item.type === 'produit') {
          produits.push(item.ref_id)
        } else if (item.type === 'equipement') {
          produits.push(...getProduitsFromEquipement(item.ref_id))
        } else if (item.type === 'robot') {
          robots.push(item.ref_id)
        }
      }
      
      // Vérifier incompatibilités produit-produit
      for (let i = 0; i < produits.length; i++) {
        for (let j = i + 1; j < produits.length; j++) {
          if (areProduitsIncompatible(produits[i], produits[j])) {
            return false
          }
        }
      }
      
      // Vérifier compatibilités robot-produit
      for (const robotId of robots) {
        for (const produitId of produits) {
          if (!isRobotCompatibleWithProduit(robotId, produitId)) {
            return false
          }
        }
      }
      
      return true
    }

    // Optimisation: limiter le nombre de combinaisons à vérifier
    const maxCombinations = 1000
    const combinations = generateCombinations(groupColumns)
    
    if (combinations.length > maxCombinations) {
      // Si trop de combinaisons, utiliser un échantillonnage
      const step = Math.ceil(combinations.length / maxCombinations)
      for (let i = 0; i < combinations.length; i += step) {
        if (isCombinationValid(combinations[i])) return true
      }
      return false
    }
    
    return combinations.some(isCombinationValid)
  }

  function getFullyConflictingGroups(cols: ConfigColumn[], newColumn?: ConfigColumn): number[] {
    const allColumns = newColumn ? [...cols, newColumn] : cols
    const conflicts: number[] = []

    // Séparer les groupes des autres colonnes
    const groupColumns = allColumns.filter(col => col.type === 'group' && col.group_items?.length)
    const nonGroupColumns = allColumns.filter(col => col.type !== 'group')
    
    // Si pas de groupes, pas de conflits
    if (groupColumns.length === 0) return conflicts

    // Obtenir tous les produits des colonnes non-groupes
    const fixedProduits = getProduitsFromColumns(nonGroupColumns, false)

    // Pour chaque groupe, vérifier s'il peut coexister avec le reste
    for (let i = 0; i < groupColumns.length; i++) {
      const currentGroup = groupColumns[i]
      const otherGroups = groupColumns.filter((_, index) => index !== i)
      
      // Vérifier si le groupe actuel peut coexister avec les produits fixes
      let canCoexistWithFixed = true
      if (fixedProduits.length > 0) {
        canCoexistWithFixed = currentGroup.group_items?.some(item => 
          isItemCompatible(item, fixedProduits)
        ) || false
      }
      
      if (!canCoexistWithFixed) {
        // Le groupe ne peut pas coexister avec les éléments fixes
        const originalIndex = allColumns.findIndex(col => col === currentGroup)
        if (originalIndex < cols.length) conflicts.push(originalIndex)
        continue
      }

      // Si il y a d'autres groupes, vérifier s'il existe une combinaison valide
      if (otherGroups.length > 0) {
        const testGroups = [currentGroup, ...otherGroups]
        if (!hasValidCombination(testGroups)) {
          // Aucune combinaison valide trouvée
          const originalIndex = allColumns.findIndex(col => col === currentGroup)
          if (originalIndex < cols.length) conflicts.push(originalIndex)
        }
      }
    }

    return conflicts
  }

  return {
    loadIncompatibilites,
    isProduitIncompatible,
    isEquipementIncompatible,
    isProduitIncompatibleWithGroup,
    isEquipementIncompatibleWithGroup,
    isRobotIncompatibleWithGroup,
    isRobotCompatibleWithProduit,
    GroupIncompatibilityLevel,
    wouldCauseOtherGroupConflicts,
    getFullyConflictingGroups,
    getConflictingColumns
  }
}