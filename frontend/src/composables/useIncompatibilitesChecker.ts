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
    items
      .map(item => `${item.type}-${item.ref_id}`)
      .sort()

  const normA = normalize(a)
  const normB = normalize(b)

  return normA.every((val, index) => val === normB[index])
}

export function useIncompatibilitesChecker(columns: () => ConfigColumn[]) {
  const produitIncompatibilites = ref<{ produit_id_1: number; produit_id_2: number }[]>([])
  const robotProduitCompatibilites = ref<{ robot_id: number; produit_id: number }[]>([])
  const equipementsWithProduits = ref<Record<number, { produit_id: number }[]>>({})

  async function loadIncompatibilites() {
    const [eqwithprod, prodIncomp, robotCompat] = await Promise.all([
      axios.get('http://localhost:8000/equipementproduits'),
      axios.get('http://localhost:8000/produit-incompatibilites'),
      axios.get('http://localhost:8000/robot-produit-compatibilites') 
    ])
    produitIncompatibilites.value = prodIncomp.data
    robotProduitCompatibilites.value = robotCompat.data 
    equipementsWithProduits.value = eqwithprod.data
  }

  function getProduitsFromEquipement(eqId: number): number[] {
    return equipementsWithProduits.value[eqId]?.map(ep => ep.produit_id) ?? []
  }

  function isRobotCompatibleWithProduit(robotId: number, produitId: number): boolean {
    return robotProduitCompatibilites.value.some(
      comp => comp.robot_id === robotId && comp.produit_id === produitId
    )
  }

  function getAllProduits(cols: ConfigColumn[]): number[] {
    const result: number[] = []
    for (const col of cols) {
      if (col.type === 'produit') result.push(col.ref_id)
      else if (col.type === 'equipement') result.push(...getProduitsFromEquipement(col.ref_id))
      else if (col.type === 'group') {
        for (const item of col.group_items ?? []) {
          if (item.type === 'produit') result.push(item.ref_id)
          else if (item.type === 'equipement') result.push(...getProduitsFromEquipement(item.ref_id))
        }
      }
    }
    return result
  }

  function getAllProduitsWithoutGroup(cols: ConfigColumn[]): number[] {
    const result: number[] = []
    for (const col of cols) {
      if (col.type === 'produit') result.push(col.ref_id)
      else if (col.type === 'equipement') result.push(...getProduitsFromEquipement(col.ref_id))
    }
    return result
  }

  function isProduitIncompatible(prodId: number): boolean {
    const currentProduits = getAllProduitsWithoutGroup(columns())
    return produitIncompatibilites.value.some(
      inc =>
        (inc.produit_id_1 === prodId && currentProduits.includes(inc.produit_id_2)) ||
        (inc.produit_id_2 === prodId && currentProduits.includes(inc.produit_id_1))
    )
  }

  function isEquipementIncompatible(eqId: number): boolean {
    const produits = getProduitsFromEquipement(eqId)
    return produits.some(pid => isProduitIncompatible(pid))
  }

  function isProduitIncompatibleWithGroup(prodId: number): boolean {
    const currentProduits = getAllProduits(columns())
    return produitIncompatibilites.value.some(
      inc =>
        (inc.produit_id_1 === prodId && currentProduits.includes(inc.produit_id_2)) ||
        (inc.produit_id_2 === prodId && currentProduits.includes(inc.produit_id_1))
    )
  }

  function isEquipementIncompatibleWithGroup(eqId: number): boolean {
    const produits = getProduitsFromEquipement(eqId)
    return produits.some(pid => isProduitIncompatible(pid))
  }

  function isRobotIncompatibleWithGroup(robotId: number): boolean {
    const currentProduits = getAllProduits(columns())
    return currentProduits.some(produitId => 
      !isRobotCompatibleWithProduit(robotId, produitId)
    )
  }
  function GroupIncompatibilityLevel(groupItems: GroupItem[]): number {
    const produitsGroupe: number[] = []
    const robotsGroupe: number[] = []
    
    for (const item of groupItems) {
      if (item.type === 'produit') {
        produitsGroupe.push(item.ref_id)
      } else if (item.type === 'equipement') {
        produitsGroupe.push(...getProduitsFromEquipement(item.ref_id))
      } else if (item.type === 'robot') {
        robotsGroupe.push(item.ref_id)
      }
    }
    
    const autresCols = columns().filter(col => !(col.type === 'group' && col.group_items === groupItems))
    const autresProduits = getAllProduits(autresCols)
    
    const produitIncompatibilityCount = produitsGroupe.filter(pid => isProduitIncompatibleWithGroup(pid)).length
    
    const robotIncompatibilityCount = robotsGroupe.filter(rid => 
      autresProduits.some(produitId => !isRobotCompatibleWithProduit(rid, produitId))
    ).length
    
    return produitIncompatibilityCount + robotIncompatibilityCount
  }

  function wouldCauseOtherGroupConflicts(newGroupItems: GroupItem[], currentEditingGroupIndex: number | null = null): boolean {
    const simulatedGroup: ConfigColumn = {
      type: 'group',
      ref_id: -1,
      ordre: columns().length,
      display_name: 'Simulation',
      group_items: newGroupItems,
      group_summary: {
        produit: newGroupItems.filter(i => i.type === 'produit').length,
        equipement: newGroupItems.filter(i => i.type === 'equipement').length,
        robot: newGroupItems.filter(i => i.type === 'robot').length
      }
    }

    const simulatedColumns = [...columns()]
    if (currentEditingGroupIndex !== null) {
      simulatedColumns[currentEditingGroupIndex] = simulatedGroup
    } else {
      simulatedColumns.push(simulatedGroup)
    }

    return simulatedColumns.some((col, _index) => {
      if (col.type !== 'group' || !col.group_items || areGroupItemsEqual(col.group_items, newGroupItems)) return false

      const level = GroupIncompatibilityLevel(col.group_items)

      return level === col.group_items.length
    })
  }

  function getConflictingColumns(): number[] {
    const conflictIds = new Set<number>()
    const cols = columns()

    const getProduitsFromCol = (col: ConfigColumn): number[] => {
      if (col.type === 'produit') return [col.ref_id]
      if (col.type === 'equipement') return getProduitsFromEquipement(col.ref_id)
      if (col.type === 'group')
        return col.group_items?.flatMap(item =>
          item.type === 'produit' ? [item.ref_id] :
          item.type === 'equipement' ? getProduitsFromEquipement(item.ref_id) : []
        ) ?? []
      return []
    }

    const getRobotsFromCol = (col: ConfigColumn): number[] => {
      if (col.type === 'group')
        return col.group_items?.filter(i => i.type === 'robot').map(i => i.ref_id) ?? []
      return []
    }

    for (let i = 0; i < cols.length; i++) {
      for (let j = i + 1; j < cols.length; j++) {
        const colA = cols[i]
        const colB = cols[j]

        const produitsA = getProduitsFromCol(colA)
        const produitsB = getProduitsFromCol(colB)
        const robotsA = getRobotsFromCol(colA)
        const robotsB = getRobotsFromCol(colB)

        const produitConflict = produitsA.some(pA =>
          produitsB.some(pB =>
            produitIncompatibilites.value.some(inc =>
              (inc.produit_id_1 === pA && inc.produit_id_2 === pB) ||
              (inc.produit_id_2 === pA && inc.produit_id_1 === pB)
            )
          )
        )

        const robotConflict =
          robotsA.some(r =>
            produitsB.some(p => !isRobotCompatibleWithProduit(r, p))
          ) ||
          robotsB.some(r =>
            produitsA.some(p => !isRobotCompatibleWithProduit(r, p))
          )

        if (produitConflict || robotConflict) {
          conflictIds.add(i)
          conflictIds.add(j)
        }
      }
    }

    return Array.from(conflictIds)
  }

function getFullyConflictingGroups(columns: ConfigColumn[], newColumn?: ConfigColumn): number[] {
  const conflicts: number[] = []

  const allColumns = newColumn ? [...columns, newColumn] : columns

  for (let i = 0; i < allColumns.length; i++) {
    const currentCol = allColumns[i]
    
    if (currentCol.type !== 'group' || !currentCol.group_items || currentCol.group_items.length === 0) {
      continue
    }

    const otherColumns = allColumns.filter((_, index) => index !== i)
    
    const otherProduits: number[] = []
    
    for (const col of otherColumns) {
      
      if (col.type === 'produit') {
        otherProduits.push(col.ref_id)
      } 
      else if (col.type === 'equipement') {
        const equipProduits = getProduitsFromEquipement(col.ref_id)
        otherProduits.push(...equipProduits)
      }
      else if (col.type === 'group' && col.group_items) {
        for (const item of col.group_items) {
          if (item.type === 'produit') {
            otherProduits.push(item.ref_id)
          }
          else if (item.type === 'equipement') {
            const equipProduits = getProduitsFromEquipement(item.ref_id)
            otherProduits.push(...equipProduits)
          }
        }
      }
    }


    if (otherProduits.length === 0) {
      continue
    }

    let allItemsAreIncompatible = true

    for (let j = 0; j < currentCol.group_items.length; j++) {
      const groupItem = currentCol.group_items[j]
      
      let canThisItemCoexist = true

      if (groupItem.type === 'produit') {
        
        for (const otherProduitId of otherProduits) {
          const hasIncompatibility = produitIncompatibilites.value.some(incomp => {
            const match1 = incomp.produit_id_1 === groupItem.ref_id && incomp.produit_id_2 === otherProduitId
            const match2 = incomp.produit_id_2 === groupItem.ref_id && incomp.produit_id_1 === otherProduitId
            return match1 || match2
          })
          
          if (hasIncompatibility) {
            canThisItemCoexist = false
            break
          }
        }
      } 
      else if (groupItem.type === 'equipement') {
        const equipementProduits = getProduitsFromEquipement(groupItem.ref_id)
        
        for (const equipProduitId of equipementProduits) {
          for (const otherProduitId of otherProduits) {
            const hasIncompatibility = produitIncompatibilites.value.some(incomp => 
              (incomp.produit_id_1 === equipProduitId && incomp.produit_id_2 === otherProduitId) ||
              (incomp.produit_id_2 === equipProduitId && incomp.produit_id_1 === otherProduitId)
            )
            
            if (hasIncompatibility) {
              canThisItemCoexist = false
              break
            }
          }
          if (!canThisItemCoexist) break
        }
      }
      else if (groupItem.type === 'robot') {    
        for (const otherProduitId of otherProduits) {
          const isCompatible = isRobotCompatibleWithProduit(groupItem.ref_id, otherProduitId)
          
          if (!isCompatible) {
            canThisItemCoexist = false
            break
          }
        }
      }

      if (canThisItemCoexist) {
        allItemsAreIncompatible = false
        break
      }
    }

    if (allItemsAreIncompatible) {
      if (i < columns.length) {
        conflicts.push(i)
      }
    }
  }
  return conflicts
}

  return {
    loadIncompatibilites,
    isProduitIncompatible,
    isEquipementIncompatible,
    GroupIncompatibilityLevel,
    wouldCauseOtherGroupConflicts,
    isProduitIncompatibleWithGroup,
    isEquipementIncompatibleWithGroup,
    getFullyConflictingGroups,
    getConflictingColumns,
    isRobotIncompatibleWithGroup,
    isRobotCompatibleWithProduit
  }
}