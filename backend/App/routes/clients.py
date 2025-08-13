from fastapi import APIRouter, Depends, HTTPException  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from App.database import SessionLocal
from App import models, schemas

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
