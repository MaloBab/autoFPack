//useTableConfig.ts
import { computed } from 'vue'

export function useTableConfig(tableName: string) {
  const tableConfig = computed(() => {
    const configs:any = {
      produits: { hasRemplir: false, hasDuplicate: true, hasExport: false },
      fournisseurs: { hasRemplir: false, hasDuplicate: false, hasExport: false },
      clients: { hasRemplir: false, hasDuplicate: false, hasExport: false },
      robots: { hasRemplir: false, hasDuplicate: false, hasExport: false },
      prix: { hasRemplir: false, hasDuplicate: false, hasExport: false, hasPrixEdit: true },
      prix_robot: { hasRemplir: false, hasDuplicate: false, hasExport: false },
      equipements: { hasRemplir: true, hasDuplicate: false, hasExport: false, remplirType: 'equipement' },
      fpacks: { hasRemplir: true, hasDuplicate: true, hasExport: true, remplirType: 'fpack' },
      projets: { hasRemplir: true, hasDuplicate: false, hasExport: false, remplirType: 'projet' }
    }
    return configs[tableName] || {}
  })

  return {
    tableConfig
  }
}