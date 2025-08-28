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

function areGroupItemsEqual(a: GroupItem[], b: GroupItem[]): boolean {
  if (a.length !== b.length) return false
  const normalize = (items: GroupItem[]) =>
    items.map(item => `${item.type}-${item.ref_id}`).sort()
  const [normA, normB] = [normalize(a), normalize(b)]
  return normA.every((val, index) => val === normB[index])
}

type IncompatibilityKey = string
type CompatibilityKey = string   

export function useIncompatibilitesChecker(columns: () => ConfigColumn[]) {
  const produitIncompatibilites = ref<Set<IncompatibilityKey>>(new Set())
  const robotProduitCompatibilites = ref<Set<CompatibilityKey>>(new Set())
  const equipementsWithProduits = ref<Map<number, number[]>>(new Map())

  const produitsCache = ref<Map<string, number[]>>(new Map())

  async function loadIncompatibilites() {
    const [eqwithprod, prodIncomp, robotCompat] = await Promise.all([
      axios.get('http://localhost:8000/equipementproduits'),
      axios.get('http://localhost:8000/produit-incompatibilites'),
      axios.get('http://localhost:8000/robot-produit-compatibilites') 
    ])

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

    produitsCache.value.clear()
  }
  
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
        const hasProduitConflict = dataA.produits.some(pA =>
          dataB.produits.some(pB => areProduitsIncompatible(pA, pB))
        )

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

  function hasValidCombination(groupColumns: ConfigColumn[]): boolean {
    if (groupColumns.length === 0) return true
    if (groupColumns.length === 1) {
      const group = groupColumns[0]
      if (!group.group_items) return true
      return group.group_items?.some(item => item.statut !== 'optionnel') || 
             group.group_items.length > 0
    }

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

    function isCombinationValid(combination: GroupItem[]): boolean {
      const produits: number[] = []
      const robots: number[] = []
      
      for (const item of combination) {
        if (item.type === 'produit') {
          produits.push(item.ref_id)
        } else if (item.type === 'equipement') {
          produits.push(...getProduitsFromEquipement(item.ref_id))
        } else if (item.type === 'robot') {
          robots.push(item.ref_id)
        }
      }
      
      for (let i = 0; i < produits.length; i++) {
        for (let j = i + 1; j < produits.length; j++) {
          if (areProduitsIncompatible(produits[i], produits[j])) {
            return false
          }
        }
      }
      
      for (const robotId of robots) {
        for (const produitId of produits) {
          if (!isRobotCompatibleWithProduit(robotId, produitId)) {
            return false
          }
        }
      }
      
      return true
    }

    const maxCombinations = 1000
    const combinations = generateCombinations(groupColumns)
    
    if (combinations.length > maxCombinations) {
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

    const groupColumns = allColumns.filter(col => col.type === 'group' && col.group_items?.length)
    const nonGroupColumns = allColumns.filter(col => col.type !== 'group')
    
    if (groupColumns.length === 0) return conflicts

    const fixedProduits = getProduitsFromColumns(nonGroupColumns, false)

    for (let i = 0; i < groupColumns.length; i++) {
      const currentGroup = groupColumns[i]
      const otherGroups = groupColumns.filter((_, index) => index !== i)
      
      let canCoexistWithFixed = true
      if (fixedProduits.length > 0) {
        canCoexistWithFixed = currentGroup.group_items?.some(item => 
          isItemCompatible(item, fixedProduits)
        ) || false
      }
      
      if (!canCoexistWithFixed) {
        const originalIndex = allColumns.findIndex(col => col === currentGroup)
        if (originalIndex < cols.length) conflicts.push(originalIndex)
        continue
      }

      if (otherGroups.length > 0) {
        const testGroups = [currentGroup, ...otherGroups]
        if (!hasValidCombination(testGroups)) {
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