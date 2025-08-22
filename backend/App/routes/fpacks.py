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
    
    linked_projects = db.query(models.SousProjetFpack).filter(models.SousProjetFpack.fpack_id == id).count()
    if linked_projects > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de supprimer ce fpack car il est utilisé dans {linked_projects} projet(s)."
        )
    db.delete(db_fpack)
    db.commit()
    return {"ok": True}

@router.get("/fpacks/{id}", response_model=schemas.FPackRead)
def get_fpack(id: int, db: Session = Depends(get_db)):
    db_fpack = db.query(models.FPack).get(id)
    if not db_fpack:
        raise HTTPException(status_code=404, detail="FPack non trouvé")
    return db_fpack

@router.post("/fpacks/{fpack_id}/duplicate", response_model=schemas.FPackRead)
def duplicate_fpack(fpack_id: int, db: Session = Depends(get_db)):
    original_fpack = db.query(models.FPack).filter(models.FPack.id == fpack_id).first()
    if not original_fpack:
        raise HTTPException(status_code=404, detail="FPack non trouvée")

    new_fpack = models.FPack(
        nom=original_fpack.nom + " (copie)",
        client=original_fpack.client,
        fpack_abbr=original_fpack.fpack_abbr,
    )
    db.add(new_fpack)
    db.commit()
    db.refresh(new_fpack)

    config_columns = db.query(models.FPackConfigColumn).filter_by(fpack_id=fpack_id).all()
    for col in config_columns:
        copied_col = models.FPackConfigColumn(
            fpack_id=new_fpack.id,
            ordre=col.ordre,
            type=col.type,
            ref_id=col.ref_id
        )
        db.add(copied_col)

    db.commit()

    return new_fpack

