from fastapi import APIRouter, Depends, HTTPException 
from sqlalchemy.orm import Session 
from App.database import SessionLocal
from App import models, schemas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        
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

    equipements = db.query(models.Equipement_Produit).filter(
        models.Equipement_Produit.produit_id == id
    ).all()

    if equipements:
        equipement_ids = {ep.equipement_id for ep in equipements}
        noms = db.query(models.Equipements.nom).filter(models.Equipements.id.in_(equipement_ids)).all()
        noms_liste = [nom for (nom,) in noms]
        raise HTTPException(
            status_code=400,
            detail=f"Suppression impossible : {db_produit.nom} est lié aux équipement(s) : {', '.join(noms_liste)}"
        )

    db.delete(db_produit)
    db.commit()
    return {"ok": True}

@router.get("/produits/{id}", response_model=schemas.ProduitRead)
def get_produit(id: int, db: Session = Depends(get_db)):
    produit = db.query(models.Produit).get(id)
    if not produit:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return produit


@router.post("/produits/{produit_id}/duplicate", response_model=schemas.ProduitRead)
def duplicate_produit(produit_id: int, db: Session = Depends(get_db)):
    original = db.query(models.Produit).filter(models.Produit.id == produit_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Produit non trouvé")

    new_produit = models.Produit(
        reference = original.reference,
        nom=original.nom + " (copie)",
        description=original.description,
        fournisseur_id=original.fournisseur_id,
        type=original.type,
    )
    db.add(new_produit)
    db.commit()
    db.refresh(new_produit)

    return new_produit

# PRODUIT-INCOMPATIBILITÉS
@router.get("/produit-incompatibilites", response_model=list[schemas.ProduitIncompatibiliteRead])
def list_incompatibilites(db: Session = Depends(get_db)):
    return db.query(models.ProduitIncompatibilite).all()

@router.post("/produit-incompatibilites", response_model=schemas.ProduitIncompatibiliteRead)
def create_incompatibilite(incomp: schemas.ProduitIncompatibiliteCreate, db: Session = Depends(get_db)):
    db_incomp = models.ProduitIncompatibilite(**incomp.dict())
    db.add(db_incomp)
    db.commit()
    return db_incomp

@router.delete("/produit-incompatibilites")
def delete_produit_incompatibilite(inc: schemas.ProduitIncompatibiliteCreate, db: Session = Depends(get_db)):
    db.query(models.ProduitIncompatibilite).filter(
        models.ProduitIncompatibilite.produit_id_1 == inc.produit_id_1,
        models.ProduitIncompatibilite.produit_id_2 == inc.produit_id_2
    ).delete()
    db.commit()
    return {"ok": True}