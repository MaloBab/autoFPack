import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Produits from '../views/Produits.vue'
import Fournisseurs from '../views/Fournisseurs.vue'
import Clients from '../views/Clients.vue'
import FPack from '../views/FPack.vue'
import Resultats from '../views/Resultats.vue'
import Parametres from '../views/Parametres.vue'  

const routes = [
  { path: '/', component: Dashboard },
  { path: '/produits', component: Produits },
  { path: '/fournisseurs', component: Fournisseurs },
  { path: '/clients', component: Clients },
  { path: '/fpack', component: FPack },
  { path: '/resultats', component: Resultats },
  { path: '/parametres', component: Parametres }
  
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router