import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Produits from '../views/Produits.vue'

const routes = [
  { path: '/', component: Dashboard },
  { path: '/produits', component: Produits },
  // autres vues à ajouter ici
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router