import importlib
import pkgutil
from fastapi import APIRouter, Depends, HTTPException # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from App.database import SessionLocal
from App import models
from sqlalchemy import inspect  # type: ignore
import os
from App.routes import __path__ as routes_path

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
            "prix_robot": "FPM_prix_robot",
            "sous_projets": "FPM_sous_projets",
            "projets_global": "FPM_projets_global",
            "sous_projet_fpack": "FPM_sous_projet_fpack"
        }

        actual_name = table_mapping.get(table_name)
        if not actual_name:
            raise HTTPException(status_code=404, detail=f"Table inconnue : {table_name}")
    else:
        actual_name = table_name

    columns = inspector.get_columns(actual_name)
    return [col["name"] for col in columns]

@router.get("/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    return {
        "produits": db.query(models.Produit).count(),
        "equipements": db.query(models.Equipements).count(),
        "robots": db.query(models.Robots).count(),
        "clients": db.query(models.Client).count(),
        "fournisseurs": db.query(models.Fournisseur).count(),
        "fpacks": db.query(models.FPack).count(),
        "projets": db.query(models.SousProjet).count(),
    }

for module_info in pkgutil.iter_modules(routes_path):
    module_name = module_info.name
    full_module_name = f"App.routes.{module_name}"
    module = importlib.import_module(full_module_name)

    if hasattr(module, "router"):
        sub_router = getattr(module, "router")
        router.include_router(sub_router)