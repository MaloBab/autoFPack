from fastapi import APIRouter, Depends, HTTPException # type: ignore
from sqlalchemy.orm import Session # type: ignore
from App.database import SessionLocal
from App import models, schemas

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# PRIX

@router.get("/prix", response_model=list[schemas.PrixRead])
def list_prix(db: Session = Depends(get_db)):
    return db.query(models.Prix).all()

@router.post("/prix", response_model=schemas.PrixRead)
def create_prix(prix: schemas.PrixCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Prix).filter(
        models.Prix.produit_id == prix.produit_id,
        models.Prix.client_id == prix.client_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Prix déjà défini pour ce produit et client")

    db_prix = models.Prix(**prix.dict())
    db.add(db_prix)
    db.commit()
    db.refresh(db_prix)
    return db_prix

@router.put("/prix/{produit_id}/{client_id}", response_model=schemas.PrixRead)
def update_prix(produit_id: int, client_id: int, prix: schemas.PrixCreate, db: Session = Depends(get_db)):
    db_prix = db.query(models.Prix).filter(
        models.Prix.produit_id == produit_id,
        models.Prix.client_id == client_id
    ).first()
    if not db_prix:
        raise HTTPException(status_code=404, detail="Prix non trouvé")
    for key, value in prix.model_dump().items():
        setattr(db_prix, key, value)
    db.commit()
    db.refresh(db_prix)
    return db_prix

@router.delete("/prix/{produit_id}/{client_id}")
def delete_prix(produit_id: int, client_id: int, db: Session = Depends(get_db)):
    db_prix = db.query(models.Prix).filter(
        models.Prix.produit_id == produit_id,
        models.Prix.client_id == client_id
    ).first()
    if not db_prix:
        raise HTTPException(status_code=404, detail="Prix non trouvé")
    db.delete(db_prix)
    db.commit()
    return {"ok": True}

@router.get("/prix/{produit_id}/{client_id}", response_model=schemas.PrixRead)
def get_prix(produit_id: int, client_id: int, db: Session = Depends(get_db)):
    db_prix = db.query(models.Prix).filter(
        models.Prix.produit_id == produit_id,
        models.Prix.client_id == client_id
    ).first()
    if not db_prix:
        raise HTTPException(status_code=404, detail="Prix non trouvé")
    return db_prix

