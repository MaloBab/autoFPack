from fastapi import APIRouter, Depends, HTTPException 
from sqlalchemy.orm import Session 
from App.database import SessionLocal
from App import models, schemas
from sqlalchemy.orm import selectinload


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


@router.get("/equipements/{id}", response_model=schemas.EquipementRead)
def get_equipement(id: int, db: Session = Depends(get_db)):
    equipement = db.query(models.Equipements)\
        .options(selectinload(models.Equipements.equipement_produit))\
        .filter(models.Equipements.id == id)\
        .first()
    if not equipement:
        raise HTTPException(status_code=404, detail="Équipement non trouvé")
    return equipement

# EQUIPEMENTS PRODUITS

@router.get("/equipementproduits", response_model=dict[int, list[schemas.EquipementProduitRead]])
def get_all_equipement_produits(db: Session = Depends(get_db)):
    results = db.query(models.Equipement_Produit).all()

    equipement_dict: dict[int, list[models.Equipement_Produit]] = {}
    for ep in results:
        equipement_dict.setdefault(ep.equipement_id, []).append(ep)

    return equipement_dict

@router.get("/equipementproduit/{equipement_id}", response_model=list[schemas.EquipementProduitRead])
def get_equipement_produit_by_equipement(equipement_id: int, db: Session = Depends(get_db)):
    return db.query(models.Equipement_Produit).filter(models.Equipement_Produit.equipement_id == equipement_id).all()

@router.post("/equipementproduit", response_model=schemas.EquipementProduitRead)
def create_or_update_equipement_produit(equipement_produit: schemas.EquipementProduitCreate, db: Session = Depends(get_db)):
    ep = db.query(models.Equipement_Produit).filter(
        models.Equipement_Produit.equipement_id == equipement_produit.equipement_id,
        models.Equipement_Produit.produit_id == equipement_produit.produit_id
    ).first()
    if ep:
        ep.quantite = equipement_produit.quantite
    else:
        ep = models.Equipement_Produit(**equipement_produit.dict())
    db.add(ep)

    db.commit()
    db.refresh(ep)
    return ep


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




