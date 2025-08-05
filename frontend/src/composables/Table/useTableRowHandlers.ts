export function useTableRowHandlers(tableData: any, tableName: string) {
  function getEditingId(row: any): number | null {
    if (tableName === 'prix') {
      return tableData.editingId.value === Number(`${row.produit_id}${row.client_id}`) 
        ? tableData.editingId.value 
        : null
    }
    return tableData.editingId.value === row.id ? tableData.editingId.value : null
  }

  function handleStartEdit(row: any) {
    if (tableName === 'prix') {
      tableData.startEditPrix({ produit_id: row.produit_id, client_id: row.client_id })
    } else {
      tableData.startEdit(row.id)
    }
  }

  function handleValidateEdit(row: any) {
    if (tableName === 'prix') {
      tableData.validateEdit({ produit_id: row.produit_id, client_id: row.client_id })
    } else {
      tableData.validateEdit(row.id)
    }
  }

  function handleDeleteRow(row: any) {
    if (tableName === 'prix') {
      tableData.deleteRow({ produit_id: row.produit_id, client_id: row.client_id })
    } else {
      tableData.deleteRow(row.id)
    }
  }

  return {
    getEditingId,
    handleStartEdit,
    handleValidateEdit,
    handleDeleteRow
  }
}