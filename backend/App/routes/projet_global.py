# backend/App/routes/projet_global.py - Version optimisée

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from App.database import SessionLocal
from App import models, schemas
from typing import Dict, Any, List

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ProjetService:
    """Service pour centraliser la logique métier des projets"""
    
    @staticmethod
    def get_clients_map(db: Session) -> Dict[int, str]:
        return {c.id: c.nom for c in db.query(models.Client).all()}
    
    @staticmethod
    def get_fpacks_map(db: Session) -> Dict[int, Any]:
        return {f.id: f for f in db.query(models.FPack).all()}
    
    @staticmethod
    def calculate_projet_stats(db: Session, projet: models.Projet, fpacks_map: Dict) -> Dict:
        """Calcule les statistiques d'un projet"""
        nb_selections = db.query(models.ProjetSelection)\
            .filter_by(projet_id=projet.id).count()
        
        nb_groupes_attendus = db.query(models.FPackConfigColumn)\
            .filter_by(fpack_id=projet.fpack_id, type='group').count()
        
        fpack = fpacks_map.get(projet.fpack_id)
        
        return {
            "id": projet.id,
            "nom": projet.nom,
            "fpack_id": projet.fpack_id,
            "id_global": projet.id_global,
            "fpack_nom": fpack.nom if fpack else None,
            "client_nom": None,  # Sera rempli par l'appelant
            "complet": nb_selections >= nb_groupes_attendus if nb_groupes_attendus > 0 else False,
            "nb_selections": nb_selections,
            "nb_groupes_attendus": nb_groupes_attendus,
            "progression_percent": round((nb_selections / nb_groupes_attendus) * 100, 1) if nb_groupes_attendus > 0 else 0
        }
    
    @staticmethod
    def enrich_projets_with_client_info(projets_details: List[Dict], fpacks_map: Dict, clients_map: Dict) -> List[Dict]:
        """Enrichit les projets avec les informations client"""
        for projet in projets_details:
            fpack = fpacks_map.get(projet["fpack_id"])
            if fpack:
                projet["client_nom"] = clients_map.get(fpack.client)
        return projets_details

@router.get("/projets-global", response_model=list[schemas.ProjetGlobalReadWithProjets])
def list_projets_global(db: Session = Depends(get_db)):
    """Liste tous les projets globaux avec leurs projets enrichis"""
    projets_global = db.query(models.ProjetGlobal).all()
    clients_map = ProjetService.get_clients_map(db)
    fpacks_map = ProjetService.get_fpacks_map(db)
    
    result = []
    for pg in projets_global:
        projets = db.query(models.Projet).filter_by(id_global=pg.id).all()
        projets_details = [
            ProjetService.calculate_projet_stats(db, projet, fpacks_map) 
            for projet in projets
        ]
        
        ProjetService.enrich_projets_with_client_info(projets_details, fpacks_map, clients_map)
        
        result.append({
            "id": pg.id,
            "projet": pg.projet,
            "sous_projet": pg.sous_projet,
            "client": pg.client,
            "client_nom": clients_map.get(pg.client),
            "projets": projets_details,
            "stats": ProjetService.calculate_global_stats(projets_details)
        })
    
    return result

@router.get("/projets-global/{id}", response_model=schemas.ProjetGlobalReadWithProjets)
def get_projet_global(id: int, db: Session = Depends(get_db)):
    """Récupère un projet global avec ses projets"""
    projet_global = db.query(models.ProjetGlobal).get(id)
    if not projet_global:
        raise HTTPException(status_code=404, detail="Projet global non trouvé")
    
    clients_map = ProjetService.get_clients_map(db)
    fpacks_map = ProjetService.get_fpacks_map(db)
    
    projets = db.query(models.Projet).filter_by(id_global=id).all()
    projets_details = [
        ProjetService.calculate_projet_stats(db, projet, fpacks_map) 
        for projet in projets
    ]
    
    ProjetService.enrich_projets_with_client_info(projets_details, fpacks_map, clients_map)
    
    return {
        "id": projet_global.id,
        "projet": projet_global.projet,
        "sous_projet": projet_global.sous_projet,
        "client": projet_global.client,
        "client_nom": clients_map.get(projet_global.client),
        "projets": projets_details,
        "stats": ProjetService.calculate_global_stats(projets_details)
    }

@router.post("/projets-global", response_model=schemas.ProjetGlobalRead)
def create_projet_global(data: schemas.ProjetGlobalCreate, db: Session = Depends(get_db)):
    """Crée un nouveau projet global"""
    client = db.query(models.Client).get(data.client)
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    projet = models.ProjetGlobal(**data.dict())
    db.add(projet)
    db.commit()
    db.refresh(projet)
    return projet

@router.put("/projets-global/{id}", response_model=schemas.ProjetGlobalRead)
def update_projet_global(id: int, data: schemas.ProjetGlobalCreate, db: Session = Depends(get_db)):
    """Met à jour un projet global avec validation"""
    projet = db.query(models.ProjetGlobal).get(id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet global non trouvé")

    if data.client != projet.client:
        client = db.query(models.Client).get(data.client)
        if not client:
            raise HTTPException(status_code=404, detail="Client non trouvé")
        
        # Validation des projets associés
        projets_associes = db.query(models.Projet).filter_by(id_global=id).all()
        conflicted_projets = []
        
        for p in projets_associes:
            fpack = db.query(models.FPack).get(p.fpack_id)
            if fpack and fpack.client != data.client:
                conflicted_projets.append(p.nom)
        
        if conflicted_projets:
            raise HTTPException(
                status_code=400,
                detail=f"Impossible de changer le client : les projets suivants utilisent des FPacks d'autres clients : {', '.join(conflicted_projets)}"
            )

    for key, value in data.dict().items():
        setattr(projet, key, value)

    db.commit()
    db.refresh(projet)
    return projet

@router.delete("/projets-global/{id}")
def delete_projet_global(id: int, db: Session = Depends(get_db)):
    """Supprime un projet global après vérifications"""
    projet = db.query(models.ProjetGlobal).get(id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet global non trouvé")

    projets_associes = db.query(models.Projet).filter_by(id_global=id).all()
    if projets_associes:
        noms = [p.nom for p in projets_associes]
        raise HTTPException(
            status_code=400,
            detail=f"Suppression impossible : ce projet global contient {len(projets_associes)} projet(s) : {', '.join(noms)}"
        )

    db.delete(projet)
    db.commit()
    return {"ok": True, "message": "Projet global supprimé avec succès"}

@router.get("/projets-global/{id}/stats")
def get_projet_global_stats(id: int, db: Session = Depends(get_db)):
    """Statistiques détaillées d'un projet global"""
    projet_global = db.query(models.ProjetGlobal).get(id)
    if not projet_global:
        raise HTTPException(status_code=404, detail="Projet global non trouvé")
    
    projets = db.query(models.Projet).filter_by(id_global=id).all()
    fpacks_map = ProjetService.get_fpacks_map(db)
    
    projets_details = [
        ProjetService.calculate_projet_stats(db, projet, fpacks_map) 
        for projet in projets
    ]
    
    return ProjetService.calculate_global_stats(projets_details)

# Extension du service avec méthodes statiques
@staticmethod
def calculate_global_stats(projets_details: List[Dict]) -> Dict:
    """Calcule les statistiques globales"""
    if not projets_details:
        return {
            "nb_projets": 0,
            "nb_projets_complets": 0,
            "nb_projets_en_cours": 0,
            "progression_globale": 0,
            "total_groupes": 0,
            "total_selections": 0
        }
    
    nb_projets = len(projets_details)
    nb_complets = sum(1 for p in projets_details if p["complet"])
    total_groupes = sum(p["nb_groupes_attendus"] for p in projets_details)
    total_selections = sum(p["nb_selections"] for p in projets_details)
    
    return {
        "nb_projets": nb_projets,
        "nb_projets_complets": nb_complets,
        "nb_projets_en_cours": nb_projets - nb_complets,
        "progression_globale": round((total_selections / total_groupes) * 100, 1) if total_groupes > 0 else 0,
        "total_groupes": total_groupes,
        "total_selections": total_selections
    }

ProjetService.calculate_global_stats = calculate_global_stats