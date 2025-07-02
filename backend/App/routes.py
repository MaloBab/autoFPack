from fastapi import APIRouter, Depends, HTTPException # type: ignore
from sqlalchemy.orm import Session # type: ignore
from .database import SessionLocal
from . import models, schemas
from sqlalchemy import inspect # type: ignore

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/table-columns/{table_name}", response_model=list[str])
def get_table_columns(table_name: str, db: Session = Depends(get_db)):
    inspector = inspect(db.bind)
    columns = inspector.get_columns(table_name)
    return [col["name"] for col in columns]


# PRODUITS
@router.get("/produits", response_model=list[schemas.ProduitRead])
def list_produits(db: Session = Depends(get_db)):
    return db.query(models.Produit).all()

@router.post("/produits", response_model=schemas.ProduitRead)
def create_produit(produit: schemas.ProduitCreate, db: Session = Depends(get_db)):
    db_produit = models.Produit(**produit.dict())
    db.add(db_produit)
    db.commit()
    db.refresh(db_produit)
    return db_produit

@router.put("/produits/{id}", response_model=schemas.ProduitRead)
def update_produit(id: int, produit: schemas.ProduitCreate, db: Session = Depends(get_db)):
    db_produit = db.query(models.Produit).get(id)
    if not db_produit:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    for key, value in produit.dict().items():
        setattr(db_produit, key, value)
    db.commit()
    db.refresh(db_produit)
    return db_produit

@router.delete("/produits/{id}")
def delete_produit(id: int, db: Session = Depends(get_db)):
    db_produit = db.query(models.Produit).get(id)
    if not db_produit:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    db.delete(db_produit)
    db.commit()
    return {"ok": True}

# FOURNISSEURS
@router.get("/fournisseurs", response_model=list[schemas.FournisseurRead])
def list_fournisseurs(db: Session = Depends(get_db)):
    return db.query(models.Fournisseur).all()

@router.post("/fournisseurs", response_model=schemas.FournisseurRead)
def create_fournisseur(fournisseur: schemas.FournisseurCreate, db: Session = Depends(get_db)):
    db_fournisseur = models.Fournisseur(**fournisseur.dict())
    db.add(db_fournisseur)
    db.commit()
    db.refresh(db_fournisseur)
    return db_fournisseur


@router.put("/fournisseurs/{id}", response_model=schemas.FournisseurRead)
def update_fournisseur(id: int, fournisseur: schemas.FournisseurCreate, db: Session = Depends(get_db)):
    db_fournisseur = db.query(models.Fournisseur).get(id)
    if not db_fournisseur:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    for key, value in fournisseur.dict().items():
        setattr(db_fournisseur, key, value)
    db.commit()
    db.refresh(db_fournisseur)
    return db_fournisseur


@router.delete("/fournisseurs/{id}")
def delete_fournisseur(id: int, db: Session = Depends(get_db)):
    db_fournisseur = db.query(models.Fournisseur).get(id)
    if not db_fournisseur:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    db.delete(db_fournisseur)
    db.commit()
    return {"ok": True}

# CLIENTS
@router.get("/clients", response_model=list[schemas.ClientRead])
def list_clients(db: Session = Depends(get_db)):
    return db.query(models.Client).all()

@router.post("/clients", response_model=schemas.ClientRead)
def create_client(client: schemas.ClientCreate, db: Session = Depends(get_db)):
    db_client = models.Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@router.put("/clients/{id}", response_model=schemas.ClientRead)
def update_client(id: int, client: schemas.ClientCreate, db: Session = Depends(get_db)):
    db_client = db.query(models.Client).get(id)
    if not db_client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    for key, value in client.dict().items():
        setattr(db_client, key, value)
    db.commit()
    db.refresh(db_client)
    return db_client

@router.delete("/clients/{id}")
def delete_client(id: int, db: Session = Depends(get_db)):
    db_client = db.query(models.Client).get(id)
    if not db_client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    db.delete(db_client)
    db.commit()
    return {"ok": True}