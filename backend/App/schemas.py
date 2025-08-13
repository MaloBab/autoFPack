from __future__ import annotations
from pydantic import BaseModel  # type: ignore
from typing import List, Optional


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
    id: int
    reference: str
    prix_robot: float
    prix_transport: float
    commentaire: Optional[str] = None

class PrixRobotCreate(PrixRobotBase):
    id: int

class PrixRobotUpdate(PrixRobotBase):
    pass

class PrixRobotOut(PrixRobotBase):
    id: int

    class Config:
        from_attributes = True

class EquipementBase(BaseModel):
    reference: str
    reference: str
    nom: str

class EquipementRead(BaseModel):
    id: int
    reference : str
    nom: str
    equipement_produit: list[EquipementProduitRead] = []

    class Config:
        from_attributes = True

class EquipementCreate(EquipementBase):
    pass

class EquipementUpdate(BaseModel):
    reference: str
    nom: str

class EquipementProduitRead(BaseModel):
    produit_id: int
    quantite: int

    class Config:
        from_attributes = True


class EquipementProduitBase(BaseModel):
    equipement_id: int
    produit_id: int
    quantite: int = 1 

class EquipementProduitCreate(BaseModel):
    equipement_id: int
    produit_id: int
    quantite: int = 1 

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

    class Config:
        from_attributes = True

class GroupeItemBase(BaseModel):
    group_id: int
    type: str  # 'produit' | 'equipement' | 'robot'
    ref_id: int
    statut: Optional[str] = 'optionnel'

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


#PROJET

class ProjetSelectionBase(BaseModel):
    groupe_id: int
    type_item: Optional[str] = None
    ref_id: int

class ProjetSelectionCreate(ProjetSelectionBase):
    pass

class ProjetSelectionRead(ProjetSelectionBase):
    projet_id: int

    class Config:
        from_attributes = True

class ProjetBase(BaseModel):
    nom: str
    FPack_number: Optional[str] = None
    Robot_Location_Code: Optional[str] = None
    fpack_id: int
    id_global:int

class ProjetCreate(ProjetBase):
    pass

class ProjetRead(ProjetBase):
    id: int

    class Config:
        from_attributes = True
        
class ProjetReadExtended(ProjetRead):
    complet: bool
    
class ProjetGlobalBase(BaseModel):
    projet: Optional[str] = None
    sous_projet: Optional[str] = None
    client: int

class ProjetGlobalCreate(ProjetGlobalBase):
    pass

class ProjetGlobalRead(ProjetGlobalBase):
    id: int

    class Config:
        from_attributes = True
        
class ProjetReadWithDetails(ProjetRead):
    """Schema pour afficher un projet avec ses détails complets"""
    fpack_nom: Optional[str] = None
    client_nom: Optional[str] = None
    projet_global_nom: Optional[str] = None
    sous_projet_nom: Optional[str] = None
    complet: bool = False
    nb_selections: int = 0
    nb_groupes_attendus: int = 0

class ProjetGlobalReadWithProjets(ProjetGlobalRead):
    """Schema pour afficher un projet global avec ses projets"""
    projets: List[ProjetReadWithDetails] = []
    client_nom: Optional[str] = None

class ProjetSelectionReadWithDetails(ProjetSelectionRead):
    """Schema pour afficher une sélection avec ses détails"""
    groupe_nom: Optional[str] = None
    item_nom: Optional[str] = None
    
class ProjetTree(BaseModel):
    """Schema pour l'arbre complet des projets"""
    projets_global: List[ProjetGlobalReadWithProjets] = []