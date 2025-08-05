from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from App.database import SessionLocal
from App import models, schemas

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# GET - liste complète
@router.get("/projets-global", response_model=list[schemas.ProjetGlobalRead])
def list_projets_global(db: Session = Depends(get_db)):
    return db.query(models.ProjetGlobal).all()

# GET - un seul
@router.get("/projets-global/{id}", response_model=schemas.ProjetGlobalRead)
def get_projet_global(id: int, db: Session = Depends(get_db)):
    projet = db.query(models.ProjetGlobal).get(id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet global non trouvé")
    return projet

# POST - création
@router.post("/projets-global", response_model=schemas.ProjetGlobalRead)
def create_projet_global(data: schemas.ProjetGlobalCreate, db: Session = Depends(get_db)):
    projet = models.ProjetGlobal(**data.dict())
    db.add(projet)
    db.commit()
    db.refresh(projet)
    return projet

# PUT - modification
@router.put("/projets-global/{id}", response_model=schemas.ProjetGlobalRead)
def update_projet_global(id: int, data: schemas.ProjetGlobalCreate, db: Session = Depends(get_db)):
    projet = db.query(models.ProjetGlobal).get(id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet global non trouvé")

    for key, value in data.dict().items():
        setattr(projet, key, value)

    db.commit()
    db.refresh(projet)
    return projet

# DELETE - suppression
@router.delete("/projets-global/{id}")
def delete_projet_global(id: int, db: Session = Depends(get_db)):
    projet = db.query(models.ProjetGlobal).get(id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet global non trouvé")

    projets_associes = db.query(models.Projet).filter(models.Projet.id_global == id).all()
    if projets_associes:
        noms = [p.nom for p in projets_associes]
        raise HTTPException(
            status_code=400,
            detail=f"Suppression impossible : ce projet global est lié à des projets : {', '.join(noms)}"
        )

    db.delete(projet)
    db.commit()
    return {"ok": True}