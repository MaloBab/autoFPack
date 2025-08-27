import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException #type: ignore
from pydantic import BaseModel, Field #type: ignore
from App.database import SessionLocal
import logging

router = APIRouter()



# Chemin du fichier de configuration
CONFIG_DIR = Path("config")
CONFIG_FILE = CONFIG_DIR / "mapping-config.json"



# Modèles Pydantic
class MappingConfigModel(BaseModel):
    version: str = Field(..., description="Version de la configuration")
    description: str = Field(..., description="Description de la configuration")
    excel_columns: Dict[str, Any] = Field(..., description="Configuration des colonnes Excel")
    matching_rules: Dict[str, Any] = Field(..., description="Règles de correspondance")
    validation_rules: Dict[str, Any] = Field(..., description="Règles de validation")



class ConfigResponse(BaseModel):
    success: bool
    config: Optional[MappingConfigModel] = None
    message: str



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def ensure_config_directory():
    """Assure que le répertoire de configuration existe"""
    CONFIG_DIR.mkdir(exist_ok=True)



def get_default_config() -> Dict[str, Any]:
    """Retourne la configuration par défaut"""
    return {
        "version": "1.0",
        "description": "Configuration de mapping pour l'import Excel vers base de données",
        "excel_columns": {
            "FPack Number": {
                "target": "sous_projet_fpack.FPack_number",
                "type": "direct",
                "required": True,
                "description": "Numéro unique du F-Pack"
            },
            "Robot location code": {
                "target": "sous_projet_fpack.Robot_Location_Code",
                "type": "direct",
                "required": True,
                "description": "Code de localisation du robot"
            },
            "Contractor": {
                "target": "sous_projet_fpack.contractor",
                "type": "direct",
                "required": False,
                "description": "Entrepreneur/Contractant"
            },
            "Required Delivery time": {
                "target": "sous_projet_fpack.required_delivery_time",
                "type": "direct",
                "required": False,
                "description": "Temps de livraison requis"
            },
            "Delivery site": {
                "target": "sous_projet_fpack.delivery_site",
                "type": "direct",
                "required": False,
                "description": "Site de livraison"
            },
            "Tracking": {
                "target": "sous_projet_fpack.tracking",
                "type": "direct",
                "required": False,
                "description": "Numéro de suivi"
            },
            "Mechanical Unit": {
                "target": "selection",
                "type": "fuzzy_match",
                "required": False,
                "groupe_nom": "Mechanical Unit",
                "search_in": ["robots", "equipements"],
                "search_fields": ["nom", "model"],
                "description": "Unité mécanique/Robot",
                "fuzzy_threshold": 0.7,
                "case_sensitive": False
            },
            "Robot Controller": {
                "target": "selection",
                "type": "fuzzy_match",
                "required": False,
                "groupe_nom": "Robot Controller",
                "search_in": ["produits", "equipements"],
                "search_fields": ["nom", "description"],
                "description": "Contrôleur de robot",
                "fuzzy_threshold": 0.8,
                "case_sensitive": False
            }
        },
        "matching_rules": {
            "exact_match": {
                "description": "Correspondance exacte (insensible à la casse)",
                "case_sensitive": False,
                "trim_whitespace": True
            },
            "fuzzy_match": {
                "description": "Correspondance approximative",
                "default_threshold": 0.7,
                "case_sensitive": False,
                "trim_whitespace": True,
                "algorithm": "difflib"
            },
            "partial_match": {
                "description": "Correspondance partielle (contient le texte)",
                "case_sensitive": False,
                "trim_whitespace": True
            }
        },
        "validation_rules": {
        "required_fields": ["FPack Number", "Robot location code"],
        "max_suggestions": 10,
        "min_suggestion_score": 0.3
        }
    }

@router.put("/mapping-config", response_model=ConfigResponse)
async def update_mapping_config(config_data: MappingConfigModel):
    """Met à jour la configuration de mapping"""
    try:
        ensure_config_directory()
        
        # Valider la configuration
        try:
            validated_config = config_data.dict()
        except Exception as validation_error:
            return ConfigResponse(
                success=False,
                config=None,
                message=f"Configuration invalide: {validation_error}"
            )
        
        # Sauvegarder la configuration
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(validated_config, f, indent=2, ensure_ascii=False)
        
        return ConfigResponse(
            success=True,
            config=config_data,
            message="Configuration mise à jour avec succès"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la mise à jour de la configuration: {str(e)}"
        )

@router.post("/mapping-config", response_model=ConfigResponse)
async def create_mapping_config(config_data: MappingConfigModel):
    """Crée une nouvelle configuration de mapping (alias pour update)"""
    return await update_mapping_config(config_data)


@router.get("/mapping-config", response_model=ConfigResponse)
async def get_mapping_config():
    """Récupère la configuration de mapping actuelle"""
    try:
        ensure_config_directory()
        
        # Tenter de lire le fichier de configuration
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Valider la configuration
            try:
                config_model = MappingConfigModel(**config_data)
                return ConfigResponse(
                    success=True,
                    config=config_model,
                    message="Configuration chargée avec succès"
                )
            except Exception :
                default_config = get_default_config()
                try:
                    default_model = MappingConfigModel(**default_config)
                    return ConfigResponse(
                        success=True,
                        config=default_model,
                        message="Configuration par défaut chargée (fichier corrompu)"
                    )
                except Exception:
                    return ConfigResponse(
                        success=False,
                        config=None,
                        message="Erreur de configuration"
                    )
        else:
            # Aucun fichier de configuration n'existe, créer et retourner la config par défaut
            default_config = get_default_config()
            
            # Sauvegarder la config par défaut
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            default_model = MappingConfigModel(**default_config)
            return ConfigResponse(
                success=True,
                config=default_model,
                message="Configuration par défaut créée"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de la configuration: {str(e)}"
        )
        
@router.get("/mapping-config/info")
async def get_mapping_config_info():
    """Récupère les informations sur la configuration de mapping"""
    try:
        ensure_config_directory()
        
        info = {
            "config_file_exists": CONFIG_FILE.exists(),
            "config_directory": str(CONFIG_DIR),
            "config_file_path": str(CONFIG_FILE)
        }
        
        if CONFIG_FILE.exists():
            stat = CONFIG_FILE.stat()
            info.update({
                "file_size": stat.st_size,
                "last_modified": stat.st_mtime,
                "readable": os.access(CONFIG_FILE, os.R_OK),
                "writable": os.access(CONFIG_FILE, os.W_OK)
            })
            
            # Essayer de lire la version depuis le fichier
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                info["version"] = config_data.get("version", "unknown")
                info["description"] = config_data.get("description", "")
                info["columns_count"] = len(config_data.get("excel_columns", {}))
            except:
                info["file_corrupted"] = True
        
        return {"success": True, "info": info}
        
    except Exception as e:
        return {"success": False, "error": str(e)}