import { computed, reactive, type Ref } from 'vue'

export function useTableSorting(filteredRows: Ref<any[]>, valueLabels: Ref<Record<string, Record<any, string>>>) {
  const sortOrders = reactive<Record<string, 'asc' | 'desc' | null>>({})

  function onSortChange(column: string, order: 'asc' | 'desc' | null) {
    sortOrders[column] = order
  }

  const filteredAndSortedRows = computed(() => {
    let result = filteredRows.value.slice()

    for (const [col, order] of Object.entries(sortOrders)) {
      if (order) {
        result.sort((a, b) => {
          const valA = a[col]
          const valB = b[col]
          const labelA = valueLabels.value[col]?.[valA] ?? valA
          const labelB = valueLabels.value[col]?.[valB] ?? valB

          if (typeof labelA === 'string' && typeof labelB === 'string') {
            return order === 'asc'
              ? labelA.localeCompare(labelB)
              : labelB.localeCompare(labelA)
          }
          if (typeof valA === 'number' && typeof valB === 'number') {
            return order === 'asc' ? valA - valB : valB - valA
          }
          return 0
        })
      }
    }

    return result
  })

  return {
    sortOrders,
    onSortChange,
    filteredAndSortedRows
  }
}