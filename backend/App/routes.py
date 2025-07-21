from fastapi import APIRouter, Depends, HTTPException 
from sqlalchemy.orm import Session 
from App.database import SessionLocal
from App import models, schemas
from sqlalchemy import inspect 
from sqlalchemy.orm import selectinload
from App.export_fpack_to_excel import export_fpack_config, export_all_fpacks
from fastapi.responses import StreamingResponse
from io import BytesIO
import os

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/table-columns/{table_name}", response_model=list[str])
def get_table_columns(table_name: str, db: Session = Depends(get_db)):
    inspector = inspect(db.bind)

    use_sql_server = os.getenv("USE_SQL_SERVER", "false").lower() == "true"

    if use_sql_server:
        table_mapping = {
            "clients": "FPM_clients",
            "produits": "FPM_produits",
            "equipements": "FPM_equipements",
            "robots": "FPM_robots",
            "fournisseurs": "FPM_fournisseurs",
            "fpacks": "FPM_fpacks",
            "prix": "FPM_prix",
            "projets": "FPM_projets",
        }

        actual_name = table_mapping.get(table_name)
        if not actual_name:
            raise HTTPException(status_code=404, detail=f"Table inconnue : {table_name}")
    else:
        actual_name = table_name

    columns = inspector.get_columns(actual_name)
    return [col["name"] for col in columns]


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

    db.delete(db_produit)
    db.commit()
    return {"ok": True}

@router.get("/produits/{id}", response_model=schemas.ProduitRead)
def get_produit(id: int, db: Session = Depends(get_db)):
    produit = db.query(models.Produit).get(id)
    if not produit:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return produit


# PRIX

@router.get("/prix", response_model=list[schemas.PrixRead])
def list_prix(db: Session = Depends(get_db)):
    return db.query(models.Prix).all()

@router.post("/prix", response_model=schemas.PrixRead)
def create_prix(prix: schemas.PrixCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Prix).filter(
        models.Prix.produit_id == prix.produit_id,
        models.Prix.client_id == prix.client_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Prix déjà défini pour ce produit et client")

    db_prix = models.Prix(**prix.dict())
    db.add(db_prix)
    db.commit()
    db.refresh(db_prix)
    return db_prix

@router.put("/prix/{produit_id}/{client_id}", response_model=schemas.PrixRead)
def update_prix(produit_id: int, client_id: int, prix: schemas.PrixCreate, db: Session = Depends(get_db)):
    db_prix = db.query(models.Prix).filter(
        models.Prix.produit_id == produit_id,
        models.Prix.client_id == client_id
    ).first()
    if not db_prix:
        raise HTTPException(status_code=404, detail="Prix non trouvé")
    for key, value in prix.model_dump().items():
        setattr(db_prix, key, value)
    db.commit()
    db.refresh(db_prix)
    return db_prix

@router.delete("/prix/{produit_id}/{client_id}")
def delete_prix(produit_id: int, client_id: int, db: Session = Depends(get_db)):
    db_prix = db.query(models.Prix).filter(
        models.Prix.produit_id == produit_id,
        models.Prix.client_id == client_id
    ).first()
    if not db_prix:
        raise HTTPException(status_code=404, detail="Prix non trouvé")
    db.delete(db_prix)
    db.commit()
    return {"ok": True}

@router.get("/prix/{produit_id}/{client_id}", response_model=schemas.PrixRead)
def get_prix(produit_id: int, client_id: int, db: Session = Depends(get_db)):
    db_prix = db.query(models.Prix).filter(
        models.Prix.produit_id == produit_id,
        models.Prix.client_id == client_id
    ).first()
    if not db_prix:
        raise HTTPException(status_code=404, detail="Prix non trouvé")
    return db_prix


# FOURNISSEURS
@router.get("/fournisseurs", response_model=list[schemas.FournisseurRead])
def list_fournisseurs(db: Session = Depends(get_db)):
    return db.query(models.Fournisseur).all()

@router.post("/fournisseurs", response_model=schemas.FournisseurRead)
def create_fournisseur(fournisseur: schemas.FournisseurCreate, db: Session = Depends(get_db)):
    db_fournisseur = models.Fournisseur(**fournisseur.dict())
    db.add(db_fournisseur)
    db.commit()
    db.refresh(db_fournisseur)
    return db_fournisseur


@router.put("/fournisseurs/{id}", response_model=schemas.FournisseurRead)
def update_fournisseur(id: int, fournisseur: schemas.FournisseurCreate, db: Session = Depends(get_db)):
    db_fournisseur = db.query(models.Fournisseur).get(id)
    if not db_fournisseur:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    for key, value in fournisseur.dict().items():
        setattr(db_fournisseur, key, value)
    db.commit()
    db.refresh(db_fournisseur)
    return db_fournisseur


@router.delete("/fournisseurs/{id}")
def delete_fournisseur(id: int, db: Session = Depends(get_db)):
    db_fournisseur = db.query(models.Fournisseur).get(id)
    if not db_fournisseur:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    db.delete(db_fournisseur)
    db.commit()
    return {"ok": True}

# CLIENTS
@router.get("/clients", response_model=list[schemas.ClientRead])
def list_clients(db: Session = Depends(get_db)):
    return db.query(models.Client).all()

@router.post("/clients", response_model=schemas.ClientRead)
def create_client(client: schemas.ClientCreate, db: Session = Depends(get_db)):
    db_client = models.Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@router.put("/clients/{id}", response_model=schemas.ClientRead)
def update_client(id: int, client: schemas.ClientCreate, db: Session = Depends(get_db)):
    db_client = db.query(models.Client).get(id)
    if not db_client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    for key, value in client.dict().items():
        setattr(db_client, key, value)
    db.commit()
    db.refresh(db_client)
    return db_client

@router.delete("/clients/{id}")
def delete_client(id: int, db: Session = Depends(get_db)):
    db_client = db.query(models.Client).get(id)
    if not db_client:
        raise HTTPException(status_code=404, detail="Client non trouvé")

    # Vérifie si ce client est utilisé dans des robots
    robots = db.query(models.Robots).filter(models.Robots.client == id).all()
    fpacks = db.query(models.FPack).filter(models.FPack.client == id).all()

    noms_robots = [r.nom for r in robots]
    noms_fpacks = [f.nom for f in fpacks]

    erreurs = []
    if noms_robots:
        erreurs.append(f"robots : {', '.join(noms_robots)}")
    if noms_fpacks:
        erreurs.append(f"fpacks : {', '.join(noms_fpacks)}")

    if erreurs:
        raise HTTPException(
            status_code=400,
            detail=f"Suppression impossible : {db_client.nom} est lié aux {', et aux '.join(erreurs)}"
        )

    db.delete(db_client)
    db.commit()
    return {"ok": True}

# ROBOTS
@router.get("/robots", response_model=list[schemas.RobotRead])
def list_robots(db: Session = Depends(get_db)):
    return db.query(models.Robots).all()

@router.post("/robots", response_model=schemas.RobotRead)
def create_robot(robot: schemas.RobotCreate, db: Session = Depends(get_db)):
    db_robot = models.Robots(**robot.dict())
    db.add(db_robot)
    db.commit()
    db.refresh(db_robot)
    return db_robot

@router.put("/robots/{id}", response_model=schemas.RobotRead)
def update_robot(id: int, robot: schemas.RobotCreate, db: Session = Depends(get_db)):
    db_robot = db.query(models.Robots).get(id)
    if not db_robot:
        raise HTTPException(status_code=404, detail="Robot non trouvé")
    for key, value in robot.dict().items():
        setattr(db_robot, key, value)
    db.commit()
    db.refresh(db_robot)
    return db_robot

@router.delete("/robots/{id}")
def delete_robot(id: int, db: Session = Depends(get_db)):
    db_robot = db.query(models.Robots).get(id)
    if not db_robot:
        raise HTTPException(status_code=404, detail="Robot non trouvé")
    db.delete(db_robot)
    db.commit()
    return {"ok": True}

# EQUIPEMENTS
@router.get("/equipements", response_model=list[schemas.EquipementRead])
def list_equipements(db: Session = Depends(get_db)):
    return db.query(models.Equipements).all()

@router.post("/equipements", response_model=schemas.EquipementRead)
def create_equipement(equipement: schemas.EquipementCreate, db: Session = Depends(get_db)):
    db_equipement = models.Equipements(**equipement.dict())
    db.add(db_equipement)
    db.commit()
    db.refresh(db_equipement)
    return db_equipement

@router.put("/equipements/{id}", response_model=schemas.EquipementRead)
def update_equipement(id: int, equipement: schemas.EquipementCreate, db: Session = Depends(get_db)):
    db_equipement = db.query(models.Equipements).get(id)
    if not db_equipement:
        raise HTTPException(status_code=404, detail="Equipement non trouvé")
    for key, value in equipement.dict().items():
        setattr(db_equipement, key, value)
    db.commit()
    db.refresh(db_equipement)
    return db_equipement

@router.delete("/equipements/{id}")
def delete_equipement(id: int, db: Session = Depends(get_db)):
    db_equipement = db.query(models.Equipements).get(id)
    if not db_equipement:
        raise HTTPException(status_code=404, detail="Equipement non trouvé")
    db.delete(db_equipement)
    db.commit()
    return {"ok": True}


@router.get("/equipements/{id}", response_model=schemas.EquipementRead)
def get_equipement(id: int, db: Session = Depends(get_db)):
    equipement = db.query(models.Equipements)\
        .options(selectinload(models.Equipements.equipement_produit))\
        .filter(models.Equipements.id == id)\
        .first()
    if not equipement:
        raise HTTPException(status_code=404, detail="Équipement non trouvé")
    return equipement

# EQUIPEMENTS PRODUITS

@router.get("/equipementproduits", response_model=dict[int, list[schemas.EquipementProduitRead]])
def get_all_equipement_produits(db: Session = Depends(get_db)):
    results = db.query(models.Equipement_Produit).all()

    equipement_dict: dict[int, list[models.Equipement_Produit]] = {}
    for ep in results:
        equipement_dict.setdefault(ep.equipement_id, []).append(ep)

    return equipement_dict

@router.get("/equipementproduit/{equipement_id}", response_model=list[schemas.EquipementProduitRead])
def get_equipement_produit_by_equipement(equipement_id: int, db: Session = Depends(get_db)):
    return db.query(models.Equipement_Produit).filter(models.Equipement_Produit.equipement_id == equipement_id).all()

@router.post("/equipementproduit", response_model=schemas.EquipementProduitRead)
def create_equipement_produit(equipement_produit: schemas.EquipementProduitCreate, db: Session = Depends(get_db)):
    db_equipement_produit = models.Equipement_Produit(**equipement_produit.dict())
    db.add(db_equipement_produit)
    db.commit()
    db.refresh(db_equipement_produit)
    return db_equipement_produit


@router.delete("/equipementproduit/{id}")
def delete_equipement_produit(id: int, db: Session = Depends(get_db)):
    db_equipement_produit = db.query(models.Equipement_Produit).get(id)
    if not db_equipement_produit:
        raise HTTPException(status_code=404, detail="Equipement de produit non trouvé")
    db.delete(db_equipement_produit)
    db.commit()
    return {"ok": True}

@router.delete("/equipementproduit/clear/{equipement_id}")
def clear_equipement_produits(equipement_id: int, db: Session = Depends(get_db)):
    db.query(models.Equipement_Produit).filter(models.Equipement_Produit.equipement_id == equipement_id).delete()
    db.commit()
    return {"ok": True}


@router.get("/equipements/{equipement_id}")
def get_equipement(equipement_id: int, db: Session = Depends(get_db)):
    equipement = db.query(models.Equipements).filter(models.Equipements.id == equipement_id).first()
    if not equipement:
        raise HTTPException(status_code=404, detail="Equipement not found")
    return equipement


# FPACKS
@router.get("/fpacks", response_model=list[schemas.FPackRead])
def list_fpacks(db: Session = Depends(get_db)):
    return db.query(models.FPack).all()

@router.post("/fpacks", response_model=schemas.FPackRead)
def create_fpack(fpack: schemas.FPackCreate, db: Session = Depends(get_db)):
    db_fpack = models.FPack(**fpack.dict())
    db.add(db_fpack)
    db.commit()
    db.refresh(db_fpack)
    return db_fpack

@router.put("/fpacks/{id}", response_model=schemas.FPackRead)
def update_fpack(id: int, fpack: schemas.FPackCreate, db: Session = Depends(get_db)):
    db_fpack = db.query(models.FPack).get(id)
    if not db_fpack:
        raise HTTPException(status_code=404, detail="FPack non trouvé")
    for key, value in fpack.dict().items():
        setattr(db_fpack, key, value)
    db.commit()
    db.refresh(db_fpack)
    return db_fpack

@router.delete("/fpacks/{id}")
def delete_fpack(id: int, db: Session = Depends(get_db)):
    db_fpack = db.query(models.FPack).get(id)
    if not db_fpack:
        raise HTTPException(status_code=404, detail="FPack non trouvé")
    db.delete(db_fpack)
    db.commit()
    return {"ok": True}

@router.get("/fpacks/{id}", response_model=schemas.FPackRead)
def get_fpack(id: int, db: Session = Depends(get_db)):
    db_fpack = db.query(models.FPack).get(id)
    if not db_fpack:
        raise HTTPException(status_code=404, detail="FPack non trouvé")
    return db_fpack

@router.post("/fpacks/{fpack_id}/duplicate", response_model=schemas.FPackRead)
def duplicate_fpack(fpack_id: int, db: Session = Depends(get_db)):
    original_fpack = db.query(models.FPack).filter(models.FPack.id == fpack_id).first()
    if not original_fpack:
        raise HTTPException(status_code=404, detail="FPack non trouvée")

    new_fpack = models.FPack(
        nom=original_fpack.nom + " (copie)",
        client=original_fpack.client,
        fpack_abbr=original_fpack.fpack_abbr
    )
    db.add(new_fpack)
    db.commit()
    db.refresh(new_fpack)

    config_columns = db.query(models.FPackConfigColumn).filter_by(fpack_id=fpack_id).all()
    for col in config_columns:
        copied_col = models.FPackConfigColumn(
            fpack_id=new_fpack.id,
            ordre=col.ordre,
            type=col.type,
            ref_id=col.ref_id
        )
        db.add(copied_col)

    db.commit()

    return new_fpack

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
                    "label": get_item_label(item.type, item.ref_id, db)
                }
                for item in items
            ]

        result.append(entry)

    return result


def get_item_label(type_: str, ref_id: int, db: Session):
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

@router.get("/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    return {
        "produits": db.query(models.Produit).count(),
        "equipements": db.query(models.Equipements).count(),
        "robots": db.query(models.Robots).count(),
        "clients": db.query(models.Client).count(),
        "fournisseurs": db.query(models.Fournisseur).count(),
        "fpacks": db.query(models.FPack).count()
    }
    
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


# ROBOT-PRODUIT-INCOMPATIBILITÉS
@router.get("/robot-produit-incompatibilites", response_model=list[schemas.RobotProduitIncompatibiliteRead])
def list_robot_incompatibilites(db: Session = Depends(get_db)):
    return db.query(models.RobotProduitIncompatibilite).all()

@router.post("/robot-produit-incompatibilites", response_model=schemas.RobotProduitIncompatibiliteRead)
def create_robot_incompatibilite(incomp: schemas.RobotProduitIncompatibiliteCreate, db: Session = Depends(get_db)):
    db_incomp = models.RobotProduitIncompatibilite(**incomp.dict())
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

@router.delete("/robot-produit-incompatibilites")
def delete_robot_produit_incompatibilite(incomp: schemas.RobotProduitIncompatibiliteCreate, db: Session = Depends(get_db)):
    db.query(models.RobotProduitIncompatibilite).filter(
        models.RobotProduitIncompatibilite.robot_id == incomp.robot_id,
        models.RobotProduitIncompatibilite.produit_id == incomp.produit_id
    ).delete()
    db.commit()
    return {"ok": True}

#EXPORT FPACK TO EXCEL
@router.post("/export-fpack/{fpack_id}")
def export_fpack(fpack_id: int, db: Session = Depends(get_db)):
    wb = export_fpack_config(fpack_id, db)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    headers = {
        'Content-Disposition': f'attachment; filename="F-Pack-{fpack_id}.xlsx"'
    }

    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

@router.get("/export-fpacks/all")
def export_all_fpacks_route(db: Session = Depends(get_db)):
    wb = export_all_fpacks(db)
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    headers = {
        'Content-Disposition': 'attachment; filename="FPacks-All.xlsx"'
    }

    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

#PROJET

@router.post("/projets", response_model=schemas.ProjetRead)
def create_projet(projet: schemas.ProjetCreate, db: Session = Depends(get_db)):
    db_projet = models.Projet(nom=projet.nom, client=projet.client, fpack_id=projet.fpack_id)
    db.add(db_projet)
    db.commit()
    db.refresh(db_projet)
    return db_projet

@router.get("/projets", response_model=list[schemas.ProjetRead])
def list_projets(db: Session = Depends(get_db)):
    return db.query(models.Projet).all()

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

    # Met à jour les champs de base
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

from fastapi import Body

@router.put("/projets/{id}/selections", response_model=dict)
def save_projet_selections(
    id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    db.query(models.ProjetSelection).filter(models.ProjetSelection.projet_id == id).delete()
    db.commit()
    for sel in data.get("selections", []):
        selection = models.ProjetSelection(
            projet_id=id,
            groupe_id=sel.get("groupe_id"),
            ref_id=sel.get("ref_id"),
            type_item=sel.get("type_item", "produit")  # ou "equipement" ou "groupe" selon le contexte
        )
        db.add(selection)
    db.commit()
    return {"message": "Sélections enregistrées"}