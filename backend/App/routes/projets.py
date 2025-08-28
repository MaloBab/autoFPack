
from fastapi import APIRouter, Depends, HTTPException # type: ignore
from sqlalchemy.orm import Session, joinedload # type: ignore
from sqlalchemy import func # type: ignore
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
        sp_fpacks = db.query(models.SousProjetFpack).filter_by(sous_projet_id=sp.id).all()
        
        if not sp_fpacks:
            sous_projets_incomplets += 1
            continue
        
        sous_projet_complet = True
        
        for sp_fpack in sp_fpacks:
            nb_selections = db.query(models.ProjetSelection).filter_by(
                sous_projet_fpack_id=sp_fpack.id
            ).count()
            
            nb_groupes_attendus = db.query(models.FPackConfigColumn).filter(
                models.FPackConfigColumn.fpack_id == sp_fpack.fpack_id,
                models.FPackConfigColumn.type == "group"
            ).count()
            
            # Vérifier si ce fpack est complet
            if nb_groupes_attendus == 0 or nb_selections < nb_groupes_attendus:
                sous_projet_complet = False
                break
        
        if sous_projet_complet:
            sous_projets_complets += 1
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
        sous_projets_details = []
        for sp in projet.projets:
            sp_fpacks = sp.fpacks
            
            if sp_fpacks:
                fpacks_array = []
                total_selections = 0
                total_groupes_attendus = 0
                
                for sp_fpack in sp_fpacks:
                    fpack_nom = sp_fpack.fpack.nom if sp_fpack.fpack else None
                    nb_selections_fpack = db.query(models.ProjetSelection).filter(
                        models.ProjetSelection.sous_projet_fpack_id == sp_fpack.id
                    ).count()
                    nb_groupes_attendus_fpack = db.query(models.FPackConfigColumn).filter(
                        models.FPackConfigColumn.fpack_id == sp_fpack.fpack_id,
                        models.FPackConfigColumn.type == "group"
                    ).count()

                    total_selections += nb_selections_fpack
                    total_groupes_attendus += nb_groupes_attendus_fpack
                    
                    fpacks_array.append({
                        "id": sp_fpack.id,  
                        "fpack_id": sp_fpack.fpack_id,  
                        "fpack_nom": fpack_nom,
                        "FPack_number": sp_fpack.FPack_number,
                        "Robot_Location_Code": sp_fpack.Robot_Location_Code,
                        "contractor": sp_fpack.contractor,
                        "required_delivery_time": sp_fpack.required_delivery_time,
                        "delivery_site": sp_fpack.delivery_site,
                        "tracking": sp_fpack.tracking,
                        "nb_selections": nb_selections_fpack,
                        "nb_groupes_attendus": nb_groupes_attendus_fpack,
                        "complet": nb_selections_fpack >= nb_groupes_attendus_fpack if nb_groupes_attendus_fpack > 0 else False
                    })
                
                complet = all(fpack["complet"] for fpack in fpacks_array) if fpacks_array else False
                
                sous_projets_details.append({
                    "id": sp.id,
                    "nom": sp.nom,
                    "id_global": sp.id_global,
                    "client_nom": projet.client_rel.nom if projet.client_rel else None,
                    "projet_global_nom": projet.projet,
                    "complet": complet,
                    "nb_selections": total_selections,
                    "nb_groupes_attendus": total_groupes_attendus,
                    "fpacks": fpacks_array,  
                })
            else:
                sous_projets_details.append({
                    "id": sp.id,
                    "nom": sp.nom,
                    "id_global": sp.id_global,
                    "client_nom": projet.client_rel.nom if projet.client_rel else None,
                    "projet_global_nom": projet.projet,
                    "complet": False,
                    "nb_selections": 0,
                    "nb_groupes_attendus": 0,
                    "fpacks": [],
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
    
    sous_projets_details = []
    for sp in projet.projets:
        sp_fpack = db.query(models.SousProjetFpack).filter_by(sous_projet_id=sp.id).first()
        
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
            "client_nom": projet.client_rel.nom if projet.client_rel else None,
            "projet_global_nom": projet.projet,
            "complet": nb_selections >= nb_groupes_attendus if nb_groupes_attendus > 0 else False,
            "nb_selections": nb_selections,
            "nb_groupes_attendus": nb_groupes_attendus,
        })
    
    return {
        "id": projet.id,
        "projet": projet.projet,
        "client": projet.client,
        "sous_projets": sous_projets_details,
        "client_nom": projet.client_rel.nom if projet.client_rel else None
    }

@router.get("/sous_projet_fpack/{sous_projet_fpack_id}")
def get_sous_projet_fpack_by_id(sous_projet_fpack_id: int, db: Session = Depends(get_db)):
    """Récupère une association sous_projet_fpack par son ID"""
    association = db.query(models.SousProjetFpack).get(sous_projet_fpack_id)
    if not association:
        raise HTTPException(status_code=404, detail="Association sous-projet/FPack non trouvée")
    
    sous_projet = db.query(models.SousProjet).get(association.sous_projet_id)
    fpack = db.query(models.FPack).get(association.fpack_id)
    
    return {
        "id": association.id,
        "sous_projet_id": association.sous_projet_id,
        "fpack_id": association.fpack_id,
        "FPack_number": association.FPack_number,
        "Robot_Location_Code": association.Robot_Location_Code,
        "contractor": association.contractor,
        "required_delivery_time": association.required_delivery_time,
        "delivery_site": association.delivery_site,
        "tracking": association.tracking,
        "sous_projet": {
            "id": sous_projet.id,
            "nom": sous_projet.nom,
            "id_global": sous_projet.id_global
        } if sous_projet else None,
        "fpack": {
            "id": fpack.id,
            "nom": fpack.nom,
            "fpack_abbr": fpack.fpack_abbr
        } if fpack else None
    }



@router.post("/projets_globaux", response_model=schemas.ProjetGlobalRead)
def create_projet_global(projet: schemas.ProjetGlobalCreate, db: Session = Depends(get_db)):
    """Crée un nouveau projet global"""
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
    """Supprime un projet global et tous ses sous-projets en cascade (optimisé)"""
    db_projet = db.query(models.ProjetGlobal).get(id)
    if not db_projet:
        raise HTTPException(status_code=404, detail="Projet global non trouvé")
    
    sous_projets_ids = db.query(models.SousProjet.id).filter(
        models.SousProjet.id_global == id
    ).all()
    sous_projets_ids = [sp_id[0] for sp_id in sous_projets_ids]
    
    if not sous_projets_ids:
        db.delete(db_projet)
        db.commit()
        return {"ok": True, "message": "Projet global supprimé (aucun sous-projet)"}
    
    associations_ids = db.query(models.SousProjetFpack.id).filter(
        models.SousProjetFpack.sous_projet_id.in_(sous_projets_ids)
    ).all()
    associations_ids = [assoc_id[0] for assoc_id in associations_ids]
    
    stats = {
        "nb_sous_projets": len(sous_projets_ids),
        "nb_fpacks": len(associations_ids),
        "nb_selections": 0
    }
    
    if associations_ids:
        stats["nb_selections"] = db.query(models.ProjetSelection).filter(
            models.ProjetSelection.sous_projet_fpack_id.in_(associations_ids)
        ).count()
        
        db.query(models.ProjetSelection).filter(
            models.ProjetSelection.sous_projet_fpack_id.in_(associations_ids)
        ).delete(synchronize_session=False)
        
        db.query(models.SousProjetFpack).filter(
            models.SousProjetFpack.id.in_(associations_ids)
        ).delete(synchronize_session=False)

    db.query(models.SousProjet).filter(
        models.SousProjet.id.in_(sous_projets_ids)
    ).delete(synchronize_session=False)

    db.delete(db_projet)
    db.commit()
    
    return {
        "ok": True, 
        "message": f"Projet global supprimé avec {stats['nb_sous_projets']} sous-projet(s), {stats['nb_fpacks']} FPack(s) et {stats['nb_selections']} sélection(s)"
    }


def delete_sous_projet_cascade_bulk(sous_projet_id: int, db: Session):
    """Fonction utilitaire pour supprimer un sous-projet en cascade (optimisée)"""
    associations_ids = db.query(models.SousProjetFpack.id).filter(
        models.SousProjetFpack.sous_projet_id == sous_projet_id
    ).all()
    associations_ids = [assoc_id[0] for assoc_id in associations_ids]
    
    stats = {
        "nb_fpacks_supprimes": len(associations_ids),
        "nb_selections_supprimees": 0
    }
    
    if associations_ids:
        stats["nb_selections_supprimees"] = db.query(models.ProjetSelection).filter(
            models.ProjetSelection.sous_projet_fpack_id.in_(associations_ids)
        ).count()
        
        db.query(models.ProjetSelection).filter(
            models.ProjetSelection.sous_projet_fpack_id.in_(associations_ids)
        ).delete(synchronize_session=False)
        
        db.query(models.SousProjetFpack).filter(
            models.SousProjetFpack.id.in_(associations_ids)
        ).delete(synchronize_session=False)
    
    db.query(models.SousProjet).filter(
        models.SousProjet.id == sous_projet_id
    ).delete(synchronize_session=False)
    
    return stats


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
            "client_nom": client.nom if client else None,
            "projet_global_nom": projet_global.projet if projet_global else None,
            "complet": nb_selections >= nb_groupes_attendus if nb_groupes_attendus > 0 else False,
            "nb_selections": nb_selections,
            "nb_groupes_attendus": nb_groupes_attendus,
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
        "client_nom": client.nom if client else None,
        "projet_global_nom": projet_global.projet if projet_global else None,
        "complet": nb_selections >= nb_groupes_attendus if nb_groupes_attendus > 0 else False,
        "nb_selections": nb_selections,
        "nb_groupes_attendus": nb_groupes_attendus,
    }

@router.post("/sous_projets", response_model=schemas.SousProjetRead)
def create_sous_projet(sous_projet: schemas.SousProjetCreate, db: Session = Depends(get_db)):
    """Crée un nouveau sous-projet"""
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
    """Supprime un sous-projet et toutes ses associations FPack/sélections en cascade (optimisé)"""
    db_sous_projet = db.query(models.SousProjet).get(id)
    if not db_sous_projet:
        raise HTTPException(status_code=404, detail="Sous-projet non trouvé")
    
    stats = delete_sous_projet_cascade_bulk(id, db)
    
    db.commit()
    
    return {
        "ok": True,
        "message": f"Sous-projet supprimé avec {stats['nb_fpacks_supprimes']} FPack(s) et {stats['nb_selections_supprimees']} sélection(s)"
    }

# ========== FPACKS ASSOCIÉS AUX SOUS-PROJETS ==========

@router.get("/sous_projets/{sous_projet_id}/fpacks", response_model=List[schemas.SousProjetFpackRead])
def list_fpacks_by_sous_projet(sous_projet_id: int, db: Session = Depends(get_db)):
    """Liste tous les FPacks associés à un sous-projet"""
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
    sous_projet = db.query(models.SousProjet).get(sous_projet_id)
    if not sous_projet:
        raise HTTPException(status_code=404, detail="Sous-projet non trouvé")

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
    """Retire un FPack d'un sous-projet et supprime toutes ses sélections en cascade (optimisé)"""
    association = db.query(models.SousProjetFpack).filter_by(
        sous_projet_id=sous_projet_id,
        fpack_id=fpack_id
    ).first()
    
    if not association:
        raise HTTPException(status_code=404, detail="Association FPack/sous-projet non trouvée")
    
    nb_selections = db.query(models.ProjetSelection).filter(
        models.ProjetSelection.sous_projet_fpack_id == association.id
    ).count()

    db.query(models.ProjetSelection).filter(
        models.ProjetSelection.sous_projet_fpack_id == association.id
    ).delete(synchronize_session=False)
    
    db.delete(association)
    db.commit()
    
    return {
        "ok": True,
        "message": f"Association FPack supprimée avec {nb_selections} sélection(s)"
    }

# ========== SÉLECTIONS ==========

@router.get("/sous_projets/{sous_projet_id}/fpacks/{fpack_id}/selections", response_model=List[schemas.ProjetSelectionReadWithDetails])
def get_selections_by_fpack(sous_projet_id: int, fpack_id: int, db: Session = Depends(get_db)):
    """Récupère toutes les sélections pour un FPack d'un sous-projet"""
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
        groupe = db.query(models.Groupes).get(sel.groupe_id)
        groupe_nom = groupe.nom if groupe else None
        
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
    association = db.query(models.SousProjetFpack).filter_by(
        sous_projet_id=sous_projet_id,
        fpack_id=fpack_id
    ).first()
    
    if not association:
        raise HTTPException(status_code=404, detail="Association FPack/sous-projet non trouvée")

    groupe = db.query(models.Groupes).get(selection.groupe_id)
    if not groupe:
        raise HTTPException(status_code=400, detail="Groupe non trouvé")

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
        if key != "sous_projet_fpack_id": 
            setattr(selection, key, value)
    
    db.commit()
    db.refresh(selection)
    return selection

@router.delete("/sous_projets/{sous_projet_id}/fpacks/{fpack_id}/selections/{groupe_id}")
def delete_selection(sous_projet_id: int, fpack_id: int, groupe_id: int, db: Session = Depends(get_db)):
    """Supprime une sélection"""
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


@router.get("/sous_projet_fpack/{sous_projet_fpack_id}/selections", response_model=List[schemas.ProjetSelectionReadWithDetails])
def get_selections_by_sous_projet_fpack_id(sous_projet_fpack_id: int, db: Session = Depends(get_db)):
    """Récupère toutes les sélections pour une association sous_projet_fpack par son ID"""
    association = db.query(models.SousProjetFpack).get(sous_projet_fpack_id)
    if not association:
        raise HTTPException(status_code=404, detail="Association sous-projet/FPack non trouvée")
    
    selections = db.query(models.ProjetSelection).filter_by(
        sous_projet_fpack_id=sous_projet_fpack_id
    ).all()
    
    result = []
    for sel in selections:
        groupe = db.query(models.Groupes).get(sel.groupe_id)
        groupe_nom = groupe.nom if groupe else None
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

@router.post("/sous_projet_fpack/{sous_projet_fpack_id}/selections", response_model=schemas.ProjetSelectionRead)
def create_selection_by_sous_projet_fpack_id(
    sous_projet_fpack_id: int,
    selection: schemas.ProjetSelectionCreate,
    db: Session = Depends(get_db)
):
    """Crée une nouvelle sélection pour une association sous_projet_fpack"""
    association = db.query(models.SousProjetFpack).get(sous_projet_fpack_id)
    if not association:
        raise HTTPException(status_code=404, detail="Association sous-projet/FPack non trouvée")
    
    groupe = db.query(models.Groupes).get(selection.groupe_id)
    if not groupe:
        raise HTTPException(status_code=400, detail="Groupe non trouvé")
    
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
    
    existing = db.query(models.ProjetSelection).filter_by(
        sous_projet_fpack_id=sous_projet_fpack_id,
        groupe_id=selection.groupe_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Une sélection existe déjà pour ce groupe")
    
    db_selection = models.ProjetSelection(
        sous_projet_fpack_id=sous_projet_fpack_id,
        **selection.dict()
    )
    db.add(db_selection)
    db.commit()
    db.refresh(db_selection)
    return db_selection


@router.put("/sous_projet_fpack/{sous_projet_fpack_id}/selections/{groupe_id}", response_model=schemas.ProjetSelectionRead)
def update_selection_by_sous_projet_fpack_id(
    sous_projet_fpack_id: int,
    groupe_id: int,
    selection_data: schemas.ProjetSelectionCreate,
    db: Session = Depends(get_db)
):
    """Met à jour une sélection pour une association sous_projet_fpack"""
    association = db.query(models.SousProjetFpack).get(sous_projet_fpack_id)
    if not association:
        raise HTTPException(status_code=404, detail="Association sous-projet/FPack non trouvée")
    
    selection = db.query(models.ProjetSelection).filter_by(
        sous_projet_fpack_id=sous_projet_fpack_id,
        groupe_id=groupe_id
    ).first()
    
    if not selection:
        raise HTTPException(status_code=404, detail="Sélection non trouvée")
    
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
        if key != "sous_projet_fpack_id":
            setattr(selection, key, value)
    
    db.commit()
    db.refresh(selection)
    return selection


@router.delete("/sous_projet_fpack/{sous_projet_fpack_id}/selections/{groupe_id}")
def delete_selection_by_sous_projet_fpack_id(sous_projet_fpack_id: int, groupe_id: int, db: Session = Depends(get_db)):
    """Supprime une sélection pour une association sous_projet_fpack"""
    association = db.query(models.SousProjetFpack).get(sous_projet_fpack_id)
    if not association:
        raise HTTPException(status_code=404, detail="Association sous-projet/FPack non trouvée")
    
    selection = db.query(models.ProjetSelection).filter_by(
        sous_projet_fpack_id=sous_projet_fpack_id,
        groupe_id=groupe_id
    ).first()
    
    if not selection:
        raise HTTPException(status_code=404, detail="Sélection non trouvée")
    
    db.delete(selection)
    db.commit()
    return {"ok": True}

@router.delete("/sous_projet_fpack/{fpack_association_id}")
def remove_fpack_association(fpack_association_id: int, db: Session = Depends(get_db)):
    """Supprime une association sous-projet/FPack par son ID et toutes ses sélections en cascade (optimisé)"""
    association = db.query(models.SousProjetFpack).get(fpack_association_id)
    
    if not association:
        raise HTTPException(status_code=404, detail="Association FPack/sous-projet non trouvée")
    
    nb_selections = db.query(models.ProjetSelection).filter(
        models.ProjetSelection.sous_projet_fpack_id == fpack_association_id
    ).count()
    
    db.query(models.ProjetSelection).filter(
        models.ProjetSelection.sous_projet_fpack_id == fpack_association_id
    ).delete(synchronize_session=False)
    
    db.delete(association)
    db.commit()
    
    return {
        "ok": True,
        "message": f"Association FPack supprimée avec {nb_selections} sélection(s)"
    }


def delete_fpack_association_cascade_bulk(association_id: int, db: Session):
    """Supprime toutes les sélections d'une association FPack puis l'association (optimisé)"""
    nb_selections = db.query(models.ProjetSelection).filter(
        models.ProjetSelection.sous_projet_fpack_id == association_id
    ).count()
    
    db.query(models.ProjetSelection).filter(
        models.ProjetSelection.sous_projet_fpack_id == association_id
    ).delete(synchronize_session=False)
    
    db.query(models.SousProjetFpack).filter(
        models.SousProjetFpack.id == association_id
    ).delete(synchronize_session=False)
    
    return nb_selections

@router.get("/sous_projet_fpack/{sous_projet_fpack_id}/facture")
def get_sous_projet_fpack_facture(sous_projet_fpack_id: int, db: Session = Depends(get_db)):
    """Génère la facture d'une association sous_projet_fpack spécifique"""
    
    sp_fpack = db.query(models.SousProjetFpack).get(sous_projet_fpack_id)
    if not sp_fpack:
        raise HTTPException(status_code=404, detail="Association sous-projet/FPack non trouvée")
    
    sous_projet = db.query(models.SousProjet).get(sp_fpack.sous_projet_id)
    if not sous_projet:
        raise HTTPException(status_code=404, detail="Sous-projet non trouvé")
    
    projet_global = db.query(models.ProjetGlobal).get(sous_projet.id_global)
    client_id = projet_global.client if projet_global else None
    
    if not client_id:
        raise HTTPException(status_code=400, detail="Client non trouvé pour ce projet")
    
    fpack = db.query(models.FPack).get(sp_fpack.fpack_id)
    
    config_cols = db.query(models.FPackConfigColumn)\
        .filter_by(fpack_id=sp_fpack.fpack_id)\
        .order_by(models.FPackConfigColumn.ordre)\
        .all()
    
    sels = db.query(models.ProjetSelection).filter_by(sous_projet_fpack_id=sous_projet_fpack_id).all()
    sel_map = {s.groupe_id: {"type": s.type_item, "ref_id": s.ref_id} for s in sels}

    eq_prods = db.query(models.Equipement_Produit).all()
    eq_map = {}
    for ep in eq_prods:
        eq_map.setdefault(ep.equipement_id, []).append((ep.produit_id, ep.quantite))

    produit_counts = defaultdict(int)
    robot_counts = defaultdict(int)

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

    all_produit_ids = list(produit_counts.keys())
    
    prix_rows = db.query(models.Prix)\
        .filter(
            models.Prix.client_id == client_id,
            models.Prix.produit_id.in_(all_produit_ids)
        ).all() if all_produit_ids else []
    
    prix_map = {p.produit_id: p for p in prix_rows}
    
    prix_robot_rows = db.query(models.PrixRobot)\
        .join(models.Robots, models.Robots.id == models.PrixRobot.id).filter(
            models.Robots.client == client_id,
            models.PrixRobot.id.in_(robot_counts.keys())
        ).all() if robot_counts else []
    
    prix_robot_map = {p.id: p for p in prix_robot_rows}

    produits_rows = db.query(models.Produit).filter(models.Produit.id.in_(all_produit_ids)).all() if all_produit_ids else []
    produit_nom_map = {p.id: p.nom for p in produits_rows}

    robot_rows = db.query(models.Robots).filter(models.Robots.id.in_(robot_counts.keys())).all() if robot_counts else []
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
        "sous_projet_fpack_id": sous_projet_fpack_id,
        "sous_projet_id": sous_projet.id,
        "nom_sous_projet": sous_projet.nom,
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
            "Robot_Location_Code": sp_fpack.Robot_Location_Code,
            "contractor": sp_fpack.contractor,
            "required_delivery_time": sp_fpack.required_delivery_time,
            "delivery_site": sp_fpack.delivery_site,
            "tracking": sp_fpack.tracking
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