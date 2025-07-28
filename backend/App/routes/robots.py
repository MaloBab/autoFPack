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


@router.delete("/robot-produit-incompatibilites")
def delete_robot_produit_incompatibilite(incomp: schemas.RobotProduitIncompatibiliteCreate, db: Session = Depends(get_db)):
    db.query(models.RobotProduitIncompatibilite).filter(
        models.RobotProduitIncompatibilite.robot_id == incomp.robot_id,
        models.RobotProduitIncompatibilite.produit_id == incomp.produit_id
    ).delete()
    db.commit()
    return {"ok": True}


@router.get("/prix_robot", response_model=list[schemas.PrixRobotOut])
def get_all_prices(db: Session = Depends(get_db)):
    return db.query(models.PrixRobot).all()


@router.post("/prix_robot", response_model=schemas.PrixRobotOut)
def create_price(data: schemas.PrixRobotCreate, db: Session = Depends(get_db)):
    if db.query(models.PrixRobot).filter(models.PrixRobot.robot_id == data.robot_id).first():
        raise HTTPException(status_code=400, detail="Ce robot a déjà un prix défini")
    prix = models.PrixRobot(**data.dict())
    db.add(prix)
    db.commit()
    db.refresh(prix)
    return prix

# PUT
@router.put("/prix_robot/{robot_id}", response_model=schemas.PrixRobotOut)
def update_price(robot_id: int, data: schemas.PrixRobotUpdate, db: Session = Depends(get_db)):
    prix = db.query(models.PrixRobot).filter(models.PrixRobot.robot_id == robot_id).first()
    if not prix:
        raise HTTPException(status_code=404, detail="Prix non trouvé")
    for key, value in data.dict().items():
        setattr(prix, key, value)
    db.commit()
    db.refresh(prix)
    return prix


@router.delete("/prix_robot/{robot_id}")
def delete_price(robot_id: int, db: Session = Depends(get_db)):
    prix = db.query(models.PrixRobot).filter(models.PrixRobot.robot_id == robot_id).first()
    if not prix:
        raise HTTPException(status_code=404, detail="Prix non trouvé")
    db.delete(prix)
    db.commit()
    return {"message": "Prix supprimé avec succès"}