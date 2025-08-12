// tableConfig.ts
export interface TableAction {
  label: string
  icon: string
  variant: 'primary' | 'success' | 'warning' | 'danger' | 'secondary'
  action: 'add' | 'export' | 'import' | 'custom'
  url?: string
  routeTo?: string
  customHandler?: () => void
}

export interface TableConfiguration {
  displayName: string
  actions: TableAction[]
  hasAdd: boolean
  hasExport: boolean
  hasImport: boolean
  customActions?: TableAction[]
}

export const tableConfigurations: Record<string, TableConfiguration> = {
  produits: {
    displayName: 'Produits',
    hasAdd: true,
    hasExport: true,
    hasImport: true,
    actions: [
      {
        label: 'Ajouter Produit',
        icon: '➕',
        variant: 'primary',
        action: 'add'
      },
      {
        label: 'Exporter Produits',
        icon: '📤',
        variant: 'success',
        action: 'export',
        url: 'http://localhost:8000/produits/export/excel'
      },
      {
        label: 'Importer Produits',
        icon: '📥',
        variant: 'success',
        action: 'import',
        url: 'http://localhost:8000/produits/import/add'
      },
      {
        label: 'Gérer Incompatibilités',
        icon: '⛔',
        variant: 'danger',
        action: 'custom',
        routeTo: '/incompatibilites'
      },
      {
        label: 'Gérer Prix',
        icon: '💵',
        variant: 'secondary',
        action: 'custom',
        routeTo: '/prix'
      }
    ]
  },
  robots: {
    displayName: 'Robots',
    hasAdd: true,
    hasExport: true,
    hasImport: true,
    actions: [
      {
        label: 'Ajouter Robot',
        icon: '➕',
        variant: 'primary',
        action: 'add'
      },
      {
        label: 'Exporter Robots',
        icon: '📤',
        variant: 'success',
        action: 'export',
        url: 'http://localhost:8000/robots/export/excel'
      },
      {
        label: 'Importer Robots',
        icon: '📥',
        variant: 'success',
        action: 'import',
        url: 'http://localhost:8000/robots/import/add'
      }
    ]
  },
  clients: {
    displayName: 'Clients',
    hasAdd: true,
    hasExport: false,
    hasImport: false,
    actions: [
      {
        label: 'Ajouter Client',
        icon: '➕',
        variant: 'primary',
        action: 'add'
      }
    ]
  }
}

export function getTableConfig(tableName: string): TableConfiguration {
  return tableConfigurations[tableName] || {
    displayName: tableName.charAt(0).toUpperCase() + tableName.slice(1),
    hasAdd: true,
    hasExport: false,
    hasImport: false,
    actions: [
      {
        label: `Ajouter ${tableName.slice(0, -1)}`,
        icon: '➕',
        variant: 'primary',
        action: 'add'
      }
    ]
  }
}