from sqlalchemy.ext.declarative import declarative_base # type: ignore
from sqlalchemy import Column, Integer, String, ForeignKey # type: ignore
from sqlalchemy.orm import relationship # type: ignore

Base = declarative_base()
class Fournisseur(Base):
    __tablename__ = "fournisseurs"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), unique=True, index=True, nullable=False)
    produits = relationship("Produit", back_populates="fournisseur", cascade="all, delete-orphan")

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False)
    robots = relationship("Robots", back_populates="client_rel", cascade="all, delete-orphan")
    fpacks = relationship("FPack", back_populates="client_relfpack")

class Produit(Base):
    __tablename__ = "produits"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    fournisseur_id = Column(Integer, ForeignKey("fournisseurs.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(255))
    fournisseur = relationship("Fournisseur", back_populates="produits")
    equipement_produit = relationship("Equipement_Produit", back_populates="produits", cascade="all, delete-orphan")

class Robots(Base):
    __tablename__ = "robots"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False)
    generation = Column(String(255), nullable=False)
    client = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    payload = Column(Integer, nullable=False)
    range = Column(Integer, nullable=False)
    client_rel = relationship("Client", back_populates="robots")

class Equipements(Base):
    __tablename__ = "equipements"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False)
    equipement_produit = relationship("Equipement_Produit", back_populates="equipements")

class Equipement_Produit(Base):
    __tablename__ = "equipement_produit"
    equipement_id = Column(Integer, ForeignKey("equipements.id"), primary_key=True)
    produit_id = Column(Integer, ForeignKey("produits.id"), primary_key=True)
    produits = relationship("Produit", back_populates="equipement_produit")
    equipements = relationship("Equipements", back_populates="equipement_produit")
    
#FPACK

class FPack(Base):
    __tablename__ = "fpacks"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String)
    client = Column(Integer, ForeignKey("clients.id"), nullable=False)
    fpack_abbr = Column(String, unique=True)
    client_relfpack = relationship("Client", back_populates="fpacks")
    
class Groupes(Base):
    __tablename__ = "groupes"

    id = Column(Integer, primary_key=True,index= True, autoincrement=True)
    nom = Column(String(255), nullable=False)
    items = relationship("GroupeItem", back_populates="groupe", cascade="all, delete-orphan")


class GroupeItem(Base):
    __tablename__ = "groupe_items"

    id = Column(Integer, primary_key=True, index = True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groupes.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  # 'produit' | 'equipement' | 'robot'
    ref_id = Column(Integer, nullable=False)

    groupe = relationship("Groupes", back_populates="items")


class FPackConfigColumn(Base):
    __tablename__ = "fpack_config_columns"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fpack_id = Column(Integer, ForeignKey("fpacks.id", ondelete="CASCADE"), nullable=False)
    ordre = Column(Integer, nullable=False)
    type = Column(String(50), nullable=False)  # 'produit' | 'equipement' | 'group'
    ref_id = Column(Integer, nullable=True)
    
class ProduitIncompatibilite(Base):
    __tablename__ = "produit_incompatibilites"
    produit_id_1 = Column(Integer, ForeignKey("produits.id"), primary_key=True)
    produit_id_2 = Column(Integer, ForeignKey("produits.id"), primary_key=True)

class RobotProduitIncompatibilite(Base):
    __tablename__ = "robot_produit_incompatibilites"
    robot_id = Column(Integer, ForeignKey("robots.id"), primary_key=True)
    produit_id = Column(Integer, ForeignKey("produits.id"), primary_key=True)