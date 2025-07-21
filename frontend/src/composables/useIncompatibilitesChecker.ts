import { ref } from 'vue'
import axios from 'axios'

type GroupItem = {
  type: 'produit' | 'equipement' | 'robot'
  ref_id: number
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
  const robotProduitIncompatibilites = ref<{ robot_id: number; produit_id: number }[]>([])
  const equipementsWithProduits = ref<Record<number, { produit_id: number }[]>>({})

  async function loadIncompatibilites() {
    const [eqwithprod, prodIncomp, robotIncomp] = await Promise.all([
      axios.get('http://localhost:8000/equipementproduits'),
      axios.get('http://localhost:8000/produit-incompatibilites'),
      axios.get('http://localhost:8000/robot-produit-incompatibilites')
    ])
    produitIncompatibilites.value = prodIncomp.data
    robotProduitIncompatibilites.value = robotIncomp.data
    equipementsWithProduits.value = eqwithprod.data
  }

function getProduitsFromEquipement(eqId: number): number[] {
  return equipementsWithProduits.value[eqId]?.map(ep => ep.produit_id) ?? []
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
    console.log('produits:', getAllProduitsWithoutGroup(columns() ))
  const currentProduits = getAllProduitsWithoutGroup(columns())
  return produitIncompatibilites.value.some(
    inc =>
      (inc.produit_id_1 === prodId && currentProduits.includes(inc.produit_id_2)) ||
      (inc.produit_id_2 === prodId && currentProduits.includes(inc.produit_id_1))
  )
  }

  function isEquipementIncompatible(eqId: number): boolean {
    console.log('produits2:', getAllProduitsWithoutGroup(columns()))
    const produits = getProduitsFromEquipement(eqId)
    console.log('produits de l\'équipement:', getProduitsFromEquipement(eqId))
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
    return robotProduitIncompatibilites.value.some(
      inc => inc.robot_id === robotId && currentProduits.includes(inc.produit_id))
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
    const incompatibilityLevel = produitsGroupe.filter(pid => isProduitIncompatibleWithGroup(pid)).length + ((robotsGroupe.filter(rid => robotProduitIncompatibilites.value.some(inc => inc.robot_id === rid && autresProduits.includes(inc.produit_id))).length) || 0)
    return incompatibilityLevel
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

    return level === col.group_items.length // PEUT ETRE A MODIFIER APRES TESTS
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
          produitsB.some(p =>
            robotProduitIncompatibilites.value.some(inc => inc.robot_id === r && inc.produit_id === p)
          )
        ) ||
        robotsB.some(r =>
          produitsA.some(p =>
            robotProduitIncompatibilites.value.some(inc => inc.robot_id === r && inc.produit_id === p)
          )
        )

      if (produitConflict || robotConflict) {
        conflictIds.add(i)
        conflictIds.add(j)
      }
    }
  }

  return Array.from(conflictIds)
}

function getFullyConflictingGroups(columns: ConfigColumn[]): number[] {
  const conflicts: number[] = []

  const getProduitsAndRobotsFromCol = (col: ConfigColumn): { produits: number[]; robots: number[] } => {
    const produits: number[] = []
    const robots: number[] = []

    if (col.type === 'produit') produits.push(col.ref_id)
    else if (col.type === 'equipement') produits.push(...getProduitsFromEquipement(col.ref_id))
    else if (col.type === 'group') {
      for (const item of col.group_items ?? []) {
        if (item.type === 'produit') produits.push(item.ref_id)
        else if (item.type === 'equipement') produits.push(...getProduitsFromEquipement(item.ref_id))
        else if (item.type === 'robot') robots.push(item.ref_id)
      }
    }

    return { produits, robots }
  }

  for (let i = 0; i < columns.length; i++) {
    const col = columns[i]
    if (col.type !== 'group' || !col.group_items) continue

    const groupItems = col.group_items
    const groupProduits = groupItems.flatMap(item =>
      item.type === 'produit' ? [item.ref_id] :
      item.type === 'equipement' ? getProduitsFromEquipement(item.ref_id) : []
    )
    const groupRobots = groupItems.filter(i => i.type === 'robot').map(i => i.ref_id)

    const otherCols = columns.filter((_, j) => j !== i)
    const otherProduits = otherCols.flatMap(c => getProduitsAndRobotsFromCol(c).produits)

    const produitConflict = groupProduits.every(p =>
      otherProduits.some(op =>
        produitIncompatibilites.value.some(inc =>
          (inc.produit_id_1 === p && inc.produit_id_2 === op) ||
          (inc.produit_id_2 === p && inc.produit_id_1 === op)
        )
      )
    )

    const robotConflict = groupRobots.every(r =>
      otherProduits.some(p =>
        robotProduitIncompatibilites.value.some(inc => inc.robot_id === r && inc.produit_id === p)
      )
    )

    if (groupProduits.length > 0 && produitConflict || groupRobots.length > 0 && robotConflict) {
      conflicts.push(i)
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
    isRobotIncompatibleWithGroup
  }

}

