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

export function useIncompatibilitesChecker(columns: () => ConfigColumn[]) {
  const produitIncompatibilites = ref<{ produit_id_1: number, produit_id_2: number }[]>([])
  const robotProduitIncompatibilites = ref<{ robot_id: number, produit_id: number }[]>([])

  async function loadIncompatibilites() {
    const [prodIncomp, robotIncomp] = await Promise.all([
      axios.get('http://localhost:8000/produit-incompatibilites'),
      axios.get('http://localhost:8000/robot-produit-incompatibilites')
    ])
    produitIncompatibilites.value = prodIncomp.data
    robotProduitIncompatibilites.value = robotIncomp.data
  }

  function getProduitsFromEquipement(eqId: number, equipements: any[]): number[] {
    const eq = equipements.find((e: any) => e.id === eqId)
    return eq?.equipement_produit?.map((ep: any) => ep.produit_id) ?? []
  }

  function summarizeGroupItems(items: GroupItem[]) {
    const summary = { produit: 0, equipement: 0, robot: 0 }
    items.forEach(item => summary[item.type]++)
    return summary
    }


  function getAllProduits(cols: ConfigColumn[], equipements: any[]): number[] {
    const result: number[] = []
    for (const col of cols) {
      if (col.type === 'produit') result.push(col.ref_id)
      else if (col.type === 'equipement') result.push(...getProduitsFromEquipement(col.ref_id, equipements))
      else if (col.type === 'group') {
        for (const item of col.group_items ?? []) {
          if (item.type === 'produit') result.push(item.ref_id)
          else if (item.type === 'equipement') result.push(...getProduitsFromEquipement(item.ref_id, equipements))
        }
      }
    }
    return result
  }

function areAllItemsInGroupIncompatible(
  groupItems: GroupItem[],
  equipements: any[]
): boolean {
  // Filtrer columns pour exclure tous les items du groupe courant
  const filteredColumns = columns().filter(col => {
    if (col.type !== 'group') return true
    if (!col.group_items) return true

    // Exclure ce groupe s'il a exactement les mêmes items
    return col.group_items !== groupItems
  })

  const currentProduits = getAllProduits(filteredColumns, equipements)

  // Extraire tous les robots hors du groupe en cours
  const robotsInConfig: number[] = []
  for (const col of filteredColumns) {
    if (col.type === 'group' && col.group_items) {
      for (const item of col.group_items) {
        if (item.type === 'robot') {
          robotsInConfig.push(item.ref_id)
        }
      }
    }
  }

  return groupItems.every(item => {
    if (item.type === 'produit') {
      const isIncompWithProduits = produitIncompatibilites.value.some(inc =>
        (inc.produit_id_1 === item.ref_id && currentProduits.includes(inc.produit_id_2)) ||
        (inc.produit_id_2 === item.ref_id && currentProduits.includes(inc.produit_id_1))
      )

      const isIncompWithRobots = robotProduitIncompatibilites.value.some(inc =>
        inc.produit_id === item.ref_id && robotsInConfig.includes(inc.robot_id)
      )

      return isIncompWithProduits || isIncompWithRobots
    }

    if (item.type === 'equipement') {
      const produitsEq = getProduitsFromEquipement(item.ref_id, equipements)
      return produitsEq.every(pid =>
        produitIncompatibilites.value.some(inc =>
          (inc.produit_id_1 === pid && currentProduits.includes(inc.produit_id_2)) ||
          (inc.produit_id_2 === pid && currentProduits.includes(inc.produit_id_1))
        )
      )
    }

    if (item.type === 'robot') {
      return robotProduitIncompatibilites.value.some(inc =>
        inc.robot_id === item.ref_id && currentProduits.includes(inc.produit_id)
      )
    }

    return false
  })
}


function wouldCauseOtherGroupConflicts(
  newGroupItems: GroupItem[],
  equipements: any[],
  currentEditingGroupIndex: number | null = null
): boolean {
  const simulatedGroup: ConfigColumn = {
    type: 'group',
    ref_id: -1,
    ordre: columns().length,
    display_name: 'Simulation',
    group_items: newGroupItems,
    group_summary: summarizeGroupItems(newGroupItems)
  }
  const simulatedColumns = [...columns()]
  if (currentEditingGroupIndex !== null) {
    simulatedColumns[currentEditingGroupIndex] = simulatedGroup
  } else {
    simulatedColumns.push(simulatedGroup)
  }

  return simulatedColumns.some((col, index) => {
    if (col.type !== 'group' || !col.group_items) return false


    const groupProduits: number[] = []
    const groupRobots: number[] = []
    col.group_items.forEach(item => {
      if (item.type === 'produit') groupProduits.push(item.ref_id)
      else if (item.type === 'equipement') groupProduits.push(...getProduitsFromEquipement(item.ref_id, equipements))
      else if (item.type === 'robot') groupRobots.push(item.ref_id)
    })

    // Reconstituer tous les produits et robots du reste de la config (en excluant le groupe actuel qu’on teste)
    const autresColonnes = simulatedColumns.filter((_, i) => i !== index)
    const produitsConfig = getAllProduits(autresColonnes, equipements)

    const robotsConfig: number[] = []
    autresColonnes.forEach(c => {
      if (c.type === 'group' && c.group_items) {
        c.group_items.forEach(item => {
          if (item.type === 'robot') robotsConfig.push(item.ref_id)
        })
      }
    })

    const isTotallyIncompatible = col.group_items.every(item => {
      if (item.type === 'produit') {
        const produitId = item.ref_id
        const incompProd = produitIncompatibilites.value.some(inc =>
          (inc.produit_id_1 === produitId && produitsConfig.includes(inc.produit_id_2)) ||
          (inc.produit_id_2 === produitId && produitsConfig.includes(inc.produit_id_1))
        )
        const incompRobot = robotProduitIncompatibilites.value.some(inc =>
          inc.produit_id === produitId && robotsConfig.includes(inc.robot_id)
        )
        return incompProd || incompRobot
      }
    console.log(item.type)
      if (item.type === 'equipement') {
        const produits = getProduitsFromEquipement(item.ref_id, equipements)
        console.log(produits)
        return produits.some(pid =>
          produitIncompatibilites.value.some(inc =>
            (inc.produit_id_1 === pid && produitsConfig.includes(inc.produit_id_2)) ||
            (inc.produit_id_2 === pid && produitsConfig.includes(inc.produit_id_1))
          )
        )
      }

    if (item.type === 'robot') {
    const incompRobot = robotProduitIncompatibilites.value.some(inc =>
        inc.robot_id === item.ref_id && produitsConfig.includes(inc.produit_id)
    )
    const incompProduitVersRobot = robotProduitIncompatibilites.value.some(inc =>
        inc.produit_id && produitsConfig.includes(inc.produit_id) && inc.robot_id === item.ref_id
    )
    return incompRobot || incompProduitVersRobot
    }

      return false
    })

    return isTotallyIncompatible
  })
}





  function isProduitIncompatible(prodId: number, equipements: any[]): boolean {
    const currentProduits = getAllProduits(columns(), equipements)
    return produitIncompatibilites.value.some(
      inc =>
        (inc.produit_id_1 === prodId && currentProduits.includes(inc.produit_id_2)) ||
        (inc.produit_id_2 === prodId && currentProduits.includes(inc.produit_id_1))
    )
  }

  function isEquipementIncompatible(eqId: number, equipements: any[]): boolean {
    const produits = getProduitsFromEquipement(eqId, equipements)
    return produits.some(pid => isProduitIncompatible(pid, equipements))
  }

function isGroupIncompatible(groupItems: GroupItem[], equipements: any[]): boolean {
  const produitsGroupe: number[] = []
  const robotsGroupe: number[] = []

  for (const item of groupItems) {
    if (item.type === 'produit') {
      produitsGroupe.push(item.ref_id)
    } else if (item.type === 'equipement') {
      produitsGroupe.push(...getProduitsFromEquipement(item.ref_id, equipements))
    } else if (item.type === 'robot') {
      robotsGroupe.push(item.ref_id)
    }
  }

  // Produits présents dans la config (hors groupes)
  const autresProduits = getAllProduits(columns().filter(col => col.type !== 'group'), equipements)

  // Produits des autres groupes de la config (hors ce groupe-ci)
  const produitsAutresGroupes: number[] = []
  const robotsAutresGroupes: number[] = []

  for (const col of columns()) {
    if (col.type === 'group' && col.group_items) {
      for (const item of col.group_items) {
        if (item.type === 'produit') {
          produitsAutresGroupes.push(item.ref_id)
        } else if (item.type === 'equipement') {
          produitsAutresGroupes.push(...getProduitsFromEquipement(item.ref_id, equipements))
        } else if (item.type === 'robot') {
          robotsAutresGroupes.push(item.ref_id)
        }
      }
    }
  }

  // Vérification des conflits produit ↔ produit
  const conflitProduitProduit =
    produitsGroupe.some(pid =>
      produitIncompatibilites.value.some(
        inc =>
          (inc.produit_id_1 === pid && (autresProduits.includes(inc.produit_id_2) || produitsAutresGroupes.includes(inc.produit_id_2))) ||
          (inc.produit_id_2 === pid && (autresProduits.includes(inc.produit_id_1) || produitsAutresGroupes.includes(inc.produit_id_1)))
      )
    )

  // Vérification des conflits robot ↔ produits de la config (hors groupe)
  const conflitRobotProduit =
    robotsGroupe.some(rid =>
      robotProduitIncompatibilites.value.some(
        inc => inc.robot_id === rid && (autresProduits.includes(inc.produit_id) || produitsAutresGroupes.includes(inc.produit_id))
      )
    )

  return conflitProduitProduit || conflitRobotProduit
}



  function hasDirectConflict(prodId: number, equipements: any[]): boolean {
    const autres = columns().filter(col => col.type !== 'group')
    const produitsHorsGroupes = getAllProduits(autres, equipements)
    return produitIncompatibilites.value.some(
      inc =>
        (inc.produit_id_1 === prodId && produitsHorsGroupes.includes(inc.produit_id_2)) ||
        (inc.produit_id_2 === prodId && produitsHorsGroupes.includes(inc.produit_id_1))
    )
  }

  function hasGroupConflict(prodId: number, equipements: any[]): boolean {
    const groupes = columns().filter(col => col.type === 'group')
    const produitsGroupes = getAllProduits(groupes, equipements)
    return produitIncompatibilites.value.some(
      inc =>
        (inc.produit_id_1 === prodId && produitsGroupes.includes(inc.produit_id_2)) ||
        (inc.produit_id_2 === prodId && produitsGroupes.includes(inc.produit_id_1))
    )
  }

  return {
    loadIncompatibilites,
    isProduitIncompatible,
    isEquipementIncompatible,
    isGroupIncompatible,
    hasDirectConflict,
    hasGroupConflict,
    getProduitsFromEquipement,
    areAllItemsInGroupIncompatible,
    wouldCauseOtherGroupConflicts
  }
}
