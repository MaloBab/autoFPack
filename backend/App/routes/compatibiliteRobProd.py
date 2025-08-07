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

@router.get("/robot-produit-compatibilites", response_model=list[schemas.RobotProduitCompatibiliteRead])
def list_robot_compatibilites(db: Session = Depends(get_db)):
    """Liste toutes les compatibilités robot-produit"""
    return db.query(models.RobotProduitCompatibilite).all()

@router.post("/robot-produit-compatibilites", response_model=schemas.RobotProduitCompatibiliteRead)
def create_robot_compatibilite(compat: schemas.RobotProduitCompatibiliteCreate, db: Session = Depends(get_db)):
    """Crée une nouvelle compatibilité robot-produit"""
    # Vérifier si le robot existe
    robot = db.query(models.Robots).filter(models.Robots.id == compat.robot_id).first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot non trouvé")
    
    # Vérifier si le produit existe
    produit = db.query(models.Produit).filter(models.Produit.id == compat.produit_id).first()
    if not produit:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    # Vérifier si la compatibilité existe déjà
    existing = db.query(models.RobotProduitCompatibilite).filter(
        models.RobotProduitCompatibilite.robot_id == compat.robot_id,
        models.RobotProduitCompatibilite.produit_id == compat.produit_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Cette compatibilité existe déjà")
    
    # Créer la compatibilité
    db_compat = models.RobotProduitCompatibilite(**compat.dict())
    db.add(db_compat)
    db.commit()
    db.refresh(db_compat)
    return db_compat

@router.delete("/robot-produit-compatibilites")
def delete_robot_produit_compatibilite(compat: schemas.RobotProduitCompatibiliteCreate, db: Session = Depends(get_db)):
    """Supprime une compatibilité robot-produit"""
    result = db.query(models.RobotProduitCompatibilite).filter(
        models.RobotProduitCompatibilite.robot_id == compat.robot_id,
        models.RobotProduitCompatibilite.produit_id == compat.produit_id
    ).delete()
    
    if result == 0:
        raise HTTPException(status_code=404, detail="Compatibilité non trouvée")
    
    db.commit()
    return {"ok": True}

# ENDPOINTS UTILITAIRES
@router.get("/robots/{robot_id}/compatibilites", response_model=list[schemas.ProduitRead])
def get_robot_compatible_produits(robot_id: int, db: Session = Depends(get_db)):
    """Récupère tous les produits compatibles avec un robot donné"""
    robot = db.query(models.Robots).filter(models.Robots.id == robot_id).first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot non trouvé")
    
    compatible_produits = db.query(models.Produit).join(
        models.RobotProduitCompatibilite,
        models.Produit.id == models.RobotProduitCompatibilite.produit_id
    ).filter(
        models.RobotProduitCompatibilite.robot_id == robot_id
    ).all()
    return compatible_produits

@router.get("/produits/{produit_id}/robots-compatibles", response_model=list[schemas.RobotRead])
def get_produit_compatible_robots(produit_id: int, db: Session = Depends(get_db)):
    """Récupère tous les robots compatibles avec un produit donné"""
    produit = db.query(models.Produit).filter(models.Produit.id == produit_id).first()
    if not produit:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    compatible_robots = db.query(models.Robots).join(
        models.RobotProduitCompatibilite,
        models.Robots.id == models.RobotProduitCompatibilite.robot_id
    ).filter(
        models.RobotProduitCompatibilite.produit_id == produit_id
    ).all()
    
    return compatible_robots

@router.post("/robots/{robot_id}/batch-compatibilites")
def add_batch_compatibilites(
    robot_id: int, 
    produit_ids: list[int], 
    db: Session = Depends(get_db)
):
    """Ajoute plusieurs compatibilités en une fois pour un robot"""
    robot = db.query(models.Robots).filter(models.Robots.id == robot_id).first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot non trouvé")
    
    # Vérifier que tous les produits existent
    existing_produits = db.query(models.Produit.id).filter(
        models.Produit.id.in_(produit_ids)
    ).all()
    existing_ids = {p.id for p in existing_produits}
    invalid_ids = set(produit_ids) - existing_ids
    
    if invalid_ids:
        raise HTTPException(
            status_code=400, 
            detail=f"Produits non trouvés: {list(invalid_ids)}"
        )
    
    # Récupérer les compatibilités existantes
    existing_compat = db.query(models.RobotProduitCompatibilite.produit_id).filter(
        models.RobotProduitCompatibilite.robot_id == robot_id,
        models.RobotProduitCompatibilite.produit_id.in_(produit_ids)
    ).all()
    existing_produit_ids = {c.produit_id for c in existing_compat}
    
    # Créer seulement les nouvelles compatibilités
    new_produit_ids = set(produit_ids) - existing_produit_ids
    new_compatibilites = [
        models.RobotProduitCompatibilite(robot_id=robot_id, produit_id=pid)
        for pid in new_produit_ids
    ]
    
    if new_compatibilites:
        db.add_all(new_compatibilites)
        db.commit()
    
    return {
        "added": len(new_compatibilites),
        "skipped": len(existing_produit_ids),
        "total": len(produit_ids)
    }

@router.delete("/robots/{robot_id}/compatibilites")
def delete_all_robot_compatibilites(robot_id: int, db: Session = Depends(get_db)):
    """Supprime toutes les compatibilités d'un robot"""
    robot = db.query(models.Robots).filter(models.Robots.id == robot_id).first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot non trouvé")
    
    deleted_count = db.query(models.RobotProduitCompatibilite).filter(
        models.RobotProduitCompatibilite.robot_id == robot_id
    ).delete()
    
    db.commit()
    return {"deleted": deleted_count}


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