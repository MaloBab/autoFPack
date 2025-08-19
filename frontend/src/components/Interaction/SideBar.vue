<script setup>
defineProps({ state: Number }) // 0 = fermé, 1 = icônes, 2 = ouvert
const menuItems = [
  { label: 'Tableau de Bord', route: '/', icon: '📊' },
  { label: 'Fournisseurs', route: '/fournisseurs', icon: '🏭' },
  { label: 'Clients', route: '/clients', icon: '👤' },
  { label: 'Robots', route: '/robots', icon: '🤖' },
  { label: 'Equipements', route: '/equipements', icon: '🔧' },
  { label: 'Produits', route: '/produits', icon: '🧩' },
  { label: 'F-Pack', route: '/fpack', icon: '📦' },
  { label: 'Projets', route: '/projet_global', icon: '📈' }
]
</script>

<template>
  <nav class="sidebar" :class="{ 
    closed: state === 0, 
    'icons-only': state === 1, 
    open: state === 2 
  }">
    <ul>
      <li v-for="item in menuItems" :key="item.label">
        <router-link :to="item.route" class="menu-link" :title="state === 1 ? item.label : ''">
          <span class="icon">{{ item.icon }}</span>
          <span class="label" v-if="state === 2">{{ item.label }}</span>
        </router-link>
      </li>
    </ul>
  </nav>
</template>

<style scoped>
.sidebar {
  width: 15%;
  background-color: #1e1e1e;
  color: white;
  padding: 1%;
  box-sizing: border-box;
  transition: width 0.3s ease, min-width 0.3s ease, padding 0.3s ease;
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

.sidebar.icons-only {
  width: 4rem;
  min-width: 4rem;
  padding: 1rem 0.5rem;
}

.sidebar.open {
  width: 15%;
  min-width: 200px;
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
  transition: background 0.2s, font-size 0.2s, padding 0.2s;
  position: relative;
}

.sidebar.icons-only .menu-link {
  justify-content: center;
  padding: 0.75rem 0.25rem;
}

.menu-link:hover {
  background-color: #333;
  border-radius: 5%;
}

.sidebar.open .menu-link:hover {
  padding-left: 5%;
}

.icon {
  width: 20%;
  margin-right: 0%;
  font-size: 110%;
  flex-shrink: 0;
}

.sidebar.icons-only .icon {
  width: auto;
  margin-right: 0;
  font-size: 130%;
}

.label {
  transition: opacity 0.2s ease;
}

.param-link {
  margin-top: auto;
  padding-bottom: 1%;
}

.iconfooter {
  width: 20%;
  margin-right: 0%;
  font-size: 130%;
  flex-shrink: 0;
}

.sidebar.icons-only .iconfooter {
  width: auto;
  margin-right: 0;
}

.sidebar.icons-only .menu-link {
  position: relative;
}

.sidebar.icons-only .menu-link::after {
  content: attr(title);
  position: absolute;
  left: 100%;
  top: 50%;
  transform: translateY(-50%);
  background-color: #333;
  color: white;
  padding: 0.5rem;
  border-radius: 4px;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.3s, visibility 0.3s;
  margin-left: 0.5rem;
  z-index: 1000;
  font-size: 0.9rem;
}

.sidebar.icons-only .menu-link:hover::after {
  opacity: 1;
  visibility: visible;
}
</style>