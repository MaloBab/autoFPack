from __future__ import annotations
from pydantic import BaseModel  # type: ignore
from typing import List, Optional, Dict


class ProduitBase(BaseModel):
    reference: str
    nom: str
    description: Optional[str] = None
    fournisseur_id: int
    type: Optional[str] = None

class ProduitCreate(ProduitBase):
    pass

class ProduitRead(ProduitBase):
    id: int

    class Config:
        from_attributes = True

class PrixBase(BaseModel):
    produit_id: int
    client_id: int
    prix_produit: float  
    prix_transport: float  
    commentaire: Optional[str] = None

class PrixCreate(PrixBase):
    pass

class PrixRead(PrixBase):
    
    class Config:
        from_attributes = True

class FournisseurBase(BaseModel):
    nom: str

class FournisseurCreate(FournisseurBase):
    pass

class FournisseurRead(FournisseurBase):
    id: int
    produits: List[ProduitRead] = []

    class Config:
        from_attributes = True

class ClientBase(BaseModel):
    nom: str

class ClientCreate(ClientBase):
    pass

class ClientRead(ClientBase):
    id: int
    robots: List[RobotRead] = []

    class Config:
        from_attributes = True

class RobotBase(BaseModel):
    nom: str
    reference: str
    generation: str
    client: int
    payload: int
    range: int
    commentaire: Optional[str] = None

class RobotCreate(RobotBase):
    pass

class RobotRead(RobotBase):
    id: int

    class Config:
        from_attributes = True

class PrixRobotBase(BaseModel):
    reference: str
    prix_robot: float
    prix_transport: float
    commentaire: Optional[str] = None

class PrixRobotCreate(BaseModel):
    id: int 
    reference: str
    prix_robot: float
    prix_transport: float
    commentaire: Optional[str] = None

class PrixRobotUpdate(PrixRobotBase):
    pass

class PrixRobotRead(PrixRobotBase): 
    id: int

    class Config:
        from_attributes = True

# EQUIPEMENTS
class EquipementBase(BaseModel):
    reference: str
    nom: str 
    

class EquipementCreate(EquipementBase):
    pass

class EquipementUpdate(EquipementBase):
    pass

class EquipementRead(EquipementBase):
    id: int
    equipement_produit: List[EquipementProduitRead] = []

    class Config:
        from_attributes = True

class EquipementProduitBase(BaseModel):
    equipement_id: int
    produit_id: int
    quantite: int = 1 

class EquipementProduitCreate(EquipementProduitBase):
    pass

class EquipementProduitRead(BaseModel):
    equipement_id: int
    produit_id: int
    quantite: int

    class Config:
        from_attributes = True

# FPACKS
class FPackBase(BaseModel):
    nom: str
    client: int
    fpack_abbr: str

class FPackCreate(FPackBase):
    pass

class FPackRead(FPackBase):
    id: int

    class Config:
        from_attributes = True

# GROUPS
class GroupesBase(BaseModel):
    nom: str

class GroupesCreate(GroupesBase):
    pass

class GroupesRead(GroupesBase):
    id: int
    items: List[GroupeItemRead] = []

    class Config:
        from_attributes = True

class GroupeItemBase(BaseModel):
    group_id: int
    type: str  # 'produit' | 'equipement' | 'robot'
    ref_id: int
    statut: Optional[str] = 'optionnel'  # 'standard' | 'optionnel'

class GroupeItemCreate(GroupeItemBase):
    pass

class GroupeItemRead(GroupeItemBase):
    id: int

    class Config:
        from_attributes = True

# FPACK CONFIG COLUMNS
class FPackConfigColumnBase(BaseModel):
    fpack_id: int
    ordre: int
    type: str  # 'produit' | 'equipement' | 'group'
    ref_id: Optional[int] = None

class FPackConfigColumnCreate(FPackConfigColumnBase):
    pass

class FPackConfigColumnRead(FPackConfigColumnBase):
    id: int

    class Config:
        from_attributes = True

# INCOMPATIBILITÉS ET COMPATIBILITÉS
class ProduitIncompatibiliteBase(BaseModel):
    produit_id_1: int
    produit_id_2: int

class ProduitIncompatibiliteCreate(ProduitIncompatibiliteBase):
    pass

class ProduitIncompatibiliteRead(ProduitIncompatibiliteBase):
    class Config:
        from_attributes = True

class RobotProduitCompatibiliteBase(BaseModel):
    robot_id: int
    produit_id: int

class RobotProduitCompatibiliteCreate(RobotProduitCompatibiliteBase):
    pass

class RobotProduitCompatibiliteRead(RobotProduitCompatibiliteBase):
    class Config:
        from_attributes = True

# PROJETS GLOBAUX
class ProjetGlobalBase(BaseModel):
    projet: Optional[str] = None
    client: int

class ProjetGlobalCreate(ProjetGlobalBase):
    pass

class ProjetGlobalRead(ProjetGlobalBase):
    id: int

    class Config:
        from_attributes = True

# SOUS-PROJETS
class SousProjetBase(BaseModel):
    nom: str
    id_global: int

class SousProjetCreate(SousProjetBase):
    pass

class SousProjetRead(SousProjetBase):
    id: int

    class Config:
        from_attributes = True
        
class SousProjetReadExtended(SousProjetRead):
    complet: bool

# SOUS-PROJET FPACK (table de liaison)
class SousProjetFpackBase(BaseModel):
    fpack_id: int
    FPack_number: Optional[str] = None
    Robot_Location_Code: Optional[str] = None
    contractor: str = "N/A"
    required_delivery_time: str = "N/A"
    delivery_site: str = "N/A"
    tracking: str = "N/A"

class SousProjetFpackCreate(SousProjetFpackBase):
    pass

class SousProjetFpackRead(SousProjetFpackBase):
    id: int
    sous_projet_id: int
    class Config:
        from_attributes = True

# SÉLECTIONS DE PROJET
class ProjetSelectionBase(BaseModel):
    sous_projet_fpack_id: int 
    groupe_id: int
    type_item: str 
    ref_id: int

class ProjetSelectionCreate(BaseModel):
    # Ne pas hériter de Base pour éviter d'exiger sous_projet_fpack_id
    groupe_id: int
    type_item: str 
    ref_id: int


class ProjetSelectionRead(ProjetSelectionBase):
    class Config:
        from_attributes = True

# SCHÉMAS ÉTENDUS POUR LES VUES
class SousProjetReadWithDetails(SousProjetRead):
    """Schema pour afficher un projet avec ses détails complets"""
    client_nom: Optional[str] = None
    projet_global_nom: Optional[str] = None
    sous_projet_nom: Optional[str] = None
    complet: bool = False
    nb_selections: int = 0
    nb_groupes_attendus: int = 0
    fpacks: List[Dict] = []

class ProjetGlobalReadWithSousProjets(ProjetGlobalRead):
    """Schema pour afficher un projet global avec ses projets"""
    sous_projets: List[SousProjetReadWithDetails] = []
    client_nom: Optional[str] = None

class ProjetSelectionReadWithDetails(ProjetSelectionRead):
    """Schema pour afficher une sélection avec ses détails"""
    groupe_nom: Optional[str] = None
    item_nom: Optional[str] = None
    
class ProjetTree(BaseModel):
    """Schema pour l'arbre complet des projets"""
    projets_global: List[ProjetGlobalReadWithSousProjets] = []

# SCHÉMAS AVEC RELATIONS COMPLÈTES
class ProduitReadWithRelations(ProduitRead):
    """Produit avec toutes ses relations"""
    fournisseur: Optional[FournisseurRead] = None
    prix: List[PrixRead] = []

class RobotReadWithRelations(RobotRead):
    """Robot avec toutes ses relations"""
    prix: Optional[PrixRobotRead] = None
    compatibilites_produit: List[RobotProduitCompatibiliteRead] = []

class ClientReadWithRelations(ClientRead):
    """Client avec toutes ses relations"""
    robots: List[RobotRead] = []
    fpacks: List[FPackRead] = []
    projets_globaux: List[ProjetGlobalRead] = []

class GroupesReadWithItems(GroupesRead):
    """Groupe avec ses items"""
    items: List[GroupeItemRead] = []

class FPackReadWithConfig(FPackRead):
    """FPack avec sa configuration"""
    config_columns: List[FPackConfigColumnRead] = []
    
class ProjetParClient(BaseModel):
    client: str
    count: int

class ProjetStats(BaseModel):
    nb_projets_globaux: int
    nb_sous_projets: int
    projets_par_client: List[ProjetParClient]
    sous_projets_complets: int
    sous_projets_incomplets: int
