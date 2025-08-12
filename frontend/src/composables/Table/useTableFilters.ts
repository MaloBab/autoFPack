// useTableFilters.ts
import { computed, type Ref } from 'vue'

export function useTableFilters(tableData: any, filters: Ref<Record<string, Set<any>>>, props: any) {
  const columnValues = computed(() => {
    const map: Record<string, Set<any>> = {}
    for (const row of tableData.rows.value) {
      for (const col of tableData.columns.value) {
        map[col] ??= new Set()
        map[col].add(row[col])
      }
    }
    return map
  })

  const filteredRows = computed(() =>
    tableData.rows.value
      .filter((row:any) =>
        tableData.columns.value.every((col:any) =>
          !filters.value[col] || filters.value[col].has(row[col])
        )
      )
      .filter((row:any) => {
        if (!props.search) return true
        const search = props.search.toLowerCase()
        return tableData.columns.value.some((col:any) => {
          let cellValue = row[col]

          // Gestion spéciale pour les foreign keys
          cellValue = getForeignKeyDisplayValue(cellValue, col, props.tableName, tableData)
          
          return String(cellValue).toLowerCase().includes(search)
        })
      })
  )

  function getForeignKeyDisplayValue(cellValue: any, col: string, tableName: string, tableData: any) {
    if (['projets', 'fpacks'].includes(tableName) && col === 'client') {
      const client = tableData.clients.value.find((c:any) => c.id === cellValue)
      return client?.nom || cellValue
    }
    if (tableName === 'projets' && col === 'fpack_id') {
      const fpack = tableData.fpacks.value.find((f:any) => f.id === cellValue)
      return fpack?.nom || cellValue
    }
    if (tableName === 'produits' && col === 'fournisseur_id') {
      const fournisseur = tableData.fournisseurs.value.find((f:any) => f.id === cellValue)
      return fournisseur?.nom || cellValue
    }
    if (tableName === 'robots' && col === 'client') {
      const client = tableData.clients.value.find((c:any) => c.id === cellValue)
      return client?.nom || cellValue
    }
    if (tableName === 'prix') {
      if (col === 'produit_id') {
        const produit = tableData.produits.value.find((p:any) => p.id === cellValue)
        return produit?.nom || cellValue
      }
      if (col === 'client_id') {
        const client = tableData.clients.value.find((c:any) => c.id === cellValue)
        return client?.nom || cellValue
      }
    }
    if (tableName === 'prix_robot' && col === 'id') {
      const robot = tableData.robots.value.find((r:any) => r.id === cellValue)
      return robot?.nom || cellValue
    }
    
    return cellValue
  }

  function updateFilter(col: string, values: Set<any>) {
    filters.value[col] = values
  }

  return {
    columnValues,
    filteredRows,
    updateFilter
  }
}