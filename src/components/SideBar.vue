<script setup>
const menuItems = [
  { label: 'Dashboard', route: '/', icon: '📊' },
  { label: 'Produits', route: '/produits', icon: '📦' },
  { label: 'Fournisseurs', route: '/fournisseurs', icon: '🏭' },
  { label: 'Clients', route: '/clients', icon: '👤' },
  { label: 'Robots', route: '/robots', icon: '🤖' },
  { label: 'Résultats', route: '/resultats', icon: '📈' },
  { label: 'Paramètres', route: '/parametres', icon: '⚙️' }
]
</script>

<template>
  <nav class="sidebar">
    <ul>
      <li v-for="item in menuItems" :key="item.label">
        <router-link :to="item.route" class="menu-link">
          <span class="icon">{{ item.icon }}</span>
          {{ item.label }}
        </router-link>
      </li>
    </ul>
  </nav>
</template>


<style scoped>
.sidebar {
  width: 220px;
  background-color: #1e1e1e;
  color: white;
  padding: 1rem;
}

.menu-link {
  color: white;
  text-decoration: none;
  display: flex;
  align-items: center;
  padding: 0.75rem 0;
  transition: background 0.2s;
}

.menu-link:hover {
  background-color: #333;
  border-radius: 6px;
  padding-left: 0.5rem;
}

.icon {
  width: 24px;
  margin-right: 0.75rem;
  text-align: center;
}
</style>