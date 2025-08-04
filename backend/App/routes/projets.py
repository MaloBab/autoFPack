from fastapi import APIRouter, Depends, HTTPException 
from sqlalchemy.orm import Session 
from App.database import SessionLocal
from App import models, schemas
from fastapi import Body

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#PROJET

@router.post("/projets", response_model=schemas.ProjetRead)
def create_projet(projet: schemas.ProjetCreate, db: Session = Depends(get_db)):
    db_projet = models.Projet(nom=projet.nom, client=projet.client, fpack_id=projet.fpack_id)
    db.add(db_projet)
    db.commit()
    db.refresh(db_projet)
    return db_projet

@router.get("/projets", response_model=list[schemas.ProjetReadExtended])  # Nouveau schéma avec "complet"
def list_projets(db: Session = Depends(get_db)):
    projets = db.query(models.Projet).all()
    result = []

    for projet in projets:
        fpack_id = projet.fpack_id

        # Récupérer les groupes attendus pour ce fpack
        groupes_attendus = db.query(models.FPackConfigColumn)\
            .filter_by(fpack_id=fpack_id, type='group')\
            .all()
        groupes_ids = [g.ref_id for g in groupes_attendus]

        # Récupérer les sélections de ce projet
        selections = db.query(models.ProjetSelection)\
            .filter_by(projet_id=projet.id)\
            .all()
        selection_ids = [s.groupe_id for s in selections]

        complet = all(gid in selection_ids for gid in groupes_ids)

        result.append({
            "id": projet.id,
            "nom": projet.nom,
            "client": projet.client,
            "fpack_id": projet.fpack_id,
            "complet": complet
        })

    return result

@router.get("/projets/{id}", response_model=schemas.ProjetRead)
def get_projet(id: int, db: Session = Depends(get_db)):
    projet = db.query(models.Projet).filter_by(id=id).first()
    if not projet:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return projet

@router.delete("/projets/{id}")
def delete_projet(id: int, db: Session = Depends(get_db)):
    db_projet = db.query(models.Projet).filter_by(id=id).first()
    if not db_projet:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    db.delete(db_projet)
    db.commit()
    return {"ok": True}

@router.put("/projets/{id}", response_model=schemas.ProjetRead)
def update_projet(id: int, projet: schemas.ProjetCreate, db: Session = Depends(get_db)):
    db_projet = db.query(models.Projet).filter_by(id=id).first()
    if not db_projet:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    db_projet.nom = projet.nom
    db_projet.client = projet.client
    db_projet.fpack_id = projet.fpack_id
    db.commit()
    db.refresh(db_projet)
    return db_projet

#############

@router.get("/projets/{id}/selections", response_model=list[schemas.ProjetSelectionRead])
def get_projet_selections(id: int, db: Session = Depends(get_db)):
    return db.query(models.ProjetSelection).filter(models.ProjetSelection.projet_id == id).all()


@router.put("/projets/{id}/selections", response_model=dict)
def save_projet_selections(
    id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    db.query(models.ProjetSelection).filter(models.ProjetSelection.projet_id == id).delete()
    db.commit()

    for sel in data.get("selections", []):
        if sel.get("ref_id") is None or sel.get("type_item") is None:
            continue  

        selection = models.ProjetSelection(
            projet_id=id,
            groupe_id=sel.get("groupe_id"),
            ref_id=sel.get("ref_id"),
            type_item=sel.get("type_item", "produit")
        )
        db.add(selection)

    db.commit()
    return {"message": "Sélections enregistrées"}
### FACTURE

@router.get("/projets/{id}/facture")
def get_projet_facture(id: int, db: Session = Depends(get_db)):
    from collections import defaultdict

    # 1. Charger le projet
    projet = db.query(models.Projet).filter_by(id=id).first()
    if not projet:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    client_id = projet.client
    fpack_id = projet.fpack_id

    # 2. Config du FPack
    config_cols = db.query(models.FPackConfigColumn).filter(models.FPackConfigColumn.fpack_id == fpack_id).order_by(models.FPackConfigColumn.ordre).all()

    # 3. Sélections projet
    sels = db.query(models.ProjetSelection).filter(models.ProjetSelection.projet_id == id).all()
    sel_map = {s.groupe_id: s.ref_id for s in sels}

    # 4. Mapping équipements -> produits
    eq_prods = db.query(models.Equipement_Produit).all()
    eq_map: dict[int, list[int]] = {}
    for ep in eq_prods:
        eq_map.setdefault(ep.equipement_id, []).append((ep.produit_id, ep.quantite))

    # 5. Compter les produits (avec quantités)
    produit_counts = defaultdict(int)
    robot_counts = defaultdict(int)

    # produits seuls
    for col in config_cols:
        if col.type == "produit":
            produit_counts[col.ref_id] += 1

    # équipements seuls
    for col in config_cols:
        if col.type == "equipement":
            for pid in eq_map.get(col.ref_id, []):
                produit_counts[pid[0]] += pid[1]

    # groupes
    for col in config_cols:
        if col.type == "group":
            chosen_ref = sel_map.get(col.ref_id)
            if not chosen_ref:
                continue
            gi = db.query(models.GroupeItem).filter_by(group_id=col.ref_id, ref_id=chosen_ref).first()
            if not gi:
                continue
            if gi.type == "produit":
                produit_counts[gi.ref_id] += 1
            elif gi.type == "equipement":
                for pid, qte in eq_map.get(gi.ref_id, []):
                    produit_counts[pid] += qte
            elif gi.type == "robot":
                robot_counts[gi.ref_id] += 1

    all_produit_ids = list(produit_counts.keys())

    # 6. Charger prix
    prix_rows = db.query(models.Prix)\
        .filter(models.Prix.client_id == client_id, models.Prix.produit_id.in_(all_produit_ids))\
        .all()
    prix_map = { (p.produit_id, p.client_id): p for p in prix_rows }
    
    prix_robot_rows = (db.query(models.PrixRobot).join(models.Robots, models.Robots.id == models.PrixRobot.id).filter(models.Robots.client == client_id,models.PrixRobot.id.in_(robot_counts.keys())).all()
)
    prix_robot_map = { (p.id, p.robot.client): p for p in prix_robot_rows }

    # 7. Charger noms produits
    produits_rows = db.query(models.Produit).filter(models.Produit.id.in_(all_produit_ids)).all()
    produit_nom_map = {p.id: p.nom for p in produits_rows}

    # 8. Construire les lignes
    lines = []
    total_produit = 0
    total_transport = 0

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
            "produit_id": pid,
            "nom": produit_nom_map.get(pid, f"Produit {pid}"),
            "qte": qte,
            "prix_produit": prix_prod,
            "prix_transport": prix_tr,
            "commentaire": commentaire,
            "total_ligne": total_ligne
        })
    # 9. Ajouter les robots
    robot_rows = db.query(models.Robots).filter(models.Robots.id.in_(robot_counts.keys())).all()
    robot_nom_map = {r.id: r.nom for r in robot_rows}

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
            "produit_id": rid,
            "nom": robot_nom_map.get(rid, f"Robot {rid}"),
            "qte": qte,
            "prix_produit": prix_rob,
            "prix_transport": prix_tr,
            "commentaire": commentaire,
            "total_ligne": total_ligne
        })

    return {
        "projet_id": id,
        "nom_projet": projet.nom,
        "client_id": client_id,
        "fpack_id": fpack_id,
        "currency": "EUR",
        "lines": lines,
        "totaux": {
            "produit": total_produit,
            "transport": total_transport,
            "global": total_produit + total_transport
        }
    }
    
