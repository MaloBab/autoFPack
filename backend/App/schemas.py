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

class GroupeBase(BaseModel):
    nom: str

class GroupeCreate(GroupeBase):
    pass

class GroupeRead(GroupeBase):
    id: int
    groupe_produits: List[GroupeProduitRead] = []

    class Config:
        orm_mode = True

class GroupeProduitBase(BaseModel):
    produit_id: int
    groupe_id: int

class GroupeProduitCreate(GroupeProduitBase):
    pass

class GroupeProduitRead(GroupeProduitBase):
    id: int

    class Config:
        orm_mode = True