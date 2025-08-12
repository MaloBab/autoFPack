// useTableNavigation.ts
import { useRouter } from 'vue-router'

export function useTableNavigation(tableName: string) {
  const router = useRouter()

  function remplirEquipement(row: any) {
    router.push(`/remplir/${tableName}/${row.id}`)
  }

  function remplirFPack(row: any) {
    router.push(`/configure/${tableName}/${row.id}`)
  }

  function remplirProjet(row: any) {
    router.push(`/complete/${tableName}/${row.id}`)
  }

  return {
    remplirEquipement,
    remplirFPack,
    remplirProjet
  }
}