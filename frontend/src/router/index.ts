import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Produits from '../views/Produits.vue'
import Robots from '../views/Robot.vue'
import Fournisseurs from '../views/Fournisseurs.vue'
import Equipements from '../views/Equipements.vue'
import Clients from '../views/Clients.vue'
import FPack from '../views/FPack.vue'
import Resultats from '../views/Resultats.vue'
import Parametres from '../views/Parametres.vue'  
import RemplirEquipement from '../views/RemplirEquipement.vue'
import ConfigureFPack from '../views/ConfigureFPack.vue'
import Incompatibilites from '../views/Incompatibilites.vue'
import FpackList from '../views/ConfigureFPackListe.vue'
import Prix from '../views/Prix.vue'
import Projet from '../views/Projet.vue'
import CompProjet from '../views/CompleteProjet.vue'
import FactureProjet from '../views/FactureProjet.vue'
import PrixRobot from '../views/PrixRobot.vue'

const routes = [
  { path: '/', component: Dashboard },
  { path: '/produits', component: Produits },
  { path: '/fournisseurs', component: Fournisseurs },
  { path: '/equipements', component: Equipements },
  { path: '/clients', component: Clients },
  { path: '/fpack', name: 'FPackMenu', component: FPack },
  { path: '/robots', component: Robots },
  { path: '/resultats', component: Resultats },
  { path: '/parametres', component: Parametres },
  { path: '/remplir/:tableName/:id', name: 'RemplirEquipement', component: RemplirEquipement },
  { path: '/configure/:tableName/:id', name: 'ConfigureFPack', component: ConfigureFPack},
  { path: '/incompatibilites', name: 'Incompatibilites', component: Incompatibilites },
  {path: '/fpacks/:id/config/liste', name: 'ConfigureFPackListe',component: FpackList},
  {path: '/prix', name: 'Prix',component: Prix},
  {path: '/prix_robot', name: 'Prix-Robot',component: PrixRobot},
  {path: '/projet', name: 'Projet',component: Projet},
  { path: '/complete/:tableName/:id', name: 'CompleteProjet', component: CompProjet},
  { path: '/facture/:id', name: 'FactureProjet', component: FactureProjet },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router