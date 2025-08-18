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

    # Vérification des équipements (table FPM_equipement_produit)
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

    # Vérification des prix (table FPM_prix)
    prix = db.query(models.Prix).filter(models.Prix.produit_id == id).all()
    if prix:        
        raise HTTPException(
            status_code=400,
            detail=f"Suppression impossible : {db_produit.nom} a des prix définis."
        )

    # Vérification des incompatibilités (table FPM_produit_incompatibilites)
    # Le produit peut être dans produit_id_1 ou produit_id_2
    incompatibilites_1 = db.query(models.ProduitIncompatibilite).filter(
        models.ProduitIncompatibilite.produit_id_1 == id
    ).all()
    
    incompatibilites_2 = db.query(models.ProduitIncompatibilite).filter(
        models.ProduitIncompatibilite.produit_id_2 == id
    ).all()

    if incompatibilites_1 or incompatibilites_2:
        # Récupérer les noms des produits incompatibles
        produits_incompatibles = set()
        
        for inc in incompatibilites_1:
            produit_nom = db.query(models.Produit.nom).filter(models.Produit.id == inc.produit_id_2).first()
            if produit_nom:
                produits_incompatibles.add(produit_nom[0])
        
        for inc in incompatibilites_2:
            produit_nom = db.query(models.Produit.nom).filter(models.Produit.id == inc.produit_id_1).first()
            if produit_nom:
                produits_incompatibles.add(produit_nom[0])
        
        produits_liste = list(produits_incompatibles)
        
        raise HTTPException(
            status_code=400,
            detail=f"Suppression impossible : {db_produit.nom} a des incompatibilités définies avec : {', '.join(produits_liste)}"
        )

    # Vérification des compatibilités robot (table FPM_robot_produit_compatibilites)
    compatibilites_robot = db.query(models.RobotProduitCompatibilite).filter(
        models.RobotProduitCompatibilite.produit_id == id
    ).all()
    
    if compatibilites_robot:
        robot_ids = {comp.robot_id for comp in compatibilites_robot}
        robots = db.query(models.Robots.nom).filter(models.Robots.id.in_(robot_ids)).all()
        robots_liste = [nom for (nom,) in robots if nom]  # Filtrer les None si le nom peut être null
        
        raise HTTPException(
            status_code=400,
            detail=f"Suppression impossible : {db_produit.nom} est compatible avec le(s) robot(s) : {', '.join(robots_liste)}"
        )

    # Vérification dans les groupes (table FPM_groupe_items avec type='product')
    groupe_items = db.query(models.GroupeItem).filter(
        models.GroupeItem.type == 'product',
        models.GroupeItem.ref_id == id
    ).all()
    
    if groupe_items:
        groupe_ids = {item.group_id for item in groupe_items}
        groupes = db.query(models.Groupes.nom).filter(models.Groupes.id.in_(groupe_ids)).all()
        groupes_liste = [nom for (nom,) in groupes]
        
        raise HTTPException(
            status_code=400,
            detail=f"Suppression impossible : {db_produit.nom} est utilisé dans le(s) groupe(s) : {', '.join(groupes_liste)}"
        )

    # Vérification dans les configurations FPack (table FPM_fpack_config_columns avec type='product')
    fpack_configs = db.query(models.FPackConfigColumn).filter(
        models.FPackConfigColumn.type == 'product',
        models.FPackConfigColumn.ref_id == id
    ).all()
    
    if fpack_configs:
        fpack_ids = {config.fpack_id for config in fpack_configs}
        fpacks = db.query(models.FPack.nom).filter(models.FPack.id.in_(fpack_ids)).all()
        fpacks_liste = [nom for (nom,) in fpacks]
        
        raise HTTPException(
            status_code=400,
            detail=f"Suppression impossible : {db_produit.nom} est utilisé dans la configuration des FPack(s) : {', '.join(fpacks_liste)}"
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

