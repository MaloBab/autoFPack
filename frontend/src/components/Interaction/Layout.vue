<script setup>
import SideBar from './SideBar.vue'
import HeaderBar from './HeaderBar.vue'
import { ref } from 'vue'

const isSidebarOpen = ref(true)

</script>

<template>
  <div class="app-container">
    <HeaderBar @toggle-sidebar="isSidebarOpen = !isSidebarOpen" />
    <div class="content-container">
      <SideBar :open="isSidebarOpen" />
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