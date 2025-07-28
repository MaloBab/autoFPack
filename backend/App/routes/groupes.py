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