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
                    "label": get_item_label(item.type, item.ref_id, db),
                    "statut": item.statut,
                    
                }
                for item in items
            ]

        result.append(entry)
        

    return result


def get_item_label(type_: str, ref_id: int, db: Session = Depends(get_db)):
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
