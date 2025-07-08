from __future__ import annotations
from pydantic import BaseModel # type: ignore
from typing import List, Optional


class ProduitBase(BaseModel):
    nom: str
    description: Optional[str] = None
    fournisseur_id: int
    type: Optional[str] = None

class ProduitCreate(ProduitBase):
    pass

class ProduitRead(ProduitBase):
    id: int

    class Config:
        orm_mode = True

class FournisseurBase(BaseModel):
    nom: str

class FournisseurCreate(FournisseurBase):
    pass

class FournisseurRead(FournisseurBase):
    id: int
    produits: List[ProduitRead] = []

    class Config:
        orm_mode = True

class ClientBase(BaseModel):
    nom: str

class ClientCreate(ClientBase):
    pass

class ClientRead(ClientBase):
    id: int
    robots: List[RobotRead] = []

    class Config:
        orm_mode = True

class RobotBase(BaseModel):
    nom: str
    generation: str
    client: int
    payload: int
    range: int

class RobotCreate(RobotBase):
    pass

class RobotRead(RobotBase):
    id: int

    class Config:
        orm_mode = True

class EquipementBase(BaseModel):
    nom: str

class EquipementCreate(EquipementBase):
    pass

class EquipementRead(BaseModel):
    id: int
    nom: str
    equipement_produit: list[EquipementProduitRead] = []

    class Config:
        orm_mode = True

class EquipementProduitBase(BaseModel):
    equipement_id: int
    produit_id: int

class EquipementProduitCreate(EquipementProduitBase):
    pass

class EquipementProduitRead(BaseModel):
    produit_id: int

    class Config:
        orm_mode = True
        
class FPackBase(BaseModel):
    nom: str
    client: int
    fpack_abbr: str

class FPackCreate(FPackBase):
    pass

class FPackRead(FPackBase):
    id: int

    class Config:
        orm_mode = True
        
# GROUPS
class GroupesBase(BaseModel):
    nom: str

class GroupesCreate(GroupesBase):
    pass

class GroupesRead(GroupesBase):
    id: int
    class Config:
        orm_mode = True

class GroupeItemBase(BaseModel):
    group_id: int
    type: str  # 'produit' | 'equipement' | 'robot'
    ref_id: int

class GroupeItemCreate(GroupeItemBase):
    pass

class GroupeItemRead(GroupeItemBase):
    id: int
    class Config:
        orm_mode = True

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
        orm_mode = True

class ProduitIncompatibiliteBase(BaseModel):
    produit_id_1: int
    produit_id_2: int

class ProduitIncompatibiliteCreate(ProduitIncompatibiliteBase):
    pass

class ProduitIncompatibiliteRead(ProduitIncompatibiliteBase):
    class Config:
        orm_mode = True


class RobotProduitIncompatibiliteBase(BaseModel):
    robot_id: int
    produit_id: int

class RobotProduitIncompatibiliteCreate(RobotProduitIncompatibiliteBase):
    pass

class RobotProduitIncompatibiliteRead(RobotProduitIncompatibiliteBase):
    class Config:
        orm_mode = True
