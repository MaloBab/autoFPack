import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Produits from '../views/Produits.vue'
import Fournisseurs from '../views/Fournisseurs.vue'
import Clients from '../views/Clients.vue'
import Robot from '../views/Robot.vue'
import Resultats from '../views/Resultats.vue'
import Parametres from '../views/Parametres.vue'  

const routes = [
  { path: '/', component: Dashboard },
  { path: '/produits', component: Produits },
  { path: '/fournisseurs', component: Fournisseurs },
  { path: '/clients', component: Clients },
  { path: '/robots', component: Robot },
  { path: '/resultats', component: Resultats },
  { path: '/parametres', component: Parametres }
  
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router