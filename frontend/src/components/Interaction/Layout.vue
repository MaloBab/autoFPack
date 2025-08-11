
<script setup>
import SideBar from './SideBar.vue'
import HeaderBar from './HeaderBar.vue'
import { ref } from 'vue'

// 0 = fermé, 1 = icônes seulement, 2 = ouvert complet
const sidebarState = ref(2)

const toggleSidebar = () => {
  sidebarState.value = (sidebarState.value + 1) % 3
}
</script>

<template>
  <div class="app-container">
    <HeaderBar @toggle-sidebar="toggleSidebar" />
    <div class="content-container">
      <SideBar :state="sidebarState" />
      <div class="main-container">
        <router-view />
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: sans-serif;
}

.content-container {
  display: flex;
  flex: 1;
  height: 100%;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #f7f7f7;
  min-width: 0;
}
</style>