import { ref, onMounted, watch, type Ref } from 'vue'
import axios from 'axios'
import { showToast } from '../composables/useToast'

function handleError(err: any, action = "l'action") {
  let message = `Erreur lors de ${action}`
  if (err?.response?.data?.detail) {
    message = err.response.data.detail
  } else if (err?.message) {
    message = err.message
  }
  showToast(message,"#e71717ff")
}

export function useTableReader(
  props: { tableName: string; apiUrl?: string; ajouter?: boolean },
  emit: (event: 'added' | 'cancelled') => void,
  filters: Ref<Record<string, Set<any>>>
) {
  const columns = ref<string[]>([])
  const rows = ref<any[]>([])
  const newRow = ref<any>({})
  const editingId = ref<number | null>(null)
  const editRow = ref<any>({})

  const fournisseurs = ref<{ id: number, nom: string }[]>([])
  const clients = ref<{ id: number, nom: string }[]>([])
  const produits = ref<{ id: number, nom: string }[]>([])
  const fpacks = ref<{ id: number, nom: string }[]>([])

  const isAdding = ref(false)
  const isDeleting = ref(false)
  const isDuplicating = ref(false)
  const isExporting = ref(false)

  const baseUrl = props.apiUrl || 'http://localhost:8000'

  const fetchDataList = async (endpoint: string, target: Ref<any[]>) => {
    const res = await axios.get(`${baseUrl}/${endpoint}`)
    target.value = res.data
  }

  const fetchData = async () => {
    const colRes = await axios.get(`${baseUrl}/table-columns/${props.tableName}`)
    columns.value = colRes.data

    const dataRes = await axios.get(`${baseUrl}/${props.tableName}`)
    rows.value = dataRes.data

    filters.value = {}
    columns.value.forEach(col => {
      filters.value[col] = new Set(rows.value.map(row => row[col]))
    })

    await Promise.all([
      fetchDataList('fournisseurs', fournisseurs),
      fetchDataList('clients', clients),
      fetchDataList('produits', produits),
      fetchDataList('fpacks', fpacks)
    ])
  }

  onMounted(fetchData)

  watch(() => props.ajouter, (val) => {
    if (val) startAddRow()
  })

  const validateRequiredFields = (data: Record<string, any>, excluded: string[] = []) =>
    Object.entries(data)
      .filter(([k, v]) => !excluded.includes(k) && (v === null || v === undefined || v === ''))
      .map(([k]) => k)

  const mapNomToId = (data: any, source: any[], field: string, idField = `${field}_id`) => {
    const item = source.find(i => i.nom === data[`${field}_nom`])
    data[idField] = item?.id
    delete data[`${field}_nom`]
  }

  const enrichDataWithForeignKeys = (data: any) => {
    const t = props.tableName
    if (t === 'produits') mapNomToId(data, fournisseurs.value, 'fournisseur')
    if (['robots', 'fpacks', 'projets'].includes(t)) mapNomToId(data, clients.value, 'client')
    if (t === 'prix') {
      mapNomToId(data, produits.value, 'produit')
      mapNomToId(data, clients.value, 'client', 'client_id')
    }
    if (t === 'projets') mapNomToId(data, fpacks.value, 'fpack')
  }

  async function ExportRow(row: any) {
    try {
      isExporting.value = true
      const response = await axios.post(
        `${baseUrl}/export-fpack/${row.id}`,
        {},
        { responseType: "blob" }
      )

      const blob = new Blob([response.data], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      })

      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `F-Pack-${row.nom}-${row.fpack_abbr}.xlsx`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error("Erreur lors de l'export :", err)
    } finally {
      isExporting.value = false
    }
  }

  async function ExportAll() {
    try {
      isExporting.value = true
      const response = await axios.get(
        `${baseUrl}/export-fpacks/all`,
        { responseType: "blob" }
      )

      const blob = new Blob([response.data], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      })

      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `F-Packs-All.xlsx`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error("Erreur lors de l'export global :", err)
    } finally {
      isExporting.value = false
    }
  }

  function startAddRow() {
    newRow.value = {}
    columns.value.forEach(col => {
      if (col === 'fournisseur_id') {
        newRow.value['fournisseur_nom'] = fournisseurs.value[0]?.nom || ''
      } else if (col === 'client') {
        newRow.value['client_nom'] = clients.value[0]?.nom || ''
      } else if (col === 'fpack_id') {
        newRow.value['fpack_nom'] = fpacks.value[0]?.nom || ''
      } else {
        newRow.value[col] = ''
      }
    })
  }

  async function duplicateRow(row: any) {
    try {
      if (isDuplicating.value) return
      isDuplicating.value = true
      const res = await axios.post(`${baseUrl}/${props.tableName}/${row.id}/duplicate`)
      const newrow = res.data
      await fetchData()
      startEdit(newrow.id)
    } catch (err) {
      handleError(err, "la duplication")
    }
  }

  async function validateAdd() {
    if (isAdding.value) return
    isAdding.value = true
    try {
      const dataToSend = { ...newRow.value }

      enrichDataWithForeignKeys(dataToSend)
      delete dataToSend.id

      const missing = validateRequiredFields(dataToSend, ["commentaire"])
      if (missing.length > 0) {
        isAdding.value = false
        showToast("Tous les champs de la ligne n'ont pas été remplis.", "#ef9144")
        return
      }
      if (['fpacks', 'projets', 'robots'].includes(props.tableName)) {
        dataToSend.client = dataToSend.client_id
        delete dataToSend.client_id
      }
      console.log(`${baseUrl}/${props.tableName}`, dataToSend)
      await axios.post(`${baseUrl}/${props.tableName}`, dataToSend)
      
      await fetchData()
      emit('added')
    } catch (err) {
      handleError(err, "l'ajout")
    } finally {
      isAdding.value = false
    }
  }

  function cancelAdd() {
    emit('cancelled')
  }

  function startEdit(rowId: number) {
    const row = rows.value.find(r => r.id === rowId)
    if (!row) return

    editingId.value = rowId
    editRow.value = { ...row }

    if (props.tableName === 'produits') {
      const fournisseur = fournisseurs.value.find(f => f.id === row.fournisseur_id)
      editRow.value.fournisseur_nom = fournisseur?.nom || ''
    }
    if (['robots', 'fpacks', 'projets'].includes(props.tableName)) {
      const client = clients.value.find(c => c.id === row.client)
      editRow.value.client_nom = client?.nom || ''
    }
    if (props.tableName === 'projets') {
      const fpack = fpacks.value.find(f => f.id === row.fpack_id)
      editRow.value.fpack_nom = fpack?.nom || ''
    }
  }

  function startEditPrix(rowKey: { produit_id: number; client_id: number }) {
    const row = rows.value.find(
      r => r.produit_id === rowKey.produit_id && r.client_id === rowKey.client_id
    )

    if (!row) return

    editingId.value = Number(`${rowKey.produit_id}${rowKey.client_id}`)
    editRow.value = { ...row }

    const produit = produits.value.find(p => p.id === row.produit_id)
    editRow.value.produit_nom = produit?.nom || ''

    const client = clients.value.find(c => c.id === row.client_id)
    editRow.value.client_nom = client?.nom || ''
  }

  async function validateEdit(rowId: number | { produit_id: number; client_id: number }) {
    try {
      const dataToSend = { ...editRow.value }
      enrichDataWithForeignKeys(dataToSend)

      let url = ''

      if (props.tableName === "prix") {
        const ids = rowId as { produit_id: number; client_id: number }
        url = `${baseUrl}/prix/${ids.produit_id}/${ids.client_id}`
      } else {
        const id = rowId as number
        url = `${baseUrl}/${props.tableName}/${id}`
      }

      const missing = validateRequiredFields(dataToSend, ["commentaire"])
      if (missing.length > 0) {
        showToast("Tous les champs de la ligne n'ont pas été remplis.", "#ef9144")
        isDuplicating.value = false
        return
      }

      await axios.put(url, dataToSend)
      editingId.value = null
      await fetchData()
    } catch (err) {
      console.error("Erreur lors de la modification :", err)
      handleError(err, "la modification")
    } finally {
      isDuplicating.value = false
    }
  }

  function cancelEdit() {
    if (isDuplicating.value) {
      deleteRow(editingId.value!)
    }
    editingId.value = null
    isDuplicating.value = false
  }

  async function deleteRow(rowId: number | { produit_id: number; client_id: number }) {
    if (isDeleting.value) return
    isDeleting.value = true

    try {
      let url = ''
      if (props.tableName === 'prix') {
        const ids = rowId as { produit_id: number; client_id: number }
        url = `${baseUrl}/prix/${ids.produit_id}/${ids.client_id}`
      } else {
        url = `${baseUrl}/${props.tableName}/${rowId}`
      }

      await axios.delete(url)
      await fetchData()
    } catch (err) {
      handleError(err, "la suppression")
    } finally {
      isDeleting.value = false
    }
  }

  return {
    columns, rows, newRow, editingId, editRow,
    fournisseurs, clients, produits, fpacks,
    validateAdd, cancelAdd,
    startEdit, validateEdit, cancelEdit,
    deleteRow, startEditPrix, duplicateRow,
    ExportRow, ExportAll, isExporting
  }
}
