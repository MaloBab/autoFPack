from sqlalchemy.ext.declarative import declarative_base # type: ignore
from sqlalchemy import Column, Integer, String, ForeignKey # type: ignore
from sqlalchemy.orm import relationship # type: ignore

Base = declarative_base()
class Fournisseur(Base):
    __tablename__ = "fournisseurs"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), unique=True, index=True, nullable=False)
    produits = relationship("Produit", back_populates="fournisseur")

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False)

class Produit(Base):
    __tablename__ = "produits"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    fournisseur_id = Column(Integer, ForeignKey("fournisseurs.id"), nullable=False)
    type = Column(String(255))
    fournisseur = relationship("Fournisseur", back_populates="produits")
