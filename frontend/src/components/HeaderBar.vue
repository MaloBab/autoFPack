<script setup lang="ts">
import { defineEmits } from 'vue'
import logo from '../assets/FANUC.png'
const emit = defineEmits(['toggle-sidebar'])
</script>

<template>
  <header class="header">
    <button class="sidebar-toggle" @click="emit('toggle-sidebar')">☰</button>
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
.sidebar-toggle {
  font-size: 3vw;
  background: none;
  border: none;
  color: #d80000;
  cursor: pointer;
  padding: 0.5vw 0.5vw;    
  border-radius: 0.5vw;
  transition: background 0.2s;
}

.sidebar-toggle:focus {
  outline: none;
}

.sidebar-toggle:hover {
  background: #ffe066;
}

.logo {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  max-height: 60%;
  width: auto;
}
</style>