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

class Produit(Base):
    __tablename__ = "produits"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    fournisseur_id = Column(Integer, ForeignKey("fournisseurs.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(255))
    fournisseur = relationship("Fournisseur", back_populates="produits")
    groupe_produit = relationship("Groupe_Produit", back_populates="produits", cascade="all, delete-orphan")

class Robots(Base):
    __tablename__ = "robots"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False)
    generation = Column(String(255), nullable=False)
    client = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    payload = Column(Integer, nullable=False)
    range = Column(Integer, nullable=False)
    client_rel = relationship("Client", back_populates="robots")

class Groupes(Base):
    __tablename__ = "groupes"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False)
    groupe_produit = relationship("Groupe_Produit", back_populates="groupes")

class Groupe_Produit(Base):
    __tablename__ = "groupe_produit"
    groupe_id = Column(Integer, ForeignKey("groupes.id"), primary_key=True)
    produit_id = Column(Integer, ForeignKey("produits.id"), primary_key=True)
    produits = relationship("Produit", back_populates="groupe_produit")
    groupes = relationship("Groupes", back_populates="groupe_produit")