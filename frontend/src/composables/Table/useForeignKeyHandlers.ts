import { computed, watch } from 'vue'

export function useForeignKeyHandlers(tableData: any, tableName: string) {
  // Fpacks filtrés pour projets
  const filteredFpacks = computed(() => {
    if (tableData.newRow.value.client_nom) {
      const client = tableData.clients.value.find((c:any) => c.nom === tableData.newRow.value.client_nom)
      if (client) {
        return tableData.fpacks.value.filter((f:any) => f.client === client.id)
      }
    }
    return tableData.fpacks.value
  })

  const filteredFpacksEdit = computed(() => {
    if (tableData.editRow.value.client_nom) {
      const client = tableData.clients.value.find((c:any) => c.nom === tableData.editRow.value.client_nom)
      if (client) {
        return tableData.fpacks.value.filter((f:any) => f.client === client.id)
      }
    }
    return tableData.fpacks.value
  })

  // Watchers pour projets - nouvelle ligne
  watch(() => tableData.newRow.value.client_nom, (clientNom) => {
    if (tableName !== 'projets') return
    if (!clientNom) {
      tableData.newRow.value.fpack_nom = ''
    } else {
      const client = tableData.clients.value.find((c:any) => c.nom === clientNom)
      const fpack = tableData.fpacks.value.find((f:any) => f.nom === tableData.newRow.value.fpack_nom)
      if (fpack && client && fpack.client !== client.id) {
        tableData.newRow.value.fpack_nom = ''
      }
    }
  })

  watch(() => tableData.newRow.value.fpack_nom, (fpackNom) => {
    if (tableName !== 'projets' || !fpackNom) return
    const fpack = tableData.fpacks.value.find((f:any) => f.nom === fpackNom)
    if (fpack) {
      const client = tableData.clients.value.find((c:any) => c.id === fpack.client)
      if (client && tableData.newRow.value.client_nom !== client.nom) {
        tableData.newRow.value.client_nom = client.nom
      }
    }
  })

  // Watchers pour prix_robot - nouvelle ligne
  watch(() => tableData.newRow.value.robot_nom, (nom) => {
    if (tableName !== 'prix_robot') return
    const r = tableData.robots.value.find((r:any) => r.nom === nom)
    if (r) tableData.newRow.value.robot_reference = r.reference
  })

  watch(() => tableData.newRow.value.robot_reference, (ref) => {
    if (tableName !== 'prix_robot') return
    const r = tableData.robots.value.find((r:any) => r.reference === ref)
    if (r) tableData.newRow.value.robot_nom = r.nom
  })

  // Watchers pour prix_robot - édition
  watch(() => tableData.editRow.value.robot_nom, (nom) => {
    if (tableName !== 'prix_robot') return
    const r = tableData.robots.value.find((r:any) => r.nom === nom)
    if (r) tableData.editRow.value.robot_reference = r.reference
  })

  watch(() => tableData.editRow.value.robot_reference, (ref) => {
    if (tableName !== 'prix_robot') return
    const r = tableData.robots.value.find((r:any) => r.reference === ref)
    if (r) tableData.editRow.value.robot_nom = r.nom
  })

  // Watchers pour projets - édition
  watch(() => tableData.editRow.value.client_nom, (clientNom) => {
    if (tableName !== 'projets') return
    if (!clientNom) {
      tableData.editRow.value.fpack_nom = ''
    } else {
      const client = tableData.clients.value.find((c:any) => c.nom === clientNom)
      const fpack = tableData.fpacks.value.find((f:any) => f.nom === tableData.editRow.value.fpack_nom)
      if (fpack && client && fpack.client !== client.id) {
        tableData.editRow.value.fpack_nom = ''
      }
    }
  })

  watch(() => tableData.editRow.value.fpack_nom, (fpackNom) => {
    if (tableName !== 'projets' || !fpackNom) return
    const fpack = tableData.fpacks.value.find((f:any) => f.nom === fpackNom)
    if (fpack) {
      const client = tableData.clients.value.find((c:any) => c.id === fpack.client)
      if (client && tableData.editRow.value.client_nom !== client.nom) {
        tableData.editRow.value.client_nom = client.nom
      }
    }
  })

  // Initialisation spéciale pour projets
  function initializeNewRow(ajouter: boolean) {
    if (!ajouter || tableName !== 'projets') return
    
    if (!tableData.newRow.value.client_nom || !tableData.clients.value.some((c:any) => c.nom === tableData.newRow.value.client_nom)) {
      if (tableData.clients.value.length > 0) {
        tableData.newRow.value.client_nom = tableData.clients.value[0].nom
      }
    }

    const fpacksForClient = tableData.fpacks.value.filter((f:any) => {
      const client = tableData.clients.value.find((c:any) => c.id === f.client)
      return client && client.nom === tableData.newRow.value.client_nom
    })
    
    if (!tableData.newRow.value.fpack_nom || !fpacksForClient.some((f:any) => f.nom === tableData.newRow.value.fpack_nom)) {
      if (fpacksForClient.length > 0) {
        tableData.newRow.value.fpack_nom = fpacksForClient[0].nom
      } else {
        tableData.newRow.value.fpack_nom = ''
      }
    }
  }

  return {
    filteredFpacks,
    filteredFpacksEdit,
    initializeNewRow
  }
}