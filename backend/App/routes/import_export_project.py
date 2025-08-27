from App import models
from App.database import SessionLocal
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends #type: ignore
from sqlalchemy.orm import Session # type: ignore
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd # type: ignore
import traceback
import re
from io import BytesIO
from difflib import SequenceMatcher
from dataclasses import dataclass

router = APIRouter()

# Configuration et constantes
REQUIRED_SHEET_NAME = "F-Pack Matrix"
HEADER_ROW = 4
SUPPORTED_EXTENSIONS = ('.xlsx', '.xls')
MAX_PREVIEW_ROWS = 5
MAX_SUGGESTIONS = 5
MAX_MATCHES = 10

# Classes de données pour une meilleure structure
@dataclass
class ProcessingResult:
    status: str = "success"
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

@dataclass
class ImportStats:
    created_projects: int = 0
    created_fpacks: int = 0
    created_selections: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

# Utilitaires de base réutilisables
def get_db():
    """Générateur de session de base de données"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def clean_text(text: str) -> str:
    """Nettoie le texte des sauts de ligne et espaces multiples"""
    if not isinstance(text, str):
        return str(text) if text else ""
    return re.sub(r"\s+", " ", text.replace("\n", " ")).strip()

def clean_dataframe_data(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie les données du DataFrame"""
    df.columns = df.columns.str.strip()
    return df

def get_valid_rows(df: pd.DataFrame) -> List[Dict]:
    """Extrait les lignes valides du DataFrame (non vides, non 'total')"""
    valid_rows = []
    for index, row in df.iterrows():
        first_cell = str(row.iloc[0]).strip().lower() if pd.notna(row.iloc[0]) else ""
        if first_cell and first_cell != "total":
            row_dict = row.fillna('').to_dict()
            row_dict['_row_index'] = index
            valid_rows.append(row_dict)
    return valid_rows

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """Valide la présence des champs requis"""
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise HTTPException(
            status_code=400, 
            detail=f"Champs requis manquants: {', '.join(missing_fields)}"
        )

# Utilitaires de mapping et recherche
class DataMapper:
    """Classe utilitaire pour le mapping des données"""
    
    @staticmethod
    def get_field_value_case_insensitive(row_data: Dict[str, Any], field_name: str) -> str:
        """Récupère une valeur de champ insensible à la casse"""
        # Recherche exacte d'abord
        if field_name in row_data:
            value = row_data[field_name]
            return str(value).strip() if value else ""
        
        # Recherche insensible à la casse
        field_name_lower = field_name.lower()
        for key, value in row_data.items():
            if key.lower() == field_name_lower:
                return str(value).strip() if value else ""
        return ""
    
    @staticmethod
    def get_mapped_field_value(row_data: Dict[str, Any], mapping: Dict[str, str], field_name: str) -> str:
        """Récupère la valeur d'un champ mappé depuis la configuration"""
        # Recherche exacte
        if field_name in mapping:
            excel_column = mapping[field_name]
            return DataMapper.get_field_value_case_insensitive(row_data, excel_column)
        
        # Recherche insensible à la casse pour le nom du champ
        field_name_lower = field_name.lower()
        for dest_field, excel_column in mapping.items():
            if dest_field.lower() == field_name_lower:
                return DataMapper.get_field_value_case_insensitive(row_data, excel_column)
        return ""
    
    @staticmethod
    def build_excel_to_group_mapping(groups_config: List[Dict]) -> Dict[str, str]:
        """Construit le mapping colonne Excel -> nom de groupe"""
        mapping = {}
        for group_config in groups_config:
            excel_col = group_config.get("excel_column")
            group_name = group_config.get("group_name")
            if excel_col and group_name:
                mapping[excel_col.lower()] = group_name
        return mapping

# Cache et optimisations de requêtes
class DatabaseCache:
    """Gestionnaire de cache pour les requêtes fréquentes"""
    
    def __init__(self, db: Session):
        self.db = db
        self._templates_cache = {}
        self._groups_cache = {}
    
    def get_fpack_template_groups(self, fpack_id: int) -> List[Dict]:
        """Récupère les groupes d'un template avec cache"""
        if fpack_id in self._groups_cache:
            return self._groups_cache[fpack_id]
        
        try:
            config_columns = self.db.query(models.FPackConfigColumn).filter(
                models.FPackConfigColumn.fpack_id == fpack_id,
                models.FPackConfigColumn.type == 'group'
            ).order_by(models.FPackConfigColumn.ordre).all()
            
            groups = []
            for config_col in config_columns:
                if config_col.ref_id:
                    groupe = self.db.query(models.Groupes).filter(
                        models.Groupes.id == config_col.ref_id
                    ).first()
                    
                    if groupe:
                        groupe_items = self.db.query(models.GroupeItem).filter(
                            models.GroupeItem.group_id == groupe.id
                        ).all()
                        
                        groups.append({
                            "id": groupe.id,
                            "nom": groupe.nom,
                            "items": groupe_items,
                            "ordre": config_col.ordre
                        })
            
            self._groups_cache[fpack_id] = groups
            return groups
            
        except Exception as e:
            print(f"Erreur lors de la récupération des groupes pour template {fpack_id}: {e}")
            return []
    
    def get_templates_batch(self, template_ids: List[int]) -> Dict[int, Dict]:
        """Récupère plusieurs templates en une seule requête"""
        uncached_ids = [tid for tid in template_ids if tid not in self._templates_cache]
        
        if uncached_ids:
            templates = self.db.query(models.FPack).filter(
                models.FPack.id.in_(uncached_ids)
            ).all()
            
            for template in templates:
                self._templates_cache[template.id] = {
                    'template': template,
                    'groups': self.get_fpack_template_groups(template.id)
                }
        
        return {tid: self._templates_cache[tid] for tid in template_ids if tid in self._templates_cache}

# Moteur de recherche et correspondance
class MatchingEngine:
    """Moteur de recherche et correspondance d'items"""
    
    SEARCH_TABLES = {
        'robots': models.Robots,
        'equipements': models.Equipements,
        'produits': models.Produit
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def calculate_similarity_score(str1: str, str2: str) -> float:
        """Calcule un score de similarité entre deux chaînes"""
        try:
            return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
        except:
            return 0.0
    
    def find_matching_items_for_group(
        self, 
        search_value: str, 
        group_name: str, 
        fpack_groups: List[Dict], 
        client_id: int = None
    ) -> List[Dict]:
        """Trouve les items correspondants pour un groupe"""
        target_group = self._find_group_by_name(fpack_groups, group_name)
        if not target_group:
            return []
        
        matches = []
        search_value_lower = search_value.lower()
        
        for table_name, model_class in self.SEARCH_TABLES.items():
            try:
                items = self._search_in_table(model_class, search_value, client_id)
                
                for item in items:
                    matches.append({
                        'id': item.id,
                        'nom': item.nom,
                        'type': table_name,
                        'client_id': getattr(item, 'client_id', None),
                        'score': self.calculate_similarity_score(search_value_lower, item.nom.lower())
                    })
                    
            except Exception as e:
                print(f"Erreur lors de la recherche dans {table_name}: {e}")
                continue
        
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:MAX_MATCHES]
    
    def _find_group_by_name(self, fpack_groups: List[Dict], group_name: str) -> Optional[Dict]:
        """Trouve un groupe par nom (insensible à la casse)"""
        for group in fpack_groups:
            if group['nom'].lower() == group_name.lower():
                return group
        return None
    
    def _search_in_table(self, model_class, search_value: str, client_id: int = None) -> List:
        """Effectue une recherche dans une table spécifique"""
        query = self.db.query(model_class)
        
        if client_id and hasattr(model_class, 'client_id'):
            query = query.filter(model_class.client_id == client_id)
        
        return query.filter(model_class.nom.ilike(f"%{search_value}%")).limit(MAX_MATCHES).all()
    
    def get_suggestions_for_group(
        self, 
        search_value: str, 
        group_name: str, 
        fpack_groups: List[Dict], 
        client_id: int = None
    ) -> List[Dict]:
        """Obtient des suggestions pour un groupe"""
        matches = self.find_matching_items_for_group(search_value, group_name, fpack_groups, client_id)
        
        if len(matches) < MAX_SUGGESTIONS and client_id:
            additional_matches = self.find_matching_items_for_group(search_value, group_name, fpack_groups, None)
            for match in additional_matches:
                if not any(m['id'] == match['id'] and m['type'] == match['type'] for m in matches):
                    match['from_other_client'] = True
                    matches.append(match)
        
        return matches[:MAX_SUGGESTIONS]

# Processeurs de données
class DataProcessor:
    """Processeur principal des données d'import"""
    
    def __init__(self, db: Session):
        self.db = db
        self.db_cache = DatabaseCache(db)
        self.matching_engine = MatchingEngine(db)
        self.mapper = DataMapper()
    
    def process_row_for_preview(
        self, 
        row_data: Dict, 
        fpack_config: Dict, 
        mapping_config: Dict,
        row_index: int
    ) -> Tuple[Dict, List[Dict]]:
        """Traite une ligne pour l'aperçu"""
        result = ProcessingResult()
        processed_row = dict(row_data)
        unmatched_items = []
        
        template_id = fpack_config["selectedFPackTemplate"]
        client_id = fpack_config["clientId"]
        
        # Récupération des groupes du template
        fpack_groups = self.db_cache.get_fpack_template_groups(template_id)
        
        # Configuration de mapping
        subproject_columns = mapping_config.get("subproject_columns", {})
        groups_config = mapping_config.get("groups", [])
        excel_column_to_group = self.mapper.build_excel_to_group_mapping(groups_config)
        
        # Traitement des colonnes
        self._process_columns_for_preview(
            row_data, row_index, excel_column_to_group, 
            subproject_columns, fpack_groups, client_id, 
            template_id, result, unmatched_items
        )
        
        # Validation des champs obligatoires
        self._validate_required_fields(row_data, subproject_columns, result)
        
        # Finalisation du statut
        if result.warnings and result.status == "success":
            result.status = "warning"
        
        processed_row.update({
            '_status': result.status,
            '_errors': result.errors,
            '_warnings': result.warnings,
            '_client_id': client_id,
            '_template_id': template_id
        })
        
        return processed_row, unmatched_items
    
    def _process_columns_for_preview(
        self, 
        row_data: Dict, 
        row_index: int, 
        excel_column_to_group: Dict, 
        subproject_columns: Dict,
        fpack_groups: List[Dict], 
        client_id: int, 
        template_id: int, 
        result: ProcessingResult, 
        unmatched_items: List[Dict]
    ):
        """Traite les colonnes pour l'aperçu"""
        for excel_column, cell_value in row_data.items():
            if excel_column.startswith('_') or not str(cell_value).strip():
                continue
            
            cell_value = str(cell_value).strip()
            excel_column_lower = excel_column.lower()
            
            # Vérification colonne de sous-projet
            if self._is_subproject_column(excel_column_lower, subproject_columns):
                continue
            
            # Vérification colonne de groupe
            if excel_column_lower in excel_column_to_group:
                self._process_group_column(
                    excel_column, cell_value, excel_column_to_group[excel_column_lower],
                    fpack_groups, client_id, template_id, row_index, result, unmatched_items
                )
    
    def _is_subproject_column(self, excel_column_lower: str, subproject_columns: Dict) -> bool:
        """Vérifie si c'est une colonne de sous-projet mappée"""
        for dest_field, excel_col in subproject_columns.items():
            if excel_col.lower() == excel_column_lower:
                return True
        return False
    
    def _process_group_column(
        self, 
        excel_column: str, 
        cell_value: str, 
        group_name: str,
        fpack_groups: List[Dict], 
        client_id: int, 
        template_id: int, 
        row_index: int,
        result: ProcessingResult, 
        unmatched_items: List[Dict]
    ):
        """Traite une colonne de groupe"""
        target_group = next((g for g in fpack_groups if g['nom'] == group_name), None)
        
        if not target_group:
            result.warnings.append(f"Groupe '{group_name}' non trouvé dans le template")
            return
        
        try:
            matches = self.matching_engine.find_matching_items_for_group(
                cell_value, group_name, fpack_groups, client_id
            )
            
            if not matches:
                suggestions = self.matching_engine.get_suggestions_for_group(
                    cell_value, group_name, fpack_groups, client_id
                )
                
                unmatched_items.append({
                    "id": f"{row_index}_{excel_column}",
                    "value": cell_value,
                    "column": excel_column,
                    "group_name": group_name,
                    "client_id": client_id,
                    "fpack_template_id": template_id,
                    "suggestions": suggestions,
                    "type": "group"
                })
                
                result.warnings.append(
                    f"Aucune correspondance pour '{cell_value}' dans le groupe '{group_name}' (colonne '{excel_column}')"
                )
        except Exception as e:
            result.warnings.append(
                f"Erreur lors du traitement du groupe '{group_name}' (colonne '{excel_column}'): {str(e)}"
            )
    
    def _validate_required_fields(self, row_data: Dict, subproject_columns: Dict, result: ProcessingResult):
        """Valide les champs obligatoires"""
        fpack_number = self.mapper.get_mapped_field_value(row_data, subproject_columns, 'fpack_number')
        
        if not fpack_number:
            # Essayer avec des variantes
            for variant in ['FPack_number', 'fpack_Number', 'FPACK_NUMBER']:
                fpack_number = self.mapper.get_mapped_field_value(row_data, subproject_columns, variant)
                if fpack_number:
                    break
        
        if not fpack_number:
            result.status = "error"
            result.errors.append("FPack Number est requis mais non trouvé dans le mapping")

# Routes principales optimisées
@router.post("/import/upload")
async def upload_import_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Étape 1 : Upload et analyse initiale du fichier Excel"""
    try:
        # Validation du fichier
        if not file.filename.endswith(SUPPORTED_EXTENSIONS):
            raise HTTPException(
                status_code=400,
                detail=f"Format non supporté. Utilisez: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
        
        # Lecture du fichier
        content = await file.read()
        
        try:
            df = pd.read_excel(BytesIO(content), sheet_name=REQUIRED_SHEET_NAME, header=HEADER_ROW)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"L'onglet '{REQUIRED_SHEET_NAME}' est introuvable"
            )
        
        # Traitement des données
        df = clean_dataframe_data(df)
        valid_rows = get_valid_rows(df)
        preview_rows = valid_rows[:MAX_PREVIEW_ROWS]
        
        return {
            "success": True,
            "columns": df.columns.tolist(),
            "preview": preview_rows,
            "total_valid_rows": len(valid_rows),
            "message": f"Fichier analysé : {len(valid_rows)} lignes valides, {len(df.columns)} colonnes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de l'analyse : {str(e)}")

@router.post("/import/preview")
async def preview_import(data: Dict[str, Any], db: Session = Depends(get_db)):
    """Étape 2 : Aperçu avec mapping et validation"""
    try:
        # Validation des champs requis
        validate_required_fields(data, ["preview_data", "mapping_config", "fpack_configurations"])
        
        preview_data = data["preview_data"]
        mapping_config = data["mapping_config"]
        fpack_configurations = data["fpack_configurations"]
        
        # Validations supplémentaires
        if not isinstance(mapping_config, dict):
            raise HTTPException(status_code=400, detail="mapping_config doit être un dictionnaire")
        
        if not isinstance(fpack_configurations, list):
            raise HTTPException(status_code=400, detail="fpack_configurations doit être une liste")
        
        if len(fpack_configurations) != len(preview_data):
            raise HTTPException(
                status_code=400,
                detail=f"Nombre de configurations ({len(fpack_configurations)}) != nombre de lignes ({len(preview_data)})"
            )
        
        # Traitement avec le processeur optimisé
        processor = DataProcessor(db)
        processed_data = []
        all_unmatched_items = []
        
        for row_index, (row_data, fpack_config) in enumerate(zip(preview_data, fpack_configurations)):
            processed_row, unmatched_items = processor.process_row_for_preview(
                row_data, fpack_config, mapping_config, row_index
            )
            processed_data.append(processed_row)
            all_unmatched_items.extend(unmatched_items)
        
        # Calcul des statistiques
        summary = calculate_preview_summary(processed_data, fpack_configurations, mapping_config, processor.db_cache)
        
        return {
            "success": True,
            "processed_data": processed_data,
            "unmatched_items": all_unmatched_items,
            "summary": summary,
            "mapping_config_used": {
                "name": mapping_config.get("name", "Configuration sans nom"),
                "subproject_columns_count": len(mapping_config.get("subproject_columns", {})),
                "groups_count": len(mapping_config.get("groups", []))
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur dans preview_import: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

def calculate_preview_summary(processed_data: List[Dict], fpack_configurations: List[Dict], mapping_config: Dict, db_cache: DatabaseCache) -> Dict:
    """Calcule les statistiques de l'aperçu"""
    subproject_columns = mapping_config.get("subproject_columns", {})
    groups_config = mapping_config.get("groups", [])
    
    unique_template_ids = list(set(config["selectedFPackTemplate"] for config in fpack_configurations))
    templates_cache = db_cache.get_templates_batch(unique_template_ids)
    
    return {
        "nb_fpacks": len([row for row in processed_data if row['_status'] != 'error']),
        "nb_selections_potentielles": sum(1 for row in processed_data if row['_status'] in ['success', 'warning']),
        "colonnes_mappables": build_mappable_columns_info(subproject_columns, groups_config),
        "clients_count": len(set(config["clientId"] for config in fpack_configurations)),
        "templates_used": [
            {
                "id": template_id,
                "nom": templates_cache[template_id]['template'].nom,
                "count": sum(1 for c in fpack_configurations if c["selectedFPackTemplate"] == template_id)
            }
            for template_id in unique_template_ids if template_id in templates_cache
        ],
        "subproject_columns_mapped": len(subproject_columns),
        "groups_mapped": len(groups_config)
    }

def build_mappable_columns_info(subproject_columns: Dict, groups_config: List[Dict]) -> List[Dict]:
    """Construit les informations sur les colonnes mappables"""
    mappable_columns = []
    
    # Colonnes de sous-projet
    for dest_field, excel_column in subproject_columns.items():
        mappable_columns.append({
            "column": excel_column,
            "type": "subproject_field",
            "target": dest_field,
            "mapped_via": "json_config"
        })
    
    # Colonnes de groupe
    for group_config in groups_config:
        if "excel_column" in group_config and "group_name" in group_config:
            mappable_columns.append({
                "column": group_config["excel_column"],
                "type": "group",
                "target": group_config["group_name"],
                "mapped_via": "json_config"
            })
    
    return mappable_columns

@router.post("/import/execute")
async def execute_import(data: Dict[str, Any], db: Session = Depends(get_db)):
    """Exécution de l'import avec optimisations"""
    try:
        # Validation des champs requis
        validate_required_fields(data, ["file_data", "mapping_config", "fpack_configurations"])
        
        # Nettoyage des données
        file_data = clean_import_data(data["file_data"])
        mapping_config = data["mapping_config"]
        fpack_configurations = data["fpack_configurations"]
        manual_matches = data.get("manual_matches", [])
        
        # Validation des configurations
        validate_fpack_configurations(fpack_configurations)
        
        # Traitement de l'import
        executor = ImportExecutor(db)
        stats = executor.execute_import(
            file_data, mapping_config, fpack_configurations, manual_matches
        )
        
        # Résultat final
        if stats.errors:
            db.rollback()
            return {
                "success": False,
                "detail": f"Import échoué avec {len(stats.errors)} erreurs",
                "results": stats.__dict__
            }
        else:
            db.commit()
            return {
                "success": True,
                "results": stats.__dict__,
                "message": f"Import réalisé : {stats.created_fpacks} F-Packs créés, {stats.created_selections} sélections"
            }
            
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"Erreur dans execute_import: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

class ImportExecutor:
    """Exécuteur d'import optimisé"""
    
    def __init__(self, db: Session):
        self.db = db
        self.db_cache = DatabaseCache(db)
        self.matching_engine = MatchingEngine(db)
        self.mapper = DataMapper()
    
    def execute_import(
        self, 
        file_data: List[Dict], 
        mapping_config: Dict, 
        fpack_configurations: List[Dict],
        manual_matches: List[Dict]
    ) -> ImportStats:
        """Exécute l'import complet"""
        stats = ImportStats()
        
        # Préparation des données
        subproject_columns = mapping_config.get("subproject_columns", {})
        excel_column_to_group = self.mapper.build_excel_to_group_mapping(mapping_config.get("groups", []))
        manual_matches_dict = self._build_manual_matches_dict(manual_matches)
        
        # Cache des groupes de templates
        self._preload_template_groups([config["selectedFPackTemplate"] for config in fpack_configurations])
        
        # Traitement ligne par ligne
        for row_index, (row_data, fpack_config) in enumerate(zip(file_data, fpack_configurations)):
            try:
                self._process_import_row(
                    row_index, row_data, fpack_config, subproject_columns,
                    excel_column_to_group, manual_matches_dict, stats
                )
            except Exception as e:
                stats.errors.append(f"Ligne {row_index + 1}: {str(e)}")
                continue
        
        # Calcul des projets uniques
        stats.created_projects = len(set(config["selectedProjetGlobal"] for config in fpack_configurations))
        
        return stats
    
    def _build_manual_matches_dict(self, manual_matches: List[Dict]) -> Dict[str, Dict]:
        """Construit le dictionnaire des correspondances manuelles"""
        matches_dict = {}
        for match in manual_matches:
            row_idx = match.get("row_index")
            column = match.get("column")
            if row_idx is not None and column:
                key = f"{row_idx}_{column}"
                matches_dict[key] = match.get("selectedMatch")
        return matches_dict
    
    def _preload_template_groups(self, template_ids: List[int]):
        """Précharge les groupes des templates"""
        unique_template_ids = list(set(template_ids))
        self.db_cache.get_templates_batch(unique_template_ids)
    
    def _process_import_row(
        self, 
        row_index: int, 
        row_data: Dict, 
        fpack_config: Dict,
        subproject_columns: Dict, 
        excel_column_to_group: Dict, 
        manual_matches_dict: Dict,
        stats: ImportStats
    ):
        """Traite une ligne d'import"""
        sous_projet_id = fpack_config["selectedSousProjet"]
        template_id = fpack_config["selectedFPackTemplate"]
        client_id = fpack_config["clientId"]
        
        # Vérification du sous-projet
        sous_projet = self.db.query(models.SousProjet).filter(
            models.SousProjet.id == sous_projet_id
        ).first()
        
        if not sous_projet:
            raise Exception(f"Sous-projet {sous_projet_id} non trouvé")
        
        # Création du F-Pack
        fpack_data = self._build_fpack_data(row_data, subproject_columns)
        new_fpack = models.SousProjetFpack(
            **fpack_data,
            sous_projet_id=sous_projet_id,
            fpack_id=template_id
        )
        
        self.db.add(new_fpack)
        self.db.flush()
        stats.created_fpacks += 1
        
        # Traitement des sélections
        self._process_selections(
            row_index, row_data, new_fpack.id, template_id, client_id,
            excel_column_to_group, manual_matches_dict, stats
        )
    
    def _build_fpack_data(self, row_data: Dict, subproject_columns: Dict) -> Dict[str, str]:
        """Construit les données F-Pack depuis le mapping"""
        fpack_data = {}
        
        # Mapping des champs de sous-projet
        for dest_field, excel_column in subproject_columns.items():
            value = self.mapper.get_field_value_case_insensitive(row_data, excel_column)
            if value:
                # Conversion des noms de champs pour le modèle
                if dest_field == "fpack_number":
                    fpack_data["FPack_number"] = value
                elif dest_field == "robot_location_code":
                    fpack_data["Robot_Location_Code"] = value
                else:
                    fpack_data[dest_field] = value
        
        # Valeurs par défaut pour les champs requis
        return {
            "FPack_number": fpack_data.get("FPack_number", ""),
            "Robot_Location_Code": fpack_data.get("Robot_Location_Code", ""),
            "contractor": fpack_data.get("contractor", ""),
            "required_delivery_time": fpack_data.get("required_delivery_time", ""),
            "delivery_site": fpack_data.get("delivery_site", ""),
            "tracking": fpack_data.get("tracking", ""),
            **fpack_data
        }
    
    def _process_selections(
        self, 
        row_index: int, 
        row_data: Dict, 
        fpack_id: int,
        template_id: int, 
        client_id: int, 
        excel_column_to_group: Dict,
        manual_matches_dict: Dict, 
        stats: ImportStats
    ):
        """Traite les sélections pour une ligne"""
        template_groups = self.db_cache.get_fpack_template_groups(template_id)
        
        for excel_column_lower, group_name in excel_column_to_group.items():
            # Trouver la colonne Excel originale
            original_excel_column = self._find_original_column(row_data, excel_column_lower)
            if not original_excel_column:
                continue
            
            cell_value = self.mapper.get_field_value_case_insensitive(row_data, original_excel_column)
            if not cell_value:
                continue
            
            # Recherche de correspondance
            selected_item = self._get_selected_item(
                row_index, original_excel_column, cell_value, group_name,
                template_groups, client_id, manual_matches_dict
            )
            
            if selected_item:
                self._create_selection(
                    fpack_id, group_name, selected_item, template_groups, stats
                )
            else:
                stats.warnings.append(
                    f"Ligne {row_index + 1}, groupe '{group_name}': "
                    f"Aucune correspondance pour '{cell_value}'"
                )
    
    def _find_original_column(self, row_data: Dict, excel_column_lower: str) -> Optional[str]:
        """Trouve la colonne Excel originale par recherche insensible à la casse"""
        for original_col in row_data.keys():
            if original_col.lower() == excel_column_lower:
                return original_col
        return None
    
    def _get_selected_item(
        self, 
        row_index: int, 
        excel_column: str, 
        cell_value: str,
        group_name: str, 
        template_groups: List[Dict], 
        client_id: int,
        manual_matches_dict: Dict
    ) -> Optional[Dict]:
        """Récupère l'item sélectionné (manuel ou automatique)"""
        match_key = f"{row_index}_{excel_column}"
        
        # Vérification correspondance manuelle
        if match_key in manual_matches_dict:
            return manual_matches_dict[match_key]
        
        # Recherche automatique
        matches = self.matching_engine.find_matching_items_for_group(
            cell_value, group_name, template_groups, client_id
        )
        return matches[0] if matches else None
    
    def _create_selection(
        self, 
        fpack_id: int, 
        group_name: str, 
        selected_item: Dict,
        template_groups: List[Dict], 
        stats: ImportStats
    ):
        """Crée une sélection dans la base"""
        try:
            target_group = next((g for g in template_groups if g['nom'] == group_name), None)
            
            if target_group:
                new_selection = models.SousProjetFpackSelection(
                    sous_projet_fpack_id=fpack_id,
                    groupe_id=target_group['id'],
                    groupe_nom=group_name,
                    type_item=selected_item.get('type', 'unknown'),
                    ref_id=selected_item['id'],
                    item_nom=selected_item['nom']
                )
                
                self.db.add(new_selection)
                stats.created_selections += 1
            else:
                stats.warnings.append(f"Groupe '{group_name}' non trouvé dans le template")
        
        except Exception as e:
            stats.warnings.append(f"Erreur création sélection groupe '{group_name}': {str(e)}")

# Fonctions utilitaires optimisées
def clean_import_data(file_data: List[Dict]) -> List[Dict]:
    """Nettoie les données d'import"""
    if not isinstance(file_data, list):
        return file_data
    
    cleaned_data = []
    for row in file_data:
        if isinstance(row, dict):
            cleaned_row = {}
            for key, value in row.items():
                cleaned_key = clean_text(key) if isinstance(key, str) else key
                cleaned_value = clean_text(value) if isinstance(value, str) else value
                cleaned_row[cleaned_key] = cleaned_value
            cleaned_data.append(cleaned_row)
        else:
            cleaned_data.append(row)
    
    return cleaned_data

def validate_fpack_configurations(fpack_configurations: List[Dict]) -> None:
    """Valide les configurations F-Pack"""
    if not isinstance(fpack_configurations, list):
        raise HTTPException(status_code=400, detail="fpack_configurations doit être une liste")
    
    required_config_fields = ["selectedProjetGlobal", "selectedSousProjet", "selectedFPackTemplate", "clientId"]
    
    for i, config in enumerate(fpack_configurations):
        for field in required_config_fields:
            if field not in config:
                raise HTTPException(
                    status_code=400,
                    detail=f"Configuration F-Pack {i}: champ requis manquant '{field}'"
                )

# Routes utilitaires optimisées avec cache
@router.get("/import/sous-projets")
async def get_available_sous_projets(db: Session = Depends(get_db)):
    """Récupère la liste des sous-projets avec jointure optimisée"""
    try:
        # Requête optimisée avec jointure
        sous_projets = db.query(models.SousProjet)\
            .join(models.SousProjet.global_rel, isouter=True)\
            .all()
        
        return {
            "success": True,
            "sous_projets": [
                {
                    "id": sp.id,
                    "nom": sp.nom,
                    "projet_global": sp.global_rel.projet if sp.global_rel else "N/A"
                }
                for sp in sous_projets
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur : {str(e)}")

@router.get("/import/fpack-templates")
async def get_available_fpack_templates(db: Session = Depends(get_db)):
    """Récupère la liste des templates F-Pack avec jointure optimisée"""
    try:
        # Requête optimisée avec jointure
        fpacks = db.query(models.FPack)\
            .join(models.FPack.client_relfpack, isouter=True)\
            .all()
        
        return {
            "success": True,
            "fpack_templates": [
                {
                    "id": fp.id,
                    "nom": fp.nom,
                    "client": fp.client_relfpack.nom if fp.client_relfpack else "N/A",
                    "abbreviation": fp.fpack_abbr
                }
                for fp in fpacks
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur : {str(e)}")

@router.get("/import/fpack-template/{fpack_id}/groups")
async def get_fpack_template_groups_endpoint(fpack_id: int, db: Session = Depends(get_db)):
    """Récupère les groupes d'un template F-Pack avec cache"""
    try:
        db_cache = DatabaseCache(db)
        groups = db_cache.get_fpack_template_groups(fpack_id)
        
        return {
            "success": True,
            "groups": groups
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur : {str(e)}")

# Nouvelles routes pour optimiser les performances
@router.post("/import/validate-config")
async def validate_import_config(config_data: Dict[str, Any], db: Session = Depends(get_db)):
    """Valide une configuration d'import sans traiter les données"""
    try:
        validate_required_fields(config_data, ["mapping_config", "fpack_configurations"])
        
        mapping_config = config_data["mapping_config"]
        fpack_configurations = config_data["fpack_configurations"]
        
        # Validations rapides
        if not isinstance(mapping_config, dict):
            raise HTTPException(status_code=400, detail="mapping_config invalide")
        
        validate_fpack_configurations(fpack_configurations)
        
        # Vérification des templates et sous-projets
        validation_results = await _validate_references(fpack_configurations, db)
        
        return {
            "success": True,
            "validation_results": validation_results,
            "message": "Configuration validée avec succès"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de validation: {str(e)}")

async def _validate_references(fpack_configurations: List[Dict], db: Session) -> Dict:
    """Valide les références vers les sous-projets et templates"""
    # Extraire les IDs uniques
    sous_projet_ids = list(set(config["selectedSousProjet"] for config in fpack_configurations))
    template_ids = list(set(config["selectedFPackTemplate"] for config in fpack_configurations))
    
    # Vérification en batch des sous-projets
    existing_sous_projets = db.query(models.SousProjet.id)\
        .filter(models.SousProjet.id.in_(sous_projet_ids))\
        .all()
    existing_sous_projet_ids = {sp.id for sp in existing_sous_projets}
    
    # Vérification en batch des templates
    existing_templates = db.query(models.FPack.id)\
        .filter(models.FPack.id.in_(template_ids))\
        .all()
    existing_template_ids = {t.id for t in existing_templates}
    
    # Identification des références manquantes
    missing_sous_projets = set(sous_projet_ids) - existing_sous_projet_ids
    missing_templates = set(template_ids) - existing_template_ids
    
    return {
        "valid_sous_projets": len(existing_sous_projet_ids),
        "missing_sous_projets": list(missing_sous_projets),
        "valid_templates": len(existing_template_ids),
        "missing_templates": list(missing_templates),
        "all_references_valid": len(missing_sous_projets) == 0 and len(missing_templates) == 0
    }

@router.get("/import/stats")
async def get_import_stats(db: Session = Depends(get_db)):
    """Récupère les statistiques générales d'import"""
    try:
        stats = {
            "total_sous_projets": db.query(models.SousProjet).count(),
            "total_fpack_templates": db.query(models.FPack).count(),
            "total_groups": db.query(models.Groupes).count(),
            "total_robots": db.query(models.Robots).count(),
            "total_equipements": db.query(models.Equipement).count(),
            "total_produits": db.query(models.Produit).count()
        }
        
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur : {str(e)}")