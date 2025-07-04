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

class EquipementRead(EquipementBase):
    id: int
    equipement_produits: List[EquipementProduitRead] = []

    class Config:
        orm_mode = True

class EquipementProduitBase(BaseModel):
    equipement_id: int
    produit_id: int

class EquipementProduitCreate(EquipementProduitBase):
    pass

class EquipementProduitRead(EquipementProduitBase):
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