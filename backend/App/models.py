from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Numeric, String, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()
class Fournisseur(Base):
    __tablename__ = "FPM_fournisseurs"
    __table_args__ = {'schema': 'dbo'}

    id = Column(Integer, primary_key=True)
    nom = Column(String(255), unique=True, index=True, nullable=False)
    produits = relationship("Produit", back_populates="fournisseur", cascade="all, delete-orphan", passive_deletes=True)

class Client(Base):
    __tablename__ = "FPM_clients"
    __table_args__ = {'schema': 'dbo'}
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False)
    robots = relationship("Robots", back_populates="client_rel", cascade="all, delete-orphan", passive_deletes=True)
    fpacks = relationship("FPack", back_populates="client_relfpack", cascade="all, delete-orphan", passive_deletes=True)

class Produit(Base):
    __tablename__ = "FPM_produits"
    __table_args__ = {'schema': 'dbo'}
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(60), nullable=False)
    nom = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    fournisseur_id = Column(Integer, ForeignKey("dbo.FPM_fournisseurs.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(255))
    fournisseur = relationship("Fournisseur", back_populates="produits", passive_deletes=True)
    equipement_produit = relationship("Equipement_Produit", back_populates="produits", cascade="all, delete-orphan", passive_deletes=True)

class Prix(Base):
    __tablename__ = "FPM_prix"
    __table_args__ = {'schema': 'dbo'}

    produit_id = Column(Integer, ForeignKey("dbo.FPM_produits.id", ondelete="CASCADE"), primary_key=True)
    client_id = Column(Integer, ForeignKey("dbo.FPM_clients.id", ondelete="CASCADE"), primary_key=True)
    prix_produit = Column(Numeric(10, 2), nullable=False)
    prix_transport = Column(Numeric(10, 2), nullable=False)
    commentaire = Column(String(255), nullable=True)

    produit = relationship("Produit", passive_deletes=True)
    client = relationship("Client", passive_deletes=True)

class Robots(Base):
    __tablename__ = "FPM_robots"
    __table_args__ = {'schema': 'dbo'}
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(255), nullable=False)
    nom = Column(String(255), nullable=False)
    generation = Column(String(255), nullable=False)
    client = Column(Integer, ForeignKey("dbo.FPM_clients.id", ondelete="CASCADE"), nullable=False)
    payload = Column(Integer, nullable=False)
    range = Column(Integer, nullable=False)
    client_rel = relationship("Client", back_populates="robots", passive_deletes=True)
    prix = relationship("PrixRobot", uselist=False, back_populates="robot")
    
class PrixRobot(Base):
    __table_args__ = {'schema': 'dbo'}
    __tablename__ = "FPM_prix_robot"

    id = Column(Integer, ForeignKey("dbo.FPM_robots.id"), primary_key=True)
    reference = Column(String(255), nullable=False)
    prix_robot = Column(Numeric(10, 2), nullable=False)
    prix_transport = Column(Numeric(10, 2), nullable=False)
    commentaire = Column(String(255))

    robot = relationship("Robots", back_populates="prix")

class Equipements(Base):
    __tablename__ = "FPM_equipements"
    __table_args__ = {'schema': 'dbo'}
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(255), nullable=False)
    nom = Column(String(255), nullable=False)
    
    equipement_produit = relationship("Equipement_Produit", back_populates="equipements", cascade="all, delete-orphan", passive_deletes=True)


class Equipement_Produit(Base):
    __tablename__ = "FPM_equipement_produit"
    __table_args__ = {'schema': 'dbo'}
    equipement_id = Column(Integer, ForeignKey("dbo.FPM_equipements.id", ondelete="CASCADE"), primary_key=True)
    produit_id = Column(Integer, ForeignKey("dbo.FPM_produits.id", ondelete="CASCADE"), primary_key=True)
    quantite = Column(Integer, nullable=False, default=1)
    
    produits = relationship("Produit", back_populates="equipement_produit", passive_deletes=True)
    equipements = relationship("Equipements", back_populates="equipement_produit", passive_deletes=True)

    
#FPACK

class FPack(Base):
    __tablename__ = "FPM_fpacks"
    __table_args__ = {'schema': 'dbo'}
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String)
    client = Column(Integer, ForeignKey("dbo.FPM_clients.id", ondelete="CASCADE"), nullable=False)
    fpack_abbr = Column(String, unique=True)
    client_relfpack = relationship("Client", back_populates="fpacks", passive_deletes=True)
    
class Groupes(Base):
    __tablename__ = "FPM_groupes"
    __table_args__ = {'schema': 'dbo'}
    id = Column(Integer, primary_key=True,index= True, autoincrement=True)
    nom = Column(String(255), nullable=False)
    items = relationship("GroupeItem", back_populates="groupe", cascade="all, delete-orphan", passive_deletes=True)


class GroupeItem(Base):
    __tablename__ = "FPM_groupe_items"
    __table_args__ = {'schema': 'dbo'}
    id = Column(Integer, primary_key=True, index = True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("dbo.FPM_groupes.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  # 'produit' | 'equipement' | 'robot'
    ref_id = Column(Integer, nullable=False)
    statut = Column(String(20), nullable=False, server_default='optionnel')

    groupe = relationship("Groupes", back_populates="items", passive_deletes=True)


class FPackConfigColumn(Base):
    __tablename__ = "FPM_fpack_config_columns"
    __table_args__ = {'schema': 'dbo'}
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fpack_id = Column(Integer, ForeignKey("dbo.FPM_fpacks.id", ondelete="CASCADE"), nullable=False)
    ordre = Column(Integer, nullable=False)
    type = Column(String(50), nullable=False)  # 'produit' | 'equipement' | 'group'
    ref_id = Column(Integer, nullable=True)
    
class ProduitIncompatibilite(Base):
    __tablename__ = "FPM_produit_incompatibilites"
    __table_args__ = {'schema': 'dbo'}
    produit_id_1 = Column(Integer, ForeignKey("dbo.FPM_produits.id", ondelete="CASCADE"), primary_key=True)
    produit_id_2 = Column(Integer, ForeignKey("dbo.FPM_produits.id", ondelete="CASCADE"), primary_key=True)

class RobotProduitIncompatibilite(Base):
    __tablename__ = "FPM_robot_produit_incompatibilites"
    __table_args__ = {'schema': 'dbo'}
    robot_id = Column(Integer, ForeignKey("dbo.FPM_robots.id", ondelete="CASCADE"), primary_key=True)
    produit_id = Column(Integer, ForeignKey("dbo.FPM_produits.id", ondelete="CASCADE"), primary_key=True)

#PROJET GLOBAL

class ProjetGlobal(Base):
    __tablename__ = "FPM_projets_global"
    __table_args__ = {'schema': 'dbo'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    projet = Column(String(255))
    sous_projet = Column(String(255))
    client = Column(Integer, ForeignKey("dbo.FPM_clients.id", ondelete="CASCADE"), nullable=False)

    projets = relationship("Projet", back_populates="global_rel", cascade="all, delete-orphan")
    client_rel = relationship("Client", passive_deletes=True)

#PROJET

class Projet(Base):
    __tablename__ = "FPM_projets"
    __table_args__ = {'schema': 'dbo'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String, nullable=False)
    fpack_id = Column(Integer, ForeignKey("dbo.FPM_fpacks.id", ondelete="CASCADE"), nullable=False)
    id_global = Column(Integer, ForeignKey("dbo.FPM_projets_global.id", ondelete="SET NULL"))

    global_rel = relationship("ProjetGlobal", back_populates="projets", passive_deletes=True)
    selections = relationship("ProjetSelection", back_populates="projet", cascade="all, delete-orphan")


class ProjetSelection(Base):
    __tablename__ = "FPM_projet_selection"
    __table_args__ =  {'schema': 'dbo'}


    projet_id = Column(Integer, ForeignKey("dbo.FPM_projets.id", ondelete="CASCADE"), primary_key=True)
    groupe_id = Column(Integer, ForeignKey("dbo.FPM_groupes.id", ondelete="CASCADE"), primary_key=True)
    type_item = Column(String(50), nullable=False)
    ref_id = Column(Integer, nullable=False)

    projet = relationship("Projet", back_populates="selections")