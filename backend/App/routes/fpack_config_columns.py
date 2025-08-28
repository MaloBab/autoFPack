from fastapi import APIRouter, Depends, HTTPException #type: ignore
from sqlalchemy.orm import Session  #type: ignore
from App.database import SessionLocal
from App import models, schemas

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_item_label(type_: str, ref_id: int, db: Session) -> str:
    """Fonction utilitaire pour récupérer le label d'un item selon son type"""
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

# FPACK CONFIG COLUMNS
@router.get("/fpack_config_columns/{fpack_id}")
def get_config_columns(fpack_id: int, db: Session = Depends(get_db)):
    """Récupère la configuration des colonnes d'un FPack avec validation"""
    fpack = db.query(models.FPack).get(fpack_id)
    if not fpack:
        raise HTTPException(status_code=404, detail="FPack non trouvé")
    
    columns = db.query(models.FPackConfigColumn)\
        .filter_by(fpack_id=fpack_id)\
        .order_by(models.FPackConfigColumn.ordre)\
        .all()
    
    result = []

    for col in columns:
        entry = {
            "id": col.id,  
            "fpack_id": col.fpack_id,  
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

            if col.ref_id:
                items = db.query(models.GroupeItem).filter_by(group_id=col.ref_id).all()
                entry["group_items"] = [
                    {
                        "id": item.id,  
                        "group_id": item.group_id, 
                        "type": item.type,
                        "ref_id": item.ref_id,
                        "label": get_item_label(item.type, item.ref_id, db),
                        "statut": item.statut
                    }
                    for item in items
                ]
            else:
                entry["group_items"] = []
        else:
            entry["display_name"] = f"{col.type} {col.ref_id}"

        result.append(entry)
    
    return {
        "fpack_id": fpack_id,
        "fpack_nom": fpack.nom,
        "columns": result,
        "total_columns": len(result)
    }

@router.post("/fpack_config_columns", response_model=schemas.FPackConfigColumnRead)
def create_fpack_column(col: schemas.FPackConfigColumnCreate, db: Session = Depends(get_db)):
    """Crée une nouvelle colonne de configuration avec validations"""
    fpack = db.query(models.FPack).get(col.fpack_id)
    if not fpack:
        raise HTTPException(status_code=404, detail="FPack non trouvé")
    
    if col.type == "produit" and col.ref_id:
        if not db.query(models.Produit).get(col.ref_id):
            raise HTTPException(status_code=404, detail="Produit non trouvé")
    elif col.type == "equipement" and col.ref_id:
        if not db.query(models.Equipements).get(col.ref_id):
            raise HTTPException(status_code=404, detail="Équipement non trouvé")
    elif col.type == "group" and col.ref_id:
        if not db.query(models.Groupes).get(col.ref_id):
            raise HTTPException(status_code=404, detail="Groupe non trouvé")
    
    existing_ordre = db.query(models.FPackConfigColumn)\
        .filter_by(fpack_id=col.fpack_id, ordre=col.ordre)\
        .first()
    
    if existing_ordre:
        raise HTTPException(
            status_code=400, 
            detail=f"L'ordre {col.ordre} est déjà utilisé dans ce FPack"
        )
    
    db_col = models.FPackConfigColumn(**col.dict())
    db.add(db_col)
    db.commit()
    db.refresh(db_col)
    return db_col

@router.put("/fpack_config_columns/{id}", response_model=schemas.FPackConfigColumnRead)
def update_fpack_column(id: int, col: schemas.FPackConfigColumnCreate, db: Session = Depends(get_db)):
    """Met à jour une colonne de configuration avec validations"""
    db_col = db.query(models.FPackConfigColumn).get(id)
    if not db_col:
        raise HTTPException(status_code=404, detail="Colonne de configuration non trouvée")
    
    if col.fpack_id != db_col.fpack_id:
        fpack = db.query(models.FPack).get(col.fpack_id)
        if not fpack:
            raise HTTPException(status_code=404, detail="FPack non trouvé")
    
    if col.type == "produit" and col.ref_id:
        if not db.query(models.Produit).get(col.ref_id):
            raise HTTPException(status_code=404, detail="Produit non trouvé")
    elif col.type == "equipement" and col.ref_id:
        if not db.query(models.Equipements).get(col.ref_id):
            raise HTTPException(status_code=404, detail="Équipement non trouvé")
    elif col.type == "group" and col.ref_id:
        if not db.query(models.Groupes).get(col.ref_id):
            raise HTTPException(status_code=404, detail="Groupe non trouvé")
    
    if col.ordre != db_col.ordre or col.fpack_id != db_col.fpack_id:
        existing_ordre = db.query(models.FPackConfigColumn)\
            .filter_by(fpack_id=col.fpack_id, ordre=col.ordre)\
            .filter(models.FPackConfigColumn.id != id)\
            .first()
        
        if existing_ordre:
            raise HTTPException(
                status_code=400, 
                detail=f"L'ordre {col.ordre} est déjà utilisé dans ce FPack"
            )
    
    for key, value in col.dict().items():
        setattr(db_col, key, value)
    
    db.commit()
    db.refresh(db_col)
    return db_col

@router.delete("/fpack_config_columns/{id}")
def delete_fpack_column(id: int, db: Session = Depends(get_db)):
    """Supprime une colonne de configuration"""
    db_col = db.query(models.FPackConfigColumn).get(id)
    if not db_col:
        raise HTTPException(status_code=404, detail="Colonne de configuration non trouvée")
    
    fpack_id = db_col.fpack_id
    ordre = db_col.ordre
    type_col = db_col.type
    
    db.delete(db_col)
    db.commit()
    
    return {
        "ok": True,
        "message": f"Colonne {type_col} (ordre {ordre}) supprimée du FPack {fpack_id}"
    }

@router.delete("/fpack_config_columns/clear/{fpack_id}")
def clear_fpack_config_columns(fpack_id: int, db: Session = Depends(get_db)):
    """Supprime toutes les colonnes de configuration d'un FPack"""
    fpack = db.query(models.FPack).get(fpack_id)
    if not fpack:
        raise HTTPException(status_code=404, detail="FPack non trouvé")
    
    nb_columns = db.query(models.FPackConfigColumn)\
        .filter(models.FPackConfigColumn.fpack_id == fpack_id)\
        .count()
    
    db.query(models.FPackConfigColumn)\
        .filter(models.FPackConfigColumn.fpack_id == fpack_id)\
        .delete()
    
    db.commit()
    
    return {
        "ok": True,
        "message": f"{nb_columns} colonnes supprimées du FPack '{fpack.nom}'",
        "fpack_id": fpack_id,
        "columns_supprimees": nb_columns
    }

@router.get("/fpack_config_columns/by_fpack/{fpack_id}", response_model=list[schemas.FPackConfigColumnRead])
def list_config_columns_by_fpack(fpack_id: int, db: Session = Depends(get_db)):
    """Liste les colonnes de configuration d'un FPack (format simple)"""
    fpack = db.query(models.FPack).get(fpack_id)
    if not fpack:
        raise HTTPException(status_code=404, detail="FPack non trouvé")
    
    columns = db.query(models.FPackConfigColumn)\
        .filter_by(fpack_id=fpack_id)\
        .order_by(models.FPackConfigColumn.ordre)\
        .all()
    
    return columns

@router.post("/fpack_config_columns/bulk/{fpack_id}")
def create_bulk_config_columns(
    fpack_id: int, 
    columns_data: list[schemas.FPackConfigColumnCreate], 
    db: Session = Depends(get_db)
):
    """Crée plusieurs colonnes de configuration en une fois"""
    fpack = db.query(models.FPack).get(fpack_id)
    if not fpack:
        raise HTTPException(status_code=404, detail="FPack non trouvé")
    
    ordres = [col.ordre for col in columns_data]
    if len(ordres) != len(set(ordres)):
        raise HTTPException(status_code=400, detail="Ordres dupliqués dans le batch")
    
    existing_ordres = set(
        ordre for ordre, in db.query(models.FPackConfigColumn.ordre)
        .filter_by(fpack_id=fpack_id)
        .all()
    )
    
    conflicting_ordres = set(ordres) & existing_ordres
    if conflicting_ordres:
        raise HTTPException(
            status_code=400,
            detail=f"Ordres déjà utilisés: {sorted(conflicting_ordres)}"
        )
    
    created_columns = []
    for col_data in columns_data:
        if col_data.fpack_id != fpack_id:
            raise HTTPException(
                status_code=400,
                detail=f"fpack_id incohérent: attendu {fpack_id}, reçu {col_data.fpack_id}"
            )
        
        db_col = models.FPackConfigColumn(**col_data.dict())
        db.add(db_col)
        created_columns.append(db_col)
    
    db.commit()
    
    for col in created_columns:
        db.refresh(col)
    
    return {
        "ok": True,
        "message": f"{len(created_columns)} colonnes créées pour le FPack '{fpack.nom}'",
        "fpack_id": fpack_id,
        "created_count": len(created_columns),
        "columns": created_columns
    }

@router.put("/fpack_config_columns/reorder/{fpack_id}")
def reorder_config_columns(
    fpack_id: int,
    new_order: list[dict], 
    db: Session = Depends(get_db)
):
    """Réordonne les colonnes de configuration d'un FPack"""
    fpack = db.query(models.FPack).get(fpack_id)
    if not fpack:
        raise HTTPException(status_code=404, detail="FPack non trouvé")
    
    columns = db.query(models.FPackConfigColumn)\
        .filter_by(fpack_id=fpack_id)\
        .all()
    
    columns_map = {col.id: col for col in columns}
    
    provided_ids = {item["id"] for item in new_order}
    existing_ids = set(columns_map.keys())
    
    if provided_ids != existing_ids:
        missing_ids = existing_ids - provided_ids
        extra_ids = provided_ids - existing_ids
        raise HTTPException(
            status_code=400,
            detail=f"IDs manquants: {missing_ids}, IDs inexistants: {extra_ids}"
        )
    
    new_ordres = [item["ordre"] for item in new_order]
    if len(new_ordres) != len(set(new_ordres)):
        raise HTTPException(status_code=400, detail="Ordres dupliqués dans le réordonnancement")
    
    for item in new_order:
        column = columns_map[item["id"]]
        column.ordre = item["ordre"]
    
    db.commit()
    
    return {
        "ok": True,
        "message": f"Réordonnancement appliqué pour {len(new_order)} colonnes",
        "fpack_id": fpack_id,
        "reordered_count": len(new_order)
    }