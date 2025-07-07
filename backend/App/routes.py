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

# GROUPS
@router.get("/groupes", response_model=list[schemas.GroupesRead])
def list_groupes(db: Session = Depends(get_db)):
    return db.query(models.Groupes).all()

@router.post("/groupes", response_model=schemas.GroupesRead)
def create_groupe(group: schemas.GroupesCreate, db: Session = Depends(get_db)):
    db_group = models.Groupes(**group.dict())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@router.get("/groupe_items/{groupe_id}", response_model=list[schemas.GroupeItemRead])
def list_groupe_items(groupe_id: int, db: Session = Depends(get_db)):
    return db.query(models.GroupeItem).filter(models.GroupeItem.group_id == groupe_id).all()

@router.post("/groupe_items", response_model=schemas.GroupeItemRead)
def create_groupe_item(item: schemas.GroupeItemCreate, db: Session = Depends(get_db)):
    db_item = models.GroupeItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# FPACK CONFIG COLUMNS
@router.get("/fpack_config_columns/{fpack_id}")
def get_config_columns(fpack_id: int, db: Session = Depends(get_db)):
    columns = db.query(models.FPackConfigColumn).filter_by(fpack_id=fpack_id).order_by(models.FPackConfigColumn.ordre).all()
    result = []

    for col in columns:
        entry = {
            "type": col.type,
            "ref_id": col.ref_id,
            "ordre": col.ordre
        }

        # Ajout du display_name selon le type
        if col.type == "produit":
            produit = db.query(models.Produit).filter_by(id=col.ref_id).first()
            entry["display_name"] = produit.nom if produit else f"(produit {col.ref_id})"

        elif col.type == "equipement":
            eq = db.query(models.Equipements).filter_by(id=col.ref_id).first()
            entry["display_name"] = eq.nom if eq else f"(équipement {col.ref_id})"

        elif col.type == "group":
            groupe = db.query(models.Groupes).filter_by(id=col.ref_id).first()
            entry["display_name"] = groupe.nom if groupe else f"(groupe {col.ref_id})"

            items = db.query(models.GroupeItem).filter_by(group_id=col.ref_id).all()
            entry["group_items"] = [
                {
                    "type": item.type,
                    "ref_id": item.ref_id,
                    "label": get_item_label(item.type, item.ref_id, db)
                }
                for item in items
            ]

        result.append(entry)

    return result


def get_item_label(type_: str, ref_id: int, db: Session):
    if type_ == "produit":
        item = db.query(models.Produit).filter_by(id=ref_id).first()
        return item.nom if item else f"(produit {ref_id})"
    elif type_ == "equipement":
        item = db.query(models.Equipements).filter_by(id=ref_id).first()
        return item.nom if item else f"(équipement {ref_id})"
    elif type_ == "robot":
        item = db.query(models.Robots).filter_by(id=ref_id).first()
        return item.nom if item else f"(robot {ref_id})"
    return f"{type_} {ref_id}"

@router.post("/fpack_config_columns", response_model=schemas.FPackConfigColumnRead)
def create_fpack_column(col: schemas.FPackConfigColumnCreate, db: Session = Depends(get_db)):
    db_col = models.FPackConfigColumn(**col.dict())
    db.add(db_col)
    db.commit()
    db.refresh(db_col)
    return db_col

@router.put("/fpack_config_columns/{id}", response_model=schemas.FPackConfigColumnRead)
def update_fpack_column(id: int, col: schemas.FPackConfigColumnCreate, db: Session = Depends(get_db)):
    db_col = db.query(models.FPackConfigColumn).get(id)
    if not db_col:
        raise HTTPException(status_code=404, detail="Colonne de configuration non trouvée")
    for key, value in col.dict().items():
        setattr(db_col, key, value)
    db.commit()
    db.refresh(db_col)
    return db_col

@router.delete("/fpack_config_columns/{id}")
def delete_fpack_column(id: int, db: Session = Depends(get_db)):
    db_col = db.query(models.FPackConfigColumn).get(id)
    if not db_col:
        raise HTTPException(status_code=404, detail="Colonne de configuration non trouvée")
    db.delete(db_col)
    db.commit()
    return {"ok": True}

@router.delete("/fpack_config_columns/clear/{fpack_id}")
def clear_fpack_config_columns(fpack_id: int, db: Session = Depends(get_db)):
    db.query(models.FPackConfigColumn).filter(models.FPackConfigColumn.fpack_id == fpack_id).delete()
    db.commit()
    return {"ok": True}