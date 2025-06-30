<script setup>
import SideBar from './SideBar.vue'
import HeaderBar from './HeaderBar.vue'
</script>

<template>
  <div class="app-container">
    <SideBar />
    <div class="main-container">
      <HeaderBar />
      <router-view />
    </div>
  </div>
</template>


<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  font-family: sans-serif;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #f7f7f7;
}
</style>