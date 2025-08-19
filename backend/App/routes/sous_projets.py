from fastapi import APIRouter, Depends, HTTPException, Body # type: ignore
from sqlalchemy.orm import Session, joinedload # type: ignore
from sqlalchemy import func # type: ignore
from App.database import SessionLocal
from App import models, schemas
from typing import Dict, List

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ProjetDetailService:
    """Service pour la gestion détaillée des projets"""
    
    @staticmethod
    def get_enriched_selections(db: Session, projet_id: int) -> List[Dict]:
        """Récupère les sélections enrichies d'un projet"""
        selections = db.query(models.ProjetSelection).filter_by(projet_id=projet_id).all()
        
        enriched = []
        for sel in selections:
            groupe = db.query(models.Groupes).get(sel.groupe_id)
            item_nom = ProjetDetailService._get_item_name(db, sel.type_item, sel.ref_id)
            
            enriched.append({
                "projet_id": sel.projet_id,
                "fpack_id": sel.fpack_id,  # Ajout du fpack_id manquant
                "groupe_id": sel.groupe_id,
                "type_item": sel.type_item,
                "ref_id": sel.ref_id,
                "groupe_nom": groupe.nom if groupe else f"Groupe {sel.groupe_id}",
                "item_nom": item_nom
            })
        
        return enriched
    
    @staticmethod
    def _get_item_name(db: Session, type_item: str, ref_id: int) -> str:
        """Récupère le nom d'un item selon son type"""
        item_maps = {
            "produit": (models.Produit, "Produit"),
            "equipement": (models.Equipements, "Équipement"),
            "robot": (models.Robots, "Robot")
        }
        
        if type_item not in item_maps:
            return f"Item {ref_id}"
        
        model_class, prefix = item_maps[type_item]
        item = db.query(model_class).get(ref_id)
        return item.nom if item else f"{prefix} {ref_id}"

@router.get("/sous_projets/tree", response_model=schemas.ProjetTree)
def get_projets_tree(db: Session = Depends(get_db)):
    """Arbre complet optimisé des projets par projet global"""
    projets_global = db.query(models.ProjetGlobal)\
        .options(joinedload(models.ProjetGlobal.projets))\
        .all()
    
    clients_map = {c.id: c.nom for c in db.query(models.Client).all()}
    fpacks_map = {f.id: f for f in db.query(models.FPack).all()}
    
    # Récupérer les relations SousProjetFpack pour avoir les détails FPack
    sous_projet_fpack_map = {}
    for sp_fp in db.query(models.SousProjetFpack).all():
        sous_projet_fpack_map[sp_fp.sous_projet_id] = sp_fp
    
    selections_stats = db.query(
        models.ProjetSelection.projet_id,
        func.count(models.ProjetSelection.groupe_id).label('nb_selections')
    ).group_by(models.ProjetSelection.projet_id).all()
    
    selections_map = {stat.projet_id: stat.nb_selections for stat in selections_stats}
    
    config_stats = db.query(
        models.FPackConfigColumn.fpack_id,
        func.count(models.FPackConfigColumn.ref_id).label('nb_groupes')
    ).filter(models.FPackConfigColumn.type == 'group')\
     .group_by(models.FPackConfigColumn.fpack_id).all()
    
    config_map = {stat.fpack_id: stat.nb_groupes for stat in config_stats}
    
    result = []
    for pg in projets_global:
        projets_details = []
        for projet in pg.projets:
            # Récupérer les détails FPack depuis la table de liaison
            sp_fpack = sous_projet_fpack_map.get(projet.id)
            fpack_id = sp_fpack.fpack_id if sp_fpack else None
            fpack = fpacks_map.get(fpack_id) if fpack_id else None
            
            nb_selections = selections_map.get(projet.id, 0)
            nb_groupes_attendus = config_map.get(fpack_id, 0) if fpack_id else 0
            
            projets_details.append({
                "id": projet.id,
                "nom": projet.nom,
                "id_global": projet.id_global,
                "fpack_nom": fpack.nom if fpack else None,
                "client_nom": clients_map.get(fpack.client) if fpack else None,
                "projet_global_nom": pg.projet,
                "sous_projet_nom": projet.nom,
                "complet": nb_selections >= nb_groupes_attendus if nb_groupes_attendus > 0 else False,
                "nb_selections": nb_selections,
                "nb_groupes_attendus": nb_groupes_attendus,
                # Ajout des détails FPack manquants dans le schéma
                "FPack_number": sp_fpack.FPack_number if sp_fpack else None,
                "Robot_Location_Code": sp_fpack.Robot_Location_Code if sp_fpack else None
            })
        
        result.append({
            "id": pg.id,
            "projet": pg.projet,
            "client": pg.client,
            "client_nom": clients_map.get(pg.client),
            "sous_projets": projets_details
        })
    
    return {"projets_global": result}

@router.get("/projets-global/{global_id}/sous_projets", response_model=list[schemas.SousProjetReadWithDetails])
def get_projets_by_global(global_id: int, db: Session = Depends(get_db)):
    """Projets d'un projet global avec validation"""
    # Vérifier que le projet global existe
    projet_global = db.query(models.ProjetGlobal).get(global_id)
    if not projet_global:
        raise HTTPException(status_code=404, detail="Projet global non trouvé")
    
    projets = db.query(models.SousProjet).filter_by(id_global=global_id).all()
    
    clients_map = {c.id: c.nom for c in db.query(models.Client).all()}
    fpacks_map = {f.id: f for f in db.query(models.FPack).all()}
    
    # Récupérer les relations SousProjetFpack
    sous_projet_fpack_map = {}
    for sp_fp in db.query(models.SousProjetFpack).filter(
        models.SousProjetFpack.sous_projet_id.in_([p.id for p in projets])
    ).all():
        sous_projet_fpack_map[sp_fp.sous_projet_id] = sp_fp
    
    result = []
    for projet in projets:
        nb_selections = db.query(models.ProjetSelection)\
            .filter_by(projet_id=projet.id).count()
        
        # Utiliser l'ID du FPack depuis la table de liaison
        sp_fpack = sous_projet_fpack_map.get(projet.id)
        fpack_id = sp_fpack.fpack_id if sp_fpack else None
        fpack = fpacks_map.get(fpack_id) if fpack_id else None
        
        nb_groupes_attendus = db.query(models.FPackConfigColumn)\
            .filter_by(fpack_id=fpack_id, type='group').count() if fpack_id else 0
        
        client_nom = clients_map.get(fpack.client) if fpack else None
        
        result.append({
            "id": projet.id,
            "nom": projet.nom,
            "id_global": projet.id_global,
            "fpack_nom": fpack.nom if fpack else None,
            "client_nom": client_nom,
            "projet_global_nom": projet_global.projet,
            "sous_projet_nom": projet.nom,
            "complet": nb_selections >= nb_groupes_attendus if nb_groupes_attendus > 0 else False,
            "nb_selections": nb_selections,
            "nb_groupes_attendus": nb_groupes_attendus,
            "FPack_number": sp_fpack.FPack_number if sp_fpack else None,
            "Robot_Location_Code": sp_fpack.Robot_Location_Code if sp_fpack else None
        })
    
    return result

@router.post("/sous_projets", response_model=schemas.SousProjetRead)
def create_projet(projet: schemas.SousProjetCreate, db: Session = Depends(get_db)):
    """Crée un projet avec validations complètes"""
    projet_global = db.query(models.ProjetGlobal).get(projet.id_global)
    if not projet_global:
        raise HTTPException(status_code=404, detail="Projet global non trouvé")
    
    # Vérifier l'unicité du nom dans le projet global
    existing = db.query(models.SousProjet)\
        .filter_by(id_global=projet.id_global, nom=projet.nom)\
        .first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Un projet avec ce nom existe déjà dans ce projet global"
        )
    
    db_projet = models.SousProjet(**projet.dict())
    db.add(db_projet)
    db.commit()
    db.refresh(db_projet)
    return db_projet

@router.post("/sous_projets/{projet_id}/fpack", response_model=schemas.SousProjetFpackRead)
def associate_fpack_to_projet(
    projet_id: int, 
    fpack_data: schemas.SousProjetFpackCreate, 
    db: Session = Depends(get_db)
):
    """Associe un FPack à un sous-projet"""
    # Vérifier que le sous-projet existe
    sous_projet = db.query(models.SousProjet).get(projet_id)
    if not sous_projet:
        raise HTTPException(status_code=404, detail="Sous-projet non trouvé")
    
    # Vérifier que le FPack existe
    fpack = db.query(models.FPack).get(fpack_data.fpack_id)
    if not fpack:
        raise HTTPException(status_code=404, detail="FPack non trouvé")
    
    # Vérifier la cohérence client
    projet_global = db.query(models.ProjetGlobal).get(sous_projet.id_global)
    if projet_global and fpack.client != projet_global.client:
        raise HTTPException(
            status_code=400,
            detail="Le client du FPack doit correspondre au client du projet global"
        )
    
    # Vérifier si une association existe déjà
    existing = db.query(models.SousProjetFpack)\
        .filter_by(sous_projet_id=projet_id)\
        .first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Ce sous-projet est déjà associé à un FPack"
        )
    
    # Créer l'association
    db_association = models.SousProjetFpack(
        sous_projet_id=projet_id,
        **fpack_data.dict()
    )
    db.add(db_association)
    db.commit()
    db.refresh(db_association)
    return db_association

@router.delete("/sous_projets/{id}")
def delete_projet(id: int, db: Session = Depends(get_db)):
    """Supprime un projet avec nettoyage des sélections et associations"""
    projet = db.query(models.SousProjet).get(id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Compter les sélections pour information
    nb_selections = db.query(models.ProjetSelection)\
        .filter_by(projet_id=id).count()
    
    # Supprimer les sélections associées
    db.query(models.ProjetSelection)\
        .filter_by(projet_id=id)\
        .delete()
    
    # Supprimer l'association FPack si elle existe
    db.query(models.SousProjetFpack)\
        .filter_by(sous_projet_id=id)\
        .delete()
    
    # Supprimer le projet
    db.delete(projet)
    db.commit()
    
    return {
        "ok": True,
        "message": f"Projet '{projet.nom}' supprimé avec succès",
        "selections_supprimees": nb_selections
    }

@router.get("/sous_projets/{id}/details")
def get_projet_details(id: int, db: Session = Depends(get_db)):
    """Détails complets optimisés d'un projet"""
    projet = db.query(models.SousProjet).get(id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Chargement des entités liées
    projet_global = db.query(models.ProjetGlobal).get(projet.id_global)
    client = db.query(models.Client).get(projet_global.client) if projet_global else None
    
    # Récupérer l'association FPack
    sp_fpack = db.query(models.SousProjetFpack)\
        .filter_by(sous_projet_id=id)\
        .first()
    
    fpack = db.query(models.FPack).get(sp_fpack.fpack_id) if sp_fpack else None
    
    # Configuration et sélections
    config_columns = []
    nb_groupes_config = 0
    if fpack:
        config_columns = db.query(models.FPackConfigColumn)\
            .filter_by(fpack_id=fpack.id)\
            .order_by(models.FPackConfigColumn.ordre)\
            .all()
        nb_groupes_config = len([c for c in config_columns if c.type == 'group'])
    
    selections_enriched = ProjetDetailService.get_enriched_selections(db, id)
    
    return {
        "projet": {
            "id": projet.id,
            "nom": projet.nom,
            "id_global": projet.id_global
        },
        "projet_global": {
            "id": projet_global.id,
            "projet": projet_global.projet,
            "client": projet_global.client
        } if projet_global else None,
        "fpack": {
            "id": fpack.id,
            "nom": fpack.nom,
            "fpack_abbr": fpack.fpack_abbr,
            "client": fpack.client
        } if fpack else None,
        "fpack_association": {
            "FPack_number": sp_fpack.FPack_number,
            "Robot_Location_Code": sp_fpack.Robot_Location_Code
        } if sp_fpack else None,
        "client": {
            "id": client.id,
            "nom": client.nom
        } if client else None,
        "config_columns": nb_groupes_config,
        "selections": selections_enriched,
        "complet": len(selections_enriched) >= nb_groupes_config,
        "progression_percent": round((len(selections_enriched) / nb_groupes_config) * 100, 1) if nb_groupes_config > 0 else 0
    }

@router.get("/sous_projets", response_model=list[schemas.SousProjetReadExtended])
def list_projets(db: Session = Depends(get_db)):
    """Liste tous les projets avec stats optimisées"""
    projets = db.query(models.SousProjet).all()
    
    # Récupérer les associations FPack
    fpack_associations = db.query(models.SousProjetFpack).all()
    fpack_map = {assoc.sous_projet_id: assoc.fpack_id for assoc in fpack_associations}
    
    # Optimisation : une seule requête pour toutes les sélections
    selections_stats = db.query(
        models.ProjetSelection.projet_id,
        func.count().label('nb_selections')
    ).group_by(models.ProjetSelection.projet_id).all()
    
    selections_map = {stat.projet_id: stat.nb_selections for stat in selections_stats}
    
    # Une seule requête pour tous les groupes attendus
    config_stats = db.query(
        models.FPackConfigColumn.fpack_id,
        func.count().label('nb_groupes')
    ).filter(models.FPackConfigColumn.type == 'group')\
     .group_by(models.FPackConfigColumn.fpack_id).all()
    
    config_map = {stat.fpack_id: stat.nb_groupes for stat in config_stats}
    
    result = []
    for projet in projets:
        fpack_id = fpack_map.get(projet.id)
        nb_selections = selections_map.get(projet.id, 0)
        nb_groupes_attendus = config_map.get(fpack_id, 0) if fpack_id else 0
        complet = nb_selections >= nb_groupes_attendus if nb_groupes_attendus > 0 else False
        
        result.append({
            "id": projet.id,
            "nom": projet.nom,
            "id_global": projet.id_global,
            "complet": complet
        })
    
    return result

@router.get("/sous_projets/{id}", response_model=schemas.SousProjetRead)
def get_projet(id: int, db: Session = Depends(get_db)):
    """Récupère un projet par ID"""
    projet = db.query(models.SousProjet).get(id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return projet

@router.put("/sous_projets/{id}", response_model=schemas.SousProjetRead)
def update_projet(id: int, projet_data: schemas.SousProjetCreate, db: Session = Depends(get_db)):
    """Met à jour un projet avec validations"""
    projet = db.query(models.SousProjet).get(id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Vérifications si changement d'id_global
    if projet_data.id_global != projet.id_global:
        projet_global = db.query(models.ProjetGlobal).get(projet_data.id_global)
        if not projet_global:
            raise HTTPException(status_code=404, detail="Projet global non trouvé")
    
    # Vérifier l'unicité du nom si changement
    if projet_data.nom != projet.nom:
        existing = db.query(models.SousProjet)\
            .filter_by(id_global=projet_data.id_global, nom=projet_data.nom)\
            .filter(models.SousProjet.id != id)\
            .first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Un projet avec ce nom existe déjà dans ce projet global"
            )
    
    for key, value in projet_data.dict().items():
        setattr(projet, key, value)
    
    db.commit()
    db.refresh(projet)
    return projet

@router.get("/sous_projets/{id}/selections", response_model=list[schemas.ProjetSelectionReadWithDetails])
def get_projet_selections(id: int, db: Session = Depends(get_db)):
    """Récupère les sélections d'un projet avec détails"""
    if not db.query(models.SousProjet).get(id):
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    selections = db.query(models.ProjetSelection).filter_by(projet_id=id).all()
    
    # Enrichir avec les noms
    result = []
    for sel in selections:
        groupe = db.query(models.Groupes).get(sel.groupe_id)
        item_nom = ProjetDetailService._get_item_name(db, sel.type_item, sel.ref_id)
        
        result.append({
            "projet_id": sel.projet_id,
            "fpack_id": sel.fpack_id,
            "groupe_id": sel.groupe_id,
            "type_item": sel.type_item,
            "ref_id": sel.ref_id,
            "groupe_nom": groupe.nom if groupe else None,
            "item_nom": item_nom
        })
    
    return result

@router.put("/sous_projets/{id}/selections", response_model=dict)
def save_projet_selections(
    id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """Sauvegarde les sélections d'un projet avec validation"""
    projet = db.query(models.SousProjet).get(id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Récupérer l'ID du FPack associé
    sp_fpack = db.query(models.SousProjetFpack)\
        .filter_by(sous_projet_id=id)\
        .first()
    
    if not sp_fpack:
        raise HTTPException(status_code=400, detail="Aucun FPack associé à ce projet")
    
    # Supprimer les anciennes sélections
    old_count = db.query(models.ProjetSelection).filter_by(projet_id=id).count()
    db.query(models.ProjetSelection).filter_by(projet_id=id).delete()
    
    # Ajouter les nouvelles sélections avec validation
    valid_selections = []
    for sel in data.get("selections", []):
        if sel.get("ref_id") is not None and sel.get("type_item"):
            selection = models.ProjetSelection(
                projet_id=id,
                fpack_id=sp_fpack.fpack_id,  # Utiliser l'ID du FPack associé
                groupe_id=sel.get("groupe_id"),
                ref_id=sel.get("ref_id"),
                type_item=sel.get("type_item", "produit")
            )
            db.add(selection)
            valid_selections.append(selection)
    
    db.commit()
    
    return {
        "message": "Sélections enregistrées avec succès",
        "ancien_nombre": old_count,
        "nouveau_nombre": len(valid_selections)
    }

@router.get("/sous_projets/{id}/facture")
def get_projet_facture(id: int, db: Session = Depends(get_db)):
    """Génère la facture d'un projet (optimisé)"""
    from collections import defaultdict

    projet = db.query(models.SousProjet).get(id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

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
        raise HTTPException(status_code=400, detail="Aucun FPack associé à ce projet")
    
    fpack = db.query(models.FPack).get(sp_fpack.fpack_id)

    # Configuration et sélections
    config_cols = db.query(models.FPackConfigColumn)\
        .filter_by(fpack_id=sp_fpack.fpack_id)\
        .order_by(models.FPackConfigColumn.ordre)\
        .all()
    
    sels = db.query(models.ProjetSelection).filter_by(projet_id=id).all()
    sel_map = {s.groupe_id: s.ref_id for s in sels}

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
            chosen_ref = sel_map.get(col.ref_id)
            if not chosen_ref:
                continue
                
            gi = db.query(models.GroupeItem)\
                .filter_by(group_id=col.ref_id, ref_id=chosen_ref)\
                .first()
            
            if not gi:
                continue
                
            if gi.type == "produit":
                produit_counts[gi.ref_id] += 1
            elif gi.type == "equipement":
                for pid, qte in eq_map.get(gi.ref_id, []):
                    produit_counts[pid] += qte
            elif gi.type == "robot":
                robot_counts[gi.ref_id] += 1

    # Récupération des prix et noms
    all_produit_ids = list(produit_counts.keys())
    
    prix_rows = db.query(models.Prix)\
        .filter(
            models.Prix.client_id == client_id,
            models.Prix.produit_id.in_(all_produit_ids)
        ).all() if all_produit_ids else []
    
    prix_map = {(p.produit_id, p.client_id): p for p in prix_rows}
    
    prix_robot_rows = db.query(models.PrixRobot)\
        .join(models.Robots, models.Robots.id == models.PrixRobot.id)\
        .filter(
            models.Robots.client == client_id,
            models.PrixRobot.id.in_(robot_counts.keys())
        ).all() if robot_counts else []
    
    prix_robot_map = {(p.id, p.robot.client): p for p in prix_robot_rows}

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
        p_rec = prix_map.get((pid, client_id))
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
        pr = prix_robot_map.get((rid, client_id))
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
        "projet_id": id,
        "nom_projet": projet.nom,
        "projet_global": {
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