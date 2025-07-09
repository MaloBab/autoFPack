import { ref } from 'vue'
import axios from 'axios'

type GroupItem = {
  type: 'produit' | 'equipement' | 'robot'
  ref_id: number
}

type ConfigColumn = {
  type: 'produit' | 'equipement' | 'group'
  ref_id: number
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
    getProduitsFromEquipement
  }
}
