from fastapi import APIRouter, Depends, HTTPException # type: ignore
from sqlalchemy.orm import Session # type: ignore
from App.database import SessionLocal
from App import models, schemas

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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


@router.get("/prix_robot", response_model=list[schemas.PrixRobotRead])
def get_all_prices(db: Session = Depends(get_db)):
    return db.query(models.PrixRobot).all()


@router.post("/prix_robot", response_model=schemas.PrixRobotRead)
def create_prix(prixRobot: schemas.PrixRobotCreate, db: Session = Depends(get_db)):
    existing = db.query(models.PrixRobot).filter(
        models.PrixRobot.id == prixRobot.id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Prix déjà défini pour ce produit et client")

    db_prix = models.PrixRobot(**prixRobot.dict())
    db.add(db_prix)
    db.commit()
    db.refresh(db_prix)
    return db_prix


# PUT
@router.put("/prix_robot/{id}", response_model=schemas.PrixRobotRead)
def update_price(id: int, data: schemas.PrixRobotUpdate, db: Session = Depends(get_db)):
    prix = db.query(models.PrixRobot).filter(models.PrixRobot.id == id).first()
    if not prix:
        raise HTTPException(status_code=404, detail="Prix non trouvé")
    for key, value in data.dict().items():
        setattr(prix, key, value)
    db.commit()
    db.refresh(prix)
    return prix


@router.delete("/prix_robot/{id}")
def delete_price(id: int, db: Session = Depends(get_db)):
    prix = db.query(models.PrixRobot).filter(models.PrixRobot.id == id).first()
    if not prix:
        raise HTTPException(status_code=404, detail="Prix non trouvé")
    db.delete(prix)
    db.commit()
    return {"message": "Prix supprimé avec succès"}