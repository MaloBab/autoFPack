
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from App.database import SessionLocal
from App import models, schemas
from typing import List, Optional
from collections import defaultdict

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========== PROJETS GLOBAUX ==========


@router.get("/projets_globaux/stats", response_model=schemas.ProjetStats)
def get_projets_stats(db: Session = Depends(get_db)):
    """Statistiques sur les projets globaux"""
    nb_projets_globaux = db.query(models.ProjetGlobal).count()
    nb_sous_projets = db.query(models.SousProjet).count()
    projets_par_client_raw = db.query(
        models.Client.nom,
        func.count(models.ProjetGlobal.id).label('count')
    ).join(
        models.ProjetGlobal, models.Client.id == models.ProjetGlobal.client
    ).group_by(models.Client.nom).all()
    projets_par_client = [schemas.ProjetParClient(client=nom, count=count) for nom, count in projets_par_client_raw]
    sous_projets_complets = 0
    sous_projets_incomplets = 0

    sous_projets = db.query(models.SousProjet).all()
    for sp in sous_projets:
        sp_fpack = db.query(models.SousProjetFpack).filter_by(sous_projet_id=sp.id).first()
        if sp_fpack:
            nb_selections = db.query(models.ProjetSelection).filter_by(sous_projet_fpack_id=sp_fpack.id).count()
            nb_groupes_attendus = db.query(models.FPackConfigColumn).filter(
                models.FPackConfigColumn.fpack_id == sp_fpack.fpack_id,
                models.FPackConfigColumn.type == "group"
            ).count()
            if nb_selections >= nb_groupes_attendus and nb_groupes_attendus > 0:
                sous_projets_complets += 1
            else:
                sous_projets_incomplets += 1
        else:
            sous_projets_incomplets += 1

    return schemas.ProjetStats(
        nb_projets_globaux=nb_projets_globaux,
        nb_sous_projets=nb_sous_projets,
        projets_par_client=projets_par_client,
        sous_projets_complets=sous_projets_complets,
        sous_projets_incomplets=sous_projets_incomplets
    )


@router.get("/projets_globaux", response_model=List[schemas.ProjetGlobalReadWithSousProjets])
def list_projets_globaux(
    client_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Liste tous les projets globaux avec leurs sous-projets"""
    query = db.query(models.ProjetGlobal).options(
        joinedload(models.ProjetGlobal.projets).joinedload(models.SousProjet.fpacks).joinedload(models.SousProjetFpack.fpack),
        joinedload(models.ProjetGlobal.client_rel)
    )
    
    if client_id:
        query = query.filter(models.ProjetGlobal.client == client_id)
    
    projets = query.all()
    
    result = []
    for projet in projets:
        # Construire les sous-projets avec détails
        sous_projets_details = []
        for sp in projet.projets:
            # Utiliser la relation pour récupérer tous les FPacks
            sp_fpacks = sp.fpacks  # Utilise la relation définie dans le modèle
            
            if sp_fpacks:
                # Créer un tableau fpacks pour le nouveau format
                fpacks_array = []
                
                # Calculer les stats globales du sous-projet
                total_selections = 0
                total_groupes_attendus = 0
                
                for sp_fpack in sp_fpacks:
                    fpack_nom = sp_fpack.fpack.nom if sp_fpack.fpack else None
                    
                    # Compter les sélections pour ce FPack spécifique
                    nb_selections_fpack = db.query(models.ProjetSelection).filter(
                        models.ProjetSelection.sous_projet_fpack_id == sp_fpack.id
                    ).count()
                    
                    # Compter les groupes attendus pour ce FPack
                    nb_groupes_attendus_fpack = db.query(models.FPackConfigColumn).filter(
                        models.FPackConfigColumn.fpack_id == sp_fpack.fpack_id,
                        models.FPackConfigColumn.type == "group"
                    ).count()
                    
                    # Ajouter aux totaux
                    total_selections += nb_selections_fpack
                    total_groupes_attendus += nb_groupes_attendus_fpack
                    
                    # Ajouter ce FPack au tableau
                    fpacks_array.append({
                        "id": sp_fpack.id,  # ID de l'enregistrement SousProjetFpack
                        "fpack_id": sp_fpack.fpack_id,  # ID du template FPack
                        "fpack_nom": fpack_nom,
                        "FPack_number": sp_fpack.FPack_number,
                        "Robot_Location_Code": sp_fpack.Robot_Location_Code,
                        "nb_selections": nb_selections_fpack,
                        "nb_groupes_attendus": nb_groupes_attendus_fpack,
                        "complet": nb_selections_fpack >= nb_groupes_attendus_fpack if nb_groupes_attendus_fpack > 0 else False
                    })
                
                # Déterminer si le sous-projet est complet (tous les FPacks terminés)
                complet = all(fpack["complet"] for fpack in fpacks_array) if fpacks_array else False
                
                sous_projets_details.append({
                    "id": sp.id,
                    "nom": sp.nom,
                    "id_global": sp.id_global,
                    "client_nom": projet.client_rel.nom if projet.client_rel else None,
                    "projet_global_nom": projet.projet,
                    "sous_projet_nom": sp.nom,
                    "complet": complet,
                    "nb_selections": total_selections,
                    "nb_groupes_attendus": total_groupes_attendus,
                    "fpacks": fpacks_array,  # Nouveau format avec tous les FPacks
                    # Garder l'ancien format pour compatibilité (utilise le premier FPack)
                    "fpack_id": fpacks_array[0]["fpack_id"] if fpacks_array else None,
                    "fpack_nom": fpacks_array[0]["fpack_nom"] if fpacks_array else None,
                    "FPack_number": fpacks_array[0]["FPack_number"] if fpacks_array else None,
                    "Robot_Location_Code": fpacks_array[0]["Robot_Location_Code"] if fpacks_array else None
                })
            else:
                # Aucun FPack associé
                sous_projets_details.append({
                    "id": sp.id,
                    "nom": sp.nom,
                    "id_global": sp.id_global,
                    "client_nom": projet.client_rel.nom if projet.client_rel else None,
                    "projet_global_nom": projet.projet,
                    "sous_projet_nom": sp.nom,
                    "complet": False,
                    "nb_selections": 0,
                    "nb_groupes_attendus": 0,
                    "fpacks": [],  # Tableau vide
                    "fpack_id": None,
                    "fpack_nom": None,
                    "FPack_number": None,
                    "Robot_Location_Code": None
                })
        
        result.append({
            "id": projet.id,
            "projet": projet.projet,
            "client": projet.client,
            "sous_projets": sous_projets_details,
            "client_nom": projet.client_rel.nom if projet.client_rel else None
        })
    
    return result

@router.get("/projets_globaux/{id}", response_model=schemas.ProjetGlobalReadWithSousProjets)
def get_projet_global(id: int, db: Session = Depends(get_db)):
    """Récupère un projet global par son ID avec ses sous-projets"""
    projet = db.query(models.ProjetGlobal).options(
        joinedload(models.ProjetGlobal.projets),
        joinedload(models.ProjetGlobal.client_rel)
    ).get(id)
    
    if not projet:
        raise HTTPException(status_code=404, detail="Projet global non trouvé")
    
    # Même logique que list_projets_globaux pour un seul projet
    sous_projets_details = []
    for sp in projet.projets:
        sp_fpack = db.query(models.SousProjetFpack).filter_by(sous_projet_id=sp.id).first()
        fpack_nom = None
        fpack_number = None
        robot_location_code = None
        
        if sp_fpack:
            fpack = db.query(models.FPack).get(sp_fpack.fpack_id)
            fpack_nom = fpack.nom if fpack else None
            fpack_number = sp_fpack.FPack_number
            robot_location_code = sp_fpack.Robot_Location_Code
        
        nb_selections = db.query(models.ProjetSelection).join(
            models.SousProjetFpack, 
            models.ProjetSelection.sous_projet_fpack_id == models.SousProjetFpack.id
        ).filter(models.SousProjetFpack.sous_projet_id == sp.id).count()
        
        nb_groupes_attendus = 0
        if sp_fpack:
            nb_groupes_attendus = db.query(models.FPackConfigColumn).filter(
                models.FPackConfigColumn.fpack_id == sp_fpack.fpack_id,
                models.FPackConfigColumn.type == "group"
            ).count()
        
        sous_projets_details.append({
            "id": sp.id,
            "nom": sp.nom,
            "id_global": sp.id_global,
            "fpack_nom": fpack_nom,
            "client_nom": projet.client_rel.nom if projet.client_rel else None,
            "projet_global_nom": projet.projet,
            "sous_projet_nom": sp.nom,
            "complet": nb_selections >= nb_groupes_attendus if nb_groupes_attendus > 0 else False,
            "nb_selections": nb_selections,
            "nb_groupes_attendus": nb_groupes_attendus,
            "FPack_number": fpack_number,
            "Robot_Location_Code": robot_location_code
        })
    
    return {
        "id": projet.id,
        "projet": projet.projet,
        "client": projet.client,
        "sous_projets": sous_projets_details,
        "client_nom": projet.client_rel.nom if projet.client_rel else None
    }

@router.post("/projets_globaux", response_model=schemas.ProjetGlobalRead)
def create_projet_global(projet: schemas.ProjetGlobalCreate, db: Session = Depends(get_db)):
    """Crée un nouveau projet global"""
    # Vérifier que le client existe
    client = db.query(models.Client).get(projet.client)
    if not client:
        raise HTTPException(status_code=400, detail="Client non trouvé")
    
    db_projet = models.ProjetGlobal(**projet.dict())
    db.add(db_projet)
    db.commit()
    db.refresh(db_projet)
    return db_projet

@router.put("/projets_globaux/{id}", response_model=schemas.ProjetGlobalRead)
def update_projet_global(id: int, projet: schemas.ProjetGlobalCreate, db: Session = Depends(get_db)):
    """Met à jour un projet global"""
    db_projet = db.query(models.ProjetGlobal).get(id)
    if not db_projet:
        raise HTTPException(status_code=404, detail="Projet global non trouvé")
    
    # Vérifier que le client existe
    client = db.query(models.Client).get(projet.client)
    if not client:
        raise HTTPException(status_code=400, detail="Client non trouvé")
    
    for key, value in projet.dict().items():
        setattr(db_projet, key, value)
    db.commit()
    db.refresh(db_projet)
    return db_projet

@router.delete("/projets_globaux/{id}")
def delete_projet_global(id: int, db: Session = Depends(get_db)):
    """Supprime un projet global et tous ses sous-projets"""
    db_projet = db.query(models.ProjetGlobal).get(id)
    if not db_projet:
        raise HTTPException(status_code=404, detail="Projet global non trouvé")
    
    # Vérifier s'il y a des sous-projets
    sous_projets = db.query(models.SousProjet).filter(models.SousProjet.id_global == id).all()
    if sous_projets:
        raise HTTPException(
            status_code=400,
            detail=f"Suppression impossible : le projet contient {len(sous_projets)} sous-projet(s)"
        )
    
    db.delete(db_projet)
    db.commit()
    return {"ok": True}



# ========== SOUS-PROJETS ==========

@router.get("/sous_projets", response_model=List[schemas.SousProjetReadWithDetails])
def list_sous_projets(
    projet_global_id: Optional[int] = None,
    client_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Liste tous les sous-projets avec filtres optionnels"""
    query = db.query(models.SousProjet).join(models.ProjetGlobal)
    
    if projet_global_id:
        query = query.filter(models.SousProjet.id_global == projet_global_id)
    
    if client_id:
        query = query.filter(models.ProjetGlobal.client == client_id)
    
    sous_projets = query.all()
    
    result = []
    for sp in sous_projets:
        projet_global = db.query(models.ProjetGlobal).get(sp.id_global)
        client = db.query(models.Client).get(projet_global.client) if projet_global else None
        
        sp_fpack = db.query(models.SousProjetFpack).filter_by(sous_projet_id=sp.id).first()
        fpack_nom = None
        fpack_number = None
        robot_location_code = None
        
        if sp_fpack:
            fpack = db.query(models.FPack).get(sp_fpack.fpack_id)
            fpack_nom = fpack.nom if fpack else None
            fpack_number = sp_fpack.FPack_number
            robot_location_code = sp_fpack.Robot_Location_Code
        
        nb_selections = db.query(models.ProjetSelection).join(
            models.SousProjetFpack, 
            models.ProjetSelection.sous_projet_fpack_id == models.SousProjetFpack.id
        ).filter(models.SousProjetFpack.sous_projet_id == sp.id).count()
        
        nb_groupes_attendus = 0
        if sp_fpack:
            nb_groupes_attendus = db.query(models.FPackConfigColumn).filter(
                models.FPackConfigColumn.fpack_id == sp_fpack.fpack_id,
                models.FPackConfigColumn.type == "group"
            ).count()
        
        result.append({
            "id": sp.id,
            "nom": sp.nom,
            "id_global": sp.id_global,
            "fpack_id": sp_fpack.fpack_id if sp_fpack else None,
            "fpack_nom": fpack_nom,
            "client_nom": client.nom if client else None,
            "projet_global_nom": projet_global.projet if projet_global else None,
            "sous_projet_nom": sp.nom,
            "complet": nb_selections >= nb_groupes_attendus if nb_groupes_attendus > 0 else False,
            "nb_selections": nb_selections,
            "nb_groupes_attendus": nb_groupes_attendus,
            "FPack_number": fpack_number,
            "Robot_Location_Code": robot_location_code
        })
    
    return result

@router.get("/projets_globaux/{projet_id}/sous_projets", response_model=List[schemas.SousProjetReadWithDetails])
def list_sous_projets_by_projet(projet_id: int, db: Session = Depends(get_db)):
    """Liste tous les sous-projets d'un projet global"""
    return list_sous_projets(projet_global_id=projet_id, db=db)

@router.get("/sous_projets/{id}", response_model=schemas.SousProjetReadWithDetails)
def get_sous_projet(id: int, db: Session = Depends(get_db)):
    """Récupère un sous-projet par son ID"""
    sp = db.query(models.SousProjet).get(id)
    if not sp:
        raise HTTPException(status_code=404, detail="Sous-projet non trouvé")
    
    projet_global = db.query(models.ProjetGlobal).get(sp.id_global)
    client = db.query(models.Client).get(projet_global.client) if projet_global else None
    
    sp_fpack = db.query(models.SousProjetFpack).filter_by(sous_projet_id=sp.id).first()
    fpack_nom = None
    fpack_number = None
    robot_location_code = None
    
    if sp_fpack:
        fpack = db.query(models.FPack).get(sp_fpack.fpack_id)
        fpack_nom = fpack.nom if fpack else None
        fpack_number = sp_fpack.FPack_number
        robot_location_code = sp_fpack.Robot_Location_Code
    
    nb_selections = db.query(models.ProjetSelection).join(
        models.SousProjetFpack, 
        models.ProjetSelection.sous_projet_fpack_id == models.SousProjetFpack.id
    ).filter(models.SousProjetFpack.sous_projet_id == sp.id).count()
    
    nb_groupes_attendus = 0
    if sp_fpack:
        nb_groupes_attendus = db.query(models.FPackConfigColumn).filter(
            models.FPackConfigColumn.fpack_id == sp_fpack.fpack_id,
            models.FPackConfigColumn.type == "group"
        ).count()
    
    return {
        "id": sp.id,
        "nom": sp.nom,
        "id_global": sp.id_global,
        "fpack_id": sp_fpack.fpack_id if sp_fpack else None,
        "fpack_nom": fpack_nom,
        "client_nom": client.nom if client else None,
        "projet_global_nom": projet_global.projet if projet_global else None,
        "sous_projet_nom": sp.nom,
        "complet": nb_selections >= nb_groupes_attendus if nb_groupes_attendus > 0 else False,
        "nb_selections": nb_selections,
        "nb_groupes_attendus": nb_groupes_attendus,
        "FPack_number": fpack_number,
        "Robot_Location_Code": robot_location_code
    }

@router.post("/sous_projets", response_model=schemas.SousProjetRead)
def create_sous_projet(sous_projet: schemas.SousProjetCreate, db: Session = Depends(get_db)):
    """Crée un nouveau sous-projet"""
    # Vérifier que le projet global existe
    projet_global = db.query(models.ProjetGlobal).get(sous_projet.id_global)
    if not projet_global:
        raise HTTPException(status_code=400, detail="Projet global non trouvé")
    
    db_sous_projet = models.SousProjet(**sous_projet.dict())
    db.add(db_sous_projet)
    db.commit()
    db.refresh(db_sous_projet)
    return db_sous_projet

@router.put("/sous_projets/{id}", response_model=schemas.SousProjetRead)
def update_sous_projet(id: int, sous_projet: schemas.SousProjetCreate, db: Session = Depends(get_db)):
    """Met à jour un sous-projet"""
    db_sous_projet = db.query(models.SousProjet).get(id)
    if not db_sous_projet:
        raise HTTPException(status_code=404, detail="Sous-projet non trouvé")
    
    # Vérifier que le projet global existe
    projet_global = db.query(models.ProjetGlobal).get(sous_projet.id_global)
    if not projet_global:
        raise HTTPException(status_code=400, detail="Projet global non trouvé")
    
    for key, value in sous_projet.dict().items():
        setattr(db_sous_projet, key, value)
    db.commit()
    db.refresh(db_sous_projet)
    return db_sous_projet

@router.delete("/sous_projets/{id}")
def delete_sous_projet(id: int, db: Session = Depends(get_db)):
    """Supprime un sous-projet"""
    db_sous_projet = db.query(models.SousProjet).get(id)
    if not db_sous_projet:
        raise HTTPException(status_code=404, detail="Sous-projet non trouvé")
    
    # Vérifier s'il y a des FPacks associés
    fpacks = db.query(models.SousProjetFpack).filter(models.SousProjetFpack.sous_projet_id == id).all()
    if fpacks:
        raise HTTPException(
            status_code=400,
            detail=f"Suppression impossible : le sous-projet contient {len(fpacks)} FPack(s) associé(s)"
        )
    
    db.delete(db_sous_projet)
    db.commit()
    return {"ok": True}

# ========== FPACKS ASSOCIÉS AUX SOUS-PROJETS ==========

@router.get("/sous_projets/{sous_projet_id}/fpacks", response_model=List[schemas.SousProjetFpackRead])
def list_fpacks_by_sous_projet(sous_projet_id: int, db: Session = Depends(get_db)):
    """Liste tous les FPacks associés à un sous-projet"""
    # Vérifier que le sous-projet existe
    sous_projet = db.query(models.SousProjet).get(sous_projet_id)
    if not sous_projet:
        raise HTTPException(status_code=404, detail="Sous-projet non trouvé")
    
    fpacks = db.query(models.SousProjetFpack).filter_by(sous_projet_id=sous_projet_id).all()
    return fpacks

@router.post("/sous_projets/{sous_projet_id}/fpacks", response_model=schemas.SousProjetFpackRead)
def add_fpack_to_sous_projet(
    sous_projet_id: int, 
    fpack_data: schemas.SousProjetFpackCreate, 
    db: Session = Depends(get_db)
):
    """Associe un FPack à un sous-projet"""
    # Vérifier que le sous-projet existe
    sous_projet = db.query(models.SousProjet).get(sous_projet_id)
    if not sous_projet:
        raise HTTPException(status_code=404, detail="Sous-projet non trouvé")
    
    # Vérifier que le FPack existe
    fpack = db.query(models.FPack).get(fpack_data.fpack_id)
    if not fpack:
        raise HTTPException(status_code=400, detail="FPack non trouvé")
    
    db_association = models.SousProjetFpack(
        sous_projet_id=sous_projet_id,
        **fpack_data.dict()
    )
    db.add(db_association)
    db.commit()
    db.refresh(db_association)
    return db_association

@router.put("/sous_projets/{sous_projet_id}/fpacks/{fpack_id}", response_model=schemas.SousProjetFpackRead)
def update_fpack_association(
    sous_projet_id: int,
    fpack_id: int,
    fpack_data: schemas.SousProjetFpackCreate,
    db: Session = Depends(get_db)
):
    """Met à jour l'association FPack/sous-projet"""
    association = db.query(models.SousProjetFpack).filter_by(
        sous_projet_id=sous_projet_id,
        fpack_id=fpack_id
    ).first()
    
    if not association:
        raise HTTPException(status_code=404, detail="Association FPack/sous-projet non trouvée")
    
    for key, value in fpack_data.dict().items():
        setattr(association, key, value)
    
    db.commit()
    db.refresh(association)
    return association

@router.delete("/sous_projets/{sous_projet_id}/fpacks/{fpack_id}")
def remove_fpack_from_sous_projet(sous_projet_id: int, fpack_id: int, db: Session = Depends(get_db)):
    """Retire un FPack d'un sous-projet"""
    association = db.query(models.SousProjetFpack).filter_by(
        sous_projet_id=sous_projet_id,
        fpack_id=fpack_id
    ).first()
    
    if not association:
        raise HTTPException(status_code=404, detail="Association FPack/sous-projet non trouvée")
    
    # Vérifier s'il y a des sélections
    selections = db.query(models.ProjetSelection).filter_by(sous_projet_fpack_id=association.id).all()
    if selections:
        raise HTTPException(
            status_code=400,
            detail=f"Suppression impossible : cette association contient {len(selections)} sélection(s)"
        )
    
    db.delete(association)
    db.commit()
    return {"ok": True}

# ========== SÉLECTIONS ==========

@router.get("/sous_projets/{sous_projet_id}/fpacks/{fpack_id}/selections", response_model=List[schemas.ProjetSelectionReadWithDetails])
def get_selections_by_fpack(sous_projet_id: int, fpack_id: int, db: Session = Depends(get_db)):
    """Récupère toutes les sélections pour un FPack d'un sous-projet"""
    # Trouver l'association
    association = db.query(models.SousProjetFpack).filter_by(
        sous_projet_id=sous_projet_id,
        fpack_id=fpack_id
    ).first()
    
    if not association:
        raise HTTPException(status_code=404, detail="Association FPack/sous-projet non trouvée")
    
    selections = db.query(models.ProjetSelection).filter_by(
        sous_projet_fpack_id=association.id
    ).all()
    
    result = []
    for sel in selections:
        # Récupérer le nom du groupe
        groupe = db.query(models.Groupes).get(sel.groupe_id)
        groupe_nom = groupe.nom if groupe else None
        
        # Récupérer le nom de l'item selon son type
        item_nom = None
        if sel.type_item == "produit":
            produit = db.query(models.Produit).get(sel.ref_id)
            item_nom = produit.nom if produit else None
        elif sel.type_item == "equipement":
            equipement = db.query(models.Equipements).get(sel.ref_id)
            item_nom = equipement.nom if equipement else None
        elif sel.type_item == "robot":
            robot = db.query(models.Robots).get(sel.ref_id)
            item_nom = robot.nom if robot else None
        
        result.append({
            "sous_projet_fpack_id": sel.sous_projet_fpack_id,
            "groupe_id": sel.groupe_id,
            "type_item": sel.type_item,
            "ref_id": sel.ref_id,
            "groupe_nom": groupe_nom,
            "item_nom": item_nom
        })
    
    return result

@router.post("/sous_projets/{sous_projet_id}/fpacks/{fpack_id}/selections", response_model=schemas.ProjetSelectionRead)
def create_selection(
    sous_projet_id: int,
    fpack_id: int,
    selection: schemas.ProjetSelectionCreate,
    db: Session = Depends(get_db)
):
    """Crée une nouvelle sélection"""
    # Trouver l'association
    association = db.query(models.SousProjetFpack).filter_by(
        sous_projet_id=sous_projet_id,
        fpack_id=fpack_id
    ).first()
    
    if not association:
        raise HTTPException(status_code=404, detail="Association FPack/sous-projet non trouvée")
    
    # Vérifier que le groupe existe
    groupe = db.query(models.Groupes).get(selection.groupe_id)
    if not groupe:
        raise HTTPException(status_code=400, detail="Groupe non trouvé")
    
    # Vérifier que l'item existe selon son type
    if selection.type_item == "produit":
        item = db.query(models.Produit).get(selection.ref_id)
    elif selection.type_item == "equipement":
        item = db.query(models.Equipements).get(selection.ref_id)
    elif selection.type_item == "robot":
        item = db.query(models.Robots).get(selection.ref_id)
    else:
        raise HTTPException(status_code=400, detail="Type d'item invalide")
    
    if not item:
        raise HTTPException(status_code=400, detail=f"{selection.type_item.capitalize()} non trouvé")
    
    # Vérifier que cette sélection n'existe pas déjà
    existing = db.query(models.ProjetSelection).filter_by(
        sous_projet_fpack_id=association.id,
        groupe_id=selection.groupe_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Une sélection existe déjà pour ce groupe")
    
    db_selection = models.ProjetSelection(
        sous_projet_fpack_id=association.id,
        **selection.dict()
    )
    db.add(db_selection)
    db.commit()
    db.refresh(db_selection)
    return db_selection

@router.put("/sous_projets/{sous_projet_id}/fpacks/{fpack_id}/selections/{groupe_id}", response_model=schemas.ProjetSelectionRead)
def update_selection(
    sous_projet_id: int,
    fpack_id: int,
    groupe_id: int,
    selection_data: schemas.ProjetSelectionCreate,
    db: Session = Depends(get_db)
):
    """Met à jour une sélection"""
    # Trouver l'association
    association = db.query(models.SousProjetFpack).filter_by(
        sous_projet_id=sous_projet_id,
        fpack_id=fpack_id
    ).first()
    
    if not association:
        raise HTTPException(status_code=404, detail="Association FPack/sous-projet non trouvée")
    
    selection = db.query(models.ProjetSelection).filter_by(
        sous_projet_fpack_id=association.id,
        groupe_id=groupe_id
    ).first()
    
    if not selection:
        raise HTTPException(status_code=404, detail="Sélection non trouvée")
    
    # Vérifier que l'item existe selon son type
    if selection_data.type_item == "produit":
        item = db.query(models.Produit).get(selection_data.ref_id)
    elif selection_data.type_item == "equipement":
        item = db.query(models.Equipements).get(selection_data.ref_id)
    elif selection_data.type_item == "robot":
        item = db.query(models.Robots).get(selection_data.ref_id)
    else:
        raise HTTPException(status_code=400, detail="Type d'item invalide")
    
    if not item:
        raise HTTPException(status_code=400, detail=f"{selection_data.type_item.capitalize()} non trouvé")
    
    for key, value in selection_data.dict().items():
        if key != "sous_projet_fpack_id":  # Ne pas modifier l'ID de l'association
            setattr(selection, key, value)
    
    db.commit()
    db.refresh(selection)
    return selection

@router.delete("/sous_projets/{sous_projet_id}/fpacks/{fpack_id}/selections/{groupe_id}")
def delete_selection(sous_projet_id: int, fpack_id: int, groupe_id: int, db: Session = Depends(get_db)):
    """Supprime une sélection"""
    # Trouver l'association
    association = db.query(models.SousProjetFpack).filter_by(
        sous_projet_id=sous_projet_id,
        fpack_id=fpack_id
    ).first()
    
    if not association:
        raise HTTPException(status_code=404, detail="Association FPack/sous-projet non trouvée")
    
    selection = db.query(models.ProjetSelection).filter_by(
        sous_projet_fpack_id=association.id,
        groupe_id=groupe_id
    ).first()
    
    if not selection:
        raise HTTPException(status_code=404, detail="Sélection non trouvée")
    
    db.delete(selection)
    db.commit()
    return {"ok": True}

# ========== ARBRE COMPLET ==========

@router.get("/projets_tree", response_model=schemas.ProjetTree)
def get_projets_tree(client_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Retourne l'arborescence complète : projets -> sous-projets -> fpacks -> sélections"""
    projets_globaux = list_projets_globaux(client_id=client_id, db=db)
    
    # Enrichir avec les FPacks et sélections
    for projet in projets_globaux:
        for sous_projet in projet["sous_projets"]:
            # Récupérer les FPacks associés
            fpacks = db.query(models.SousProjetFpack).filter_by(
                sous_projet_id=sous_projet["id"]
            ).all()
            
            fpacks_data = []
            for fpack_assoc in fpacks:
                fpack = db.query(models.FPack).get(fpack_assoc.fpack_id)
                if not fpack:
                    continue
                
                # Récupérer les sélections
                selections = db.query(models.ProjetSelection).filter_by(
                    sous_projet_fpack_id=fpack_assoc.id
                ).all()
                
                selections_data = []
                for sel in selections:
                    groupe = db.query(models.Groupes).get(sel.groupe_id)
                    
                    # Nom de l'item selon son type
                    item_nom = None
                    if sel.type_item == "produit":
                        produit = db.query(models.Produit).get(sel.ref_id)
                        item_nom = produit.nom if produit else None
                    elif sel.type_item == "equipement":
                        equipement = db.query(models.Equipements).get(sel.ref_id)
                        item_nom = equipement.nom if equipement else None
                    elif sel.type_item == "robot":
                        robot = db.query(models.Robots).get(sel.ref_id)
                        item_nom = robot.nom if robot else None
                    
                    selections_data.append({
                        "groupe_id": sel.groupe_id,
                        "groupe_nom": groupe.nom if groupe else None,
                        "type_item": sel.type_item,
                        "ref_id": sel.ref_id,
                        "item_nom": item_nom
                    })
                
                fpacks_data.append({
                    "id": fpack.id,
                    "nom": fpack.nom,
                    "fpack_abbr": fpack.fpack_abbr,
                    "FPack_number": fpack_assoc.FPack_number,
                    "Robot_Location_Code": fpack_assoc.Robot_Location_Code,
                    "selections": selections_data
                })
            
            sous_projet["fpacks"] = fpacks_data
    
    return {"projets_global": projets_globaux}

# ========== FACTURES ==========

@router.get("/projets_globaux/{id}/facture")
def get_projet_global_facture(id: int, db: Session = Depends(get_db)):
    """Génère la facture globale d'un projet (somme de tous ses sous-projets)"""
    projet_global = db.query(models.ProjetGlobal).get(id)
    if not projet_global:
        raise HTTPException(status_code=404, detail="Projet global non trouvé")
    
    sous_projets = db.query(models.SousProjet).filter(models.SousProjet.id_global == id).all()
    if not sous_projets:
        return {
            "projet_global_id": id,
            "nom_projet_global": projet_global.projet,
            "client_id": projet_global.client,
            "sous_projets_factures": [],
            "totaux_globaux": {
                "produit": 0.0,
                "transport": 0.0,
                "global": 0.0
            },
            "resume_global": {
                "nb_sous_projets": 0,
                "nb_lignes_total": 0
            }
        }
    
    factures_sous_projets = []
    total_produit_global = 0.0
    total_transport_global = 0.0
    nb_lignes_total = 0
    
    for sp in sous_projets:
        try:
            facture_sp = get_sous_projet_facture(sp.id, db)
            factures_sous_projets.append(facture_sp)
            total_produit_global += facture_sp["totaux"]["produit"]
            total_transport_global += facture_sp["totaux"]["transport"]
            nb_lignes_total += facture_sp["resume"]["nb_lignes"]
        except HTTPException:
            # Si un sous-projet n'a pas de facture, on continue
            continue
    
    return {
        "projet_global_id": id,
        "nom_projet_global": projet_global.projet,
        "client_id": projet_global.client,
        "sous_projets_factures": factures_sous_projets,
        "totaux_globaux": {
            "produit": round(total_produit_global, 2),
            "transport": round(total_transport_global, 2),
            "global": round(total_produit_global + total_transport_global, 2)
        },
        "resume_global": {
            "nb_sous_projets": len(factures_sous_projets),
            "nb_lignes_total": nb_lignes_total
        }
    }

@router.get("/sous_projets/{id}/facture")
def get_sous_projet_facture(id: int, db: Session = Depends(get_db)):
    """Génère la facture d'un sous-projet (corrigée)"""
    
    projet = db.query(models.SousProjet).get(id)
    if not projet:
        raise HTTPException(status_code=404, detail="Sous-projet non trouvé")

    # Récupérer les informations de base
    projet_global = db.query(models.ProjetGlobal).get(projet.id_global)
    client_id = projet_global.client if projet_global else None
    
    if not client_id:
        raise HTTPException(status_code=400, detail="Client non trouvé pour ce projet")

    # Récupérer l'association FPack
    sp_fpack = db.query(models.SousProjetFpack)\
        .filter_by(sous_projet_id=id)\
        .first()
    
    if not sp_fpack:
        raise HTTPException(status_code=400, detail="Aucun FPack associé à ce sous-projet")
    
    fpack = db.query(models.FPack).get(sp_fpack.fpack_id)

    # Configuration et sélections
    config_cols = db.query(models.FPackConfigColumn)\
        .filter_by(fpack_id=sp_fpack.fpack_id)\
        .order_by(models.FPackConfigColumn.ordre)\
        .all()
    
    sels = db.query(models.ProjetSelection).filter_by(sous_projet_fpack_id=sp_fpack.id).all()
    sel_map = {s.groupe_id: {"type": s.type_item, "ref_id": s.ref_id} for s in sels}

    # Mapping équipements -> produits
    eq_prods = db.query(models.Equipement_Produit).all()
    eq_map = {}
    for ep in eq_prods:
        eq_map.setdefault(ep.equipement_id, []).append((ep.produit_id, ep.quantite))

    # Calcul des quantités
    produit_counts = defaultdict(int)
    robot_counts = defaultdict(int)

    # Traitement des différents types d'éléments
    for col in config_cols:
        if col.type == "produit":
            produit_counts[col.ref_id] += 1
        elif col.type == "equipement":
            for pid, qte in eq_map.get(col.ref_id, []):
                produit_counts[pid] += qte
        elif col.type == "group":
            chosen = sel_map.get(col.ref_id)
            if not chosen:
                continue
                
            if chosen["type"] == "produit":
                produit_counts[chosen["ref_id"]] += 1
            elif chosen["type"] == "equipement":
                for pid, qte in eq_map.get(chosen["ref_id"], []):
                    produit_counts[pid] += qte
            elif chosen["type"] == "robot":
                robot_counts[chosen["ref_id"]] += 1

    # Récupération des prix et noms
    all_produit_ids = list(produit_counts.keys())
    
    prix_rows = db.query(models.Prix)\
        .filter(
            models.Prix.client_id == client_id,
            models.Prix.produit_id.in_(all_produit_ids)
        ).all() if all_produit_ids else []
    
    prix_map = {p.produit_id: p for p in prix_rows}
    
    prix_robot_rows = db.query(models.PrixRobot)\
        .join(models.Robots, models.Robots.id == models.PrixRobot.id)\
        .filter(
            models.Robots.client == client_id,
            models.PrixRobot.id.in__(robot_counts.keys())
        ).all() if robot_counts else []
    
    prix_robot_map = {p.id: p for p in prix_robot_rows}

    # Noms des produits et robots
    produits_rows = db.query(models.Produit)\
        .filter(models.Produit.id.in_(all_produit_ids))\
        .all() if all_produit_ids else []
    produit_nom_map = {p.id: p.nom for p in produits_rows}

    robot_rows = db.query(models.Robots)\
        .filter(models.Robots.id.in_(robot_counts.keys()))\
        .all() if robot_counts else []
    robot_nom_map = {r.id: r.nom for r in robot_rows}

    # Construction des lignes de facture
    lines = []
    total_produit = 0.00
    total_transport = 0.00

    # Lignes produits
    for pid in sorted(all_produit_ids):
        qte = produit_counts[pid]
        p_rec = prix_map.get(pid)
        prix_prod = float(p_rec.prix_produit) if p_rec else 0.0
        prix_tr = float(p_rec.prix_transport) if p_rec else 0.0
        commentaire = p_rec.commentaire if p_rec else None

        total_ligne = qte * (prix_prod + prix_tr)
        total_produit += qte * prix_prod
        total_transport += qte * prix_tr

        lines.append({
            "type": "produit",
            "produit_id": pid,
            "nom": produit_nom_map.get(pid, f"Produit {pid}"),
            "qte": qte,
            "prix_unitaire": prix_prod,
            "prix_transport": prix_tr,
            "commentaire": commentaire,
            "total_ligne": total_ligne
        })

    # Lignes robots
    for rid in sorted(robot_counts.keys()):
        qte = robot_counts[rid]
        pr = prix_robot_map.get(rid)
        prix_rob = float(pr.prix_robot) if pr else 0.0
        prix_tr = float(pr.prix_transport) if pr else 0.0
        commentaire = pr.commentaire if pr else None

        total_ligne = qte * (prix_rob + prix_tr)
        total_produit += qte * prix_rob
        total_transport += qte * prix_tr

        lines.append({
            "type": "robot",
            "produit_id": rid,
            "nom": robot_nom_map.get(rid, f"Robot {rid}"),
            "qte": qte,
            "prix_unitaire": prix_rob,
            "prix_transport": prix_tr,
            "commentaire": commentaire,
            "total_ligne": total_ligne
        })

    return {
        "sous_projet_id": id,
        "nom_sous_projet": projet.nom,
        "projet_global": {
            "id": projet_global.id,
            "nom": projet_global.projet,
        } if projet_global else None,
        "client_id": client_id,
        "fpack": {
            "id": fpack.id,
            "nom": fpack.nom,
            "abbr": fpack.fpack_abbr,
            "FPack_number": sp_fpack.FPack_number,
            "Robot_Location_Code": sp_fpack.Robot_Location_Code
        } if fpack else None,
        "currency": "EUR",
        "lines": lines,
        "totaux": {
            "produit": round(total_produit, 2),
            "transport": round(total_transport, 2),
            "global": round(total_produit + total_transport, 2)
        },
        "resume": {
            "nb_lignes": len(lines),
            "nb_produits": len([l for l in lines if l["type"] == "produit"]),
            "nb_robots": len([l for l in lines if l["type"] == "robot"])
        }
    }

@router.get("/fpacks/{fpack_id}/facture")
def get_fpack_facture(fpack_id: int, client_id: int, db: Session = Depends(get_db)):
    """Génère une facture pour un FPack spécifique avec un client donné"""
    
    fpack = db.query(models.FPack).get(fpack_id)
    if not fpack:
        raise HTTPException(status_code=404, detail="FPack non trouvé")
    
    # Vérifier que le client existe
    client = db.query(models.Client).get(client_id)
    if not client:
        raise HTTPException(status_code=400, detail="Client non trouvé")

    # Configuration du FPack
    config_cols = db.query(models.FPackConfigColumn)\
        .filter_by(fpack_id=fpack_id)\
        .order_by(models.FPackConfigColumn.ordre)\
        .all()
    
    if not config_cols:
        return {
            "fpack_id": fpack_id,
            "nom_fpack": fpack.nom,
            "client_id": client_id,
            "client_nom": client.nom,
            "currency": "EUR",
            "lines": [],
            "totaux": {"produit": 0.0, "transport": 0.0, "global": 0.0},
            "resume": {"nb_lignes": 0, "nb_produits": 0, "nb_robots": 0},
            "note": "Configuration FPack vide"
        }

    # Mapping équipements -> produits
    eq_prods = db.query(models.Equipement_Produit).all()
    eq_map = {}
    for ep in eq_prods:
        eq_map.setdefault(ep.equipement_id, []).append((ep.produit_id, ep.quantite))

    # Calcul des quantités (uniquement éléments fixes, pas de sélections)
    produit_counts = defaultdict(int)
    robot_counts = defaultdict(int)
    
    # Pour les groupes, on prend les items "standard" seulement
    for col in config_cols:
        if col.type == "produit":
            produit_counts[col.ref_id] += 1
        elif col.type == "equipement":
            for pid, qte in eq_map.get(col.ref_id, []):
                produit_counts[pid] += qte
        elif col.type == "group":
            # Pour les groupes, prendre uniquement les items marqués comme "standard"
            items_standard = db.query(models.GroupeItem)\
                .filter_by(group_id=col.ref_id, statut="standard")\
                .all()
            
            for item in items_standard:
                if item.type == "produit":
                    produit_counts[item.ref_id] += 1
                elif item.type == "equipement":
                    for pid, qte in eq_map.get(item.ref_id, []):
                        produit_counts[pid] += qte
                elif item.type == "robot":
                    robot_counts[item.ref_id] += 1

    # Récupération des prix et construction de la facture (même logique que sous-projet)
    all_produit_ids = list(produit_counts.keys())
    
    prix_rows = db.query(models.Prix)\
        .filter(
            models.Prix.client_id == client_id,
            models.Prix.produit_id.in_(all_produit_ids)
        ).all() if all_produit_ids else []
    
    prix_map = {p.produit_id: p for p in prix_rows}
    
    prix_robot_rows = db.query(models.PrixRobot)\
        .join(models.Robots, models.Robots.id == models.PrixRobot.id)\
        .filter(
            models.Robots.client == client_id,
            models.PrixRobot.id.in_(robot_counts.keys())
        ).all() if robot_counts else []
    
    prix_robot_map = {p.id: p for p in prix_robot_rows}

    # Noms
    produits_rows = db.query(models.Produit)\
        .filter(models.Produit.id.in_(all_produit_ids))\
        .all() if all_produit_ids else []
    produit_nom_map = {p.id: p.nom for p in produits_rows}

    robot_rows = db.query(models.Robots)\
        .filter(models.Robots.id.in_(robot_counts.keys()))\
        .all() if robot_counts else []
    robot_nom_map = {r.id: r.nom for r in robot_rows}

    # Construction des lignes
    lines = []
    total_produit = 0.00
    total_transport = 0.00

    # Lignes produits
    for pid in sorted(all_produit_ids):
        qte = produit_counts[pid]
        p_rec = prix_map.get(pid)
        prix_prod = float(p_rec.prix_produit) if p_rec else 0.0
        prix_tr = float(p_rec.prix_transport) if p_rec else 0.0
        commentaire = p_rec.commentaire if p_rec else None

        total_ligne = qte * (prix_prod + prix_tr)
        total_produit += qte * prix_prod
        total_transport += qte * prix_tr

        lines.append({
            "type": "produit",
            "produit_id": pid,
            "nom": produit_nom_map.get(pid, f"Produit {pid}"),
            "qte": qte,
            "prix_unitaire": prix_prod,
            "prix_transport": prix_tr,
            "commentaire": commentaire,
            "total_ligne": total_ligne
        })

    # Lignes robots
    for rid in sorted(robot_counts.keys()):
        qte = robot_counts[rid]
        pr = prix_robot_map.get(rid)
        prix_rob = float(pr.prix_robot) if pr else 0.0
        prix_tr = float(pr.prix_transport) if pr else 0.0
        commentaire = pr.commentaire if pr else None

        total_ligne = qte * (prix_rob + prix_tr)
        total_produit += qte * prix_rob
        total_transport += qte * prix_tr

        lines.append({
            "type": "robot",
            "produit_id": rid,
            "nom": robot_nom_map.get(rid, f"Robot {rid}"),
            "qte": qte,
            "prix_unitaire": prix_rob,
            "prix_transport": prix_tr,
            "commentaire": commentaire,
            "total_ligne": total_ligne
        })

    return {
        "fpack_id": fpack_id,
        "nom_fpack": fpack.nom,
        "fpack_abbr": fpack.fpack_abbr,
        "client_id": client_id,
        "client_nom": client.nom,
        "currency": "EUR",
        "lines": lines,
        "totaux": {
            "produit": round(total_produit, 2),
            "transport": round(total_transport, 2),
            "global": round(total_produit + total_transport, 2)
        },
        "resume": {
            "nb_lignes": len(lines),
            "nb_produits": len([l for l in lines if l["type"] == "produit"]),
            "nb_robots": len([l for l in lines if l["type"] == "robot"])
        },
        "note": "Facture basée sur la configuration FPack (items standard uniquement)"
    }