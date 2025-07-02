import { ref, onMounted, watch } from 'vue'
import axios from 'axios'

export function useTableReader(
  props: { tableName: string; apiUrl?: string; ajouter?: boolean },
  emit: (event: 'added' | 'cancelled') => void ){
  const columns = ref<string[]>([])
  const rows = ref<any[]>([])
  const newRow = ref<any>({})
  const editingId = ref<number|null>(null)
  const editRow = ref<any>({})
  const fournisseurs = ref<{ id: number, nom: string }[]>([])

  const fetchFournisseurs = async () => {
    if (props.tableName === 'produits') {
      const url = props.apiUrl ? `${props.apiUrl}/fournisseurs` : `http://localhost:8000/fournisseurs`
      const res = await axios.get(url)
      fournisseurs.value = res.data
    }
  }

  const fetchData = async () => {
    const urlBase = props.apiUrl || 'http://localhost:8000'
    const colRes = await axios.get(`${urlBase}/table-columns/${props.tableName}`)
    columns.value = colRes.data

    const dataRes = await axios.get(`${urlBase}/${props.tableName}`)
    rows.value = dataRes.data

    if (props.tableName === 'produits') await fetchFournisseurs()
  }

  onMounted(fetchData)

  watch(() => props.ajouter, (val) => {
    if (val) startAddRow()
  })

  function startAddRow() {
    newRow.value = {}
    columns.value.forEach(col => {
      if (col === 'fournisseur_id' && props.tableName === 'produits') {
        newRow.value['fournisseur_nom'] = fournisseurs.value[0]?.nom || ''
      } else {
        newRow.value[col] = ''
      }
    })
  }

  async function validateAdd() {
    try {
      const dataToSend = { ...newRow.value }
      if (props.tableName === 'produits') {
        const fournisseur = fournisseurs.value.find(f => f.nom === dataToSend.fournisseur_nom)
        dataToSend.fournisseur_id = fournisseur?.id
        delete dataToSend.fournisseur_nom
      }
      delete dataToSend.id
      const url = props.apiUrl ? `${props.apiUrl}/${props.tableName}` : `http://localhost:8000/${props.tableName}`
      await axios.post(url, dataToSend)
      await fetchData()
      emit('added')
    } catch {
      alert("Erreur lors de l'ajout")
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
  }

  async function validateEdit(rowId: number) {
    try {
      const dataToSend = { ...editRow.value }
      if (props.tableName === 'produits') {
        const fournisseur = fournisseurs.value.find(f => f.nom === dataToSend.fournisseur_nom)
        dataToSend.fournisseur_id = fournisseur?.id
        delete dataToSend.fournisseur_nom
      }
      const url = props.apiUrl ? `${props.apiUrl}/${props.tableName}/${rowId}` : `http://localhost:8000/${props.tableName}/${rowId}`
      await axios.put(url, dataToSend)
      editingId.value = null
      await fetchData()
    } catch {
      alert("Erreur lors de la modification")
    }
  }

  function cancelEdit() {
    editingId.value = null
  }

  async function deleteRow(rowId: number) {
    try {
      const url = props.apiUrl ? `${props.apiUrl}/${props.tableName}/${rowId}` : `http://localhost:8000/${props.tableName}/${rowId}`
      await axios.delete(url)
      await fetchData()
    } catch {
      alert("Erreur lors de la suppression")
    }
  }

  return {
    columns, rows, newRow, editingId, editRow, fournisseurs,
    validateAdd, cancelAdd, startEdit, validateEdit, cancelEdit, deleteRow
  }
}
