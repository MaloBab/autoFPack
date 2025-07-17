<script setup>
defineProps({ open: Boolean })
const menuItems = [
  { label: 'Tableau de Bord', route: '/', icon: '📊' },
  { label: 'Fournisseurs', route: '/fournisseurs', icon: '🏭' },
  { label: 'Clients', route: '/clients', icon: '👤' },
  { label: 'Robots', route: '/robots', icon: '🤖' },
  { label: 'Equipements', route: '/equipements', icon: '🔧' },
  { label: 'Produits', route: '/produits', icon: '🧩' },
  { label: 'F-Pack', route: '/fpack', icon: '📦' },
  { label: 'Projets', route: '/projet', icon: '📈' }
]

</script>
<template>
 <nav class="sidebar" :class="{ closed: !open }">
    <ul>
      <li v-for="item in menuItems" :key="item.label">
        <router-link :to="item.route" class="menu-link">
          <span class="icon">{{ item.icon }}</span>
          {{ item.label }}
        </router-link>
      </li>
    </ul>
    <router-link to="/parametres" class="menu-link param-link">
      <span class="iconfooter">⚙️</span>
      Paramètres
    </router-link>
  </nav>
</template>


<style scoped>
.sidebar {
  width: 20%;
  min-width: 18%;
  background-color: #1e1e1e;
  color: white;
  padding: 1%;
  box-sizing: border-box;
  transition: width 0.3s, min-width 0.3s;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
}
.sidebar.closed {
  width: 0;
  min-width: 0;
  padding: 0;
}

.sidebar ul {
  list-style: none;
  padding: 0%;
  margin: 0%;
}

.menu-link {
  color: white;
  text-decoration: none;
  display: flex;
  align-items: center;
  padding: 0.75rem 0;
  font-size: 1.1rem;
  transition: background 0.2s, font-size 0.2s;
}

.menu-link:hover {
  background-color: #333;
  border-radius: 5%;
  padding-left: 5%;
}

.icon {
  width: 20%;
  margin-right: 0%;
  font-size: 110%;
}

.param-link {
  margin-top: auto;
  padding-bottom: 1%;
}
.iconfooter {
  width: 20%;
  margin-right: 0%;
  font-size: 130%;
}

</style>