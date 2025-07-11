import { ref, onMounted, watch, type Ref } from 'vue'
import axios from 'axios'


function handleError(err: any, action = "l'action") {
  let message = `Erreur lors de ${action}`
  if (err?.response?.data?.detail) {
    message = err.response.data.detail
  } else if (err?.message) {
    message = err.message
  }
  alert(message)
}

export function useTableReader(
  props: { tableName: string; apiUrl?: string; ajouter?: boolean },
  emit: (event: 'added' | 'cancelled') => void,
  filters: Ref<Record<string, Set<any>>>)
  {
  const columns = ref<string[]>([])
  const rows = ref<any[]>([])
  const newRow = ref<any>({})
  const editingId = ref<number|null>(null)
  const editRow = ref<any>({})
  const fournisseurs = ref<{ id: number, nom: string }[]>([])
  const clients = ref<{ id: number, nom: string }[]>([])
  const isAdding = ref(false)
  const isDeleting = ref(false)

  const fetchFournisseurs = async () => {
      const url = props.apiUrl ? `${props.apiUrl}/fournisseurs` : `http://localhost:8000/fournisseurs`
      const res = await axios.get(url)
      fournisseurs.value = res.data
  }

  const fetchClients = async () => {
      const url = props.apiUrl ? `${props.apiUrl}/clients` : `http://localhost:8000/clients`
      const res = await axios.get(url)
      clients.value = res.data
  }

  const fetchData = async () => {
    const urlBase = props.apiUrl || 'http://localhost:8000'
    const colRes = await axios.get(`${urlBase}/table-columns/${props.tableName}`)
    columns.value = colRes.data

    const dataRes = await axios.get(`${urlBase}/${props.tableName}`)
    rows.value = dataRes.data
    filters.value = {}
    columns.value.forEach(col => {
      filters.value[col] = new Set(rows.value.map(row => row[col]))})

    await fetchFournisseurs()
    await fetchClients()
  }

  onMounted(fetchData)

  watch(() => props.ajouter, (val) => {
    if (val) startAddRow()
  })

  function startAddRow() {
    newRow.value = {}
    columns.value.forEach(col => {
      if (col === 'fournisseur_id') {
        newRow.value['fournisseur_nom'] = fournisseurs.value[0]?.nom || ''
      } 
      if (col === 'client') {
        newRow.value['client_nom'] = clients.value[0]?.nom || ''
      }
      else {
        newRow.value[col] = ''
      }
    })
  }

  async function validateAdd() {
    if (isAdding.value) return
    isAdding.value = true
    try {
      const dataToSend = { ...newRow.value }
      if (props.tableName === 'produits') {
        const fournisseur = fournisseurs.value.find(f => f.nom === dataToSend.fournisseur_nom)
        dataToSend.fournisseur_id = fournisseur?.id
        delete dataToSend.fournisseur_nom
      }

      if (props.tableName === 'robots' || props.tableName === 'fpacks') {
        const client = clients.value.find(c => c.nom === dataToSend.client_nom)
        dataToSend.client = client?.id
        delete dataToSend.client_nom
      }

      delete dataToSend.id
      const url = props.apiUrl ? `${props.apiUrl}/${props.tableName}` : `http://localhost:8000/${props.tableName}`
      await axios.post(url, dataToSend)
      await fetchData()
      emit('added')
    } catch (err) {
      handleError(err, "l'ajout")
    }
    finally {
      isAdding.value = false
    }
  }

  function cancelAdd() {
    emit('cancelled')
  }

  function startEdit(row: any) {
    editingId.value = row.id
    editRow.value = { ...row }
    if (props.tableName === 'produits' && 'fournisseur_id' in row) {
      const fournisseur = fournisseurs.value.find(f => f.id === row.fournisseur_id)
      editRow.value.fournisseur_nom = fournisseur?.nom || ''
    }

    if ((props.tableName === 'robots' || props.tableName === 'fpacks') && 'client' in row) {
      const client = clients.value.find(c => c.id === row.client)
      editRow.value.client_nom = client?.nom || ''
    }

  }

  async function validateEdit(rowId: number) {
    try {
      const dataToSend = { ...editRow.value }
      if (props.tableName === 'produits') {
        const fournisseur = fournisseurs.value.find(f => f.nom === dataToSend.fournisseur_nom)
        dataToSend.fournisseur_id = fournisseur?.id
        delete dataToSend.fournisseur_nom
      }
      if (props.tableName === 'robots' || props.tableName === 'fpacks') {
        const client = clients.value.find(c => c.nom === dataToSend.client_nom)
        dataToSend.client = client?.id
        delete dataToSend.client_nom
      }

      const url = props.apiUrl ? `${props.apiUrl}/${props.tableName}/${rowId}` : `http://localhost:8000/${props.tableName}/${rowId}`
      await axios.put(url, dataToSend)
      editingId.value = null
      await fetchData()
    } catch (err){
      handleError(err, "la modification")
    }
  }

  function cancelEdit() {
    editingId.value = null
  }

  async function deleteRow(rowId: number) {
    if (isDeleting.value) return
    isDeleting.value = true
    try {
      const url = props.apiUrl ? `${props.apiUrl}/${props.tableName}/${rowId}` : `http://localhost:8000/${props.tableName}/${rowId}`
      await axios.delete(url)
      await fetchData()
    } catch (err){
      handleError(err, "la suppression")
    } finally {
      isDeleting.value = false
    }
  }

  return {
    columns, rows, newRow, editingId, editRow, fournisseurs, clients,
    validateAdd, cancelAdd, startEdit, validateEdit, cancelEdit, deleteRow
  }
}
