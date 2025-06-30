<script setup lang="ts">
import logo from '../assets/FANUC.png'
</script>


<template>
  <header class="header">
    <img class="logo" :src="logo" alt="Logo FANUC" />
  </header>
</template>

<style scoped>
.header {
  background-color: #ffd500;
  height: 11%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  position: relative;
}

.logo {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  max-height: 60%;
  width: auto;
}
</style>