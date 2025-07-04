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

# ROBOTS
@router.get("/robots", response_model=list[schemas.RobotRead])
def list_robots(db: Session = Depends(get_db)):
    return db.query(models.Robots).all()

@router.post("/robots", response_model=schemas.RobotRead)
def create_robot(robot: schemas.RobotCreate, db: Session = Depends(get_db)):
    db_robot = models.Robots(**robot.dict())
    db.add(db_robot)
    db.commit()
    db.refresh(db_robot)
    return db_robot

@router.put("/robots/{id}", response_model=schemas.RobotRead)
def update_robot(id: int, robot: schemas.RobotCreate, db: Session = Depends(get_db)):
    db_robot = db.query(models.Robots).get(id)
    if not db_robot:
        raise HTTPException(status_code=404, detail="Robot non trouvé")
    for key, value in robot.dict().items():
        setattr(db_robot, key, value)
    db.commit()
    db.refresh(db_robot)
    return db_robot

@router.delete("/robots/{id}")
def delete_robot(id: int, db: Session = Depends(get_db)):
    db_robot = db.query(models.Robots).get(id)
    if not db_robot:
        raise HTTPException(status_code=404, detail="Robot non trouvé")
    db.delete(db_robot)
    db.commit()
    return {"ok": True}

# EQUIPEMENTS
@router.get("/equipements", response_model=list[schemas.EquipementRead])
def list_equipements(db: Session = Depends(get_db)):
    return db.query(models.Equipements).all()

@router.post("/equipements", response_model=schemas.EquipementRead)
def create_equipement(equipement: schemas.EquipementCreate, db: Session = Depends(get_db)):
    db_equipement = models.Equipements(**equipement.dict())
    db.add(db_equipement)
    db.commit()
    db.refresh(db_equipement)
    return db_equipement

@router.put("/equipements/{id}", response_model=schemas.EquipementRead)
def update_equipement(id: int, equipement: schemas.EquipementCreate, db: Session = Depends(get_db)):
    db_equipement = db.query(models.Equipements).get(id)
    if not db_equipement:
        raise HTTPException(status_code=404, detail="Equipement non trouvé")
    for key, value in equipement.dict().items():
        setattr(db_equipement, key, value)
    db.commit()
    db.refresh(db_equipement)
    return db_equipement

@router.delete("/equipements/{id}")
def delete_equipement(id: int, db: Session = Depends(get_db)):
    db_equipement = db.query(models.Equipements).get(id)
    if not db_equipement:
        raise HTTPException(status_code=404, detail="Equipement non trouvé")
    db.delete(db_equipement)
    db.commit()
    return {"ok": True}

# EQUIPEMENTS PRODUITS


@router.get("/equipementproduit/{equipement_id}", response_model=list[schemas.EquipementProduitRead])
def get_equipement_produit_by_equipement(equipement_id: int, db: Session = Depends(get_db)):
    return db.query(models.Equipement_Produit).filter(models.Equipement_Produit.equipement_id == equipement_id).all()

@router.post("/equipementproduit", response_model=schemas.EquipementProduitRead)
def create_equipement_produit(equipement_produit: schemas.EquipementProduitCreate, db: Session = Depends(get_db)):
    db_equipement_produit = models.Equipement_Produit(**equipement_produit.dict())
    db.add(db_equipement_produit)
    db.commit()
    db.refresh(db_equipement_produit)
    return db_equipement_produit


@router.delete("/equipementproduit/{id}")
def delete_equipement_produit(id: int, db: Session = Depends(get_db)):
    db_equipement_produit = db.query(models.Equipement_Produit).get(id)
    if not db_equipement_produit:
        raise HTTPException(status_code=404, detail="Equipement de produit non trouvé")
    db.delete(db_equipement_produit)
    db.commit()
    return {"ok": True}

@router.delete("/equipementproduit/clear/{equipement_id}")
def clear_equipement_produits(equipement_id: int, db: Session = Depends(get_db)):
    db.query(models.Equipement_Produit).filter(models.Equipement_Produit.equipement_id == equipement_id).delete()
    db.commit()
    return {"ok": True}


@router.get("/equipements/{equipement_id}")
def get_equipement(equipement_id: int, db: Session = Depends(get_db)):
    equipement = db.query(models.Equipements).filter(models.Equipements.id == equipement_id).first()
    if not equipement:
        raise HTTPException(status_code=404, detail="Equipement not found")
    return equipement


# FPACKS
@router.get("/fpacks", response_model=list[schemas.FPackRead])
def list_fpacks(db: Session = Depends(get_db)):
    return db.query(models.FPack).all()

@router.post("/fpacks", response_model=schemas.FPackRead)
def create_fpack(fpack: schemas.FPackCreate, db: Session = Depends(get_db)):
    db_fpack = models.FPack(**fpack.dict())
    db.add(db_fpack)
    db.commit()
    db.refresh(db_fpack)
    return db_fpack

@router.put("/fpacks/{id}", response_model=schemas.FPackRead)
def update_fpack(id: int, fpack: schemas.FPackCreate, db: Session = Depends(get_db)):
    db_fpack = db.query(models.FPack).get(id)
    if not db_fpack:
        raise HTTPException(status_code=404, detail="FPack non trouvé")
    for key, value in fpack.dict().items():
        setattr(db_fpack, key, value)
    db.commit()
    db.refresh(db_fpack)
    return db_fpack

@router.delete("/fpacks/{id}")
def delete_fpack(id: int, db: Session = Depends(get_db)):
    db_fpack = db.query(models.FPack).get(id)
    if not db_fpack:
        raise HTTPException(status_code=404, detail="FPack non trouvé")
    db.delete(db_fpack)
    db.commit()
    return {"ok": True}