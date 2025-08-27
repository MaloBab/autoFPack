from App import models
from App.database import SessionLocal
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends #type: ignore
from sqlalchemy.orm import Session #type: ignore
from typing import List, Dict, Any, Optional
import pandas as pd #type: ignore
import traceback
from pydantic import BaseModel #type: ignore
from fuzzywuzzy import fuzz #type: ignore
from io import BytesIO

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/import/upload")
async def upload_import_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Étape 1 : Upload et analyse initiale du fichier Excel
    """
    try:
        # Vérifier le type de fichier
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Format de fichier non supporté. Utilisez .xlsx ou .xls"
            )
        
        # Lire le contenu binaire du fichier
        content = await file.read()

        # Lire uniquement l'onglet "F-Pack Matrix"
        try:
            df = pd.read_excel(BytesIO(content), sheet_name="F-Pack Matrix", header=4)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="L'onglet 'F-Pack Matrix' est introuvable dans le fichier Excel"
            )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erreur lors de la lecture du fichier Excel: {str(e)}"
            )
        
        # Nettoyer les colonnes
        df.columns = df.columns.str.strip()
        
        valid_rows = []
        for index, row in df.iterrows():
            first_cell = str(row.iloc[0]).strip().lower() if pd.notna(row.iloc[0]) else ""
            if first_cell and first_cell != "total":
                row_dict = row.fillna('').to_dict()
                row_dict['_row_index'] = index
                valid_rows.append(row_dict)
        

        preview_rows = valid_rows[:5]
        
        return {
            "success": True,
            "columns": df.columns.tolist(),
            "preview": preview_rows,
            "total_valid_rows": len(valid_rows),
            "message": f"Fichier analysé : {len(valid_rows)} lignes valides, {len(df.columns)} colonnes"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de l'analyse du fichier : {str(e)}")


@router.post("/import/preview")
async def preview_import(
    data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Étape 2 : Aperçu avec mapping et validation - Support multi-clients
    Utilise des dictionnaires génériques sans modèles Pydantic spécifiques
    """
    try:
        # Validation des champs requis
        required_fields = ["preview_data", "mapping_config", "fpack_configurations"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Champ requis manquant: {field}")
        
        preview_data = data["preview_data"]
        mapping_config = data["mapping_config"]
        fpack_configurations = data["fpack_configurations"]
        
        # Validation des configurations F-Pack
        if not isinstance(fpack_configurations, list):
            raise HTTPException(status_code=400, detail="fpack_configurations doit être une liste")
        
        for i, config in enumerate(fpack_configurations):
            required_config_fields = ["selectedProjetGlobal", "selectedSousProjet", "selectedFPackTemplate", "clientId"]
            for field in required_config_fields:
                if field not in config:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Configuration F-Pack {i}: champ requis manquant '{field}'"
                    )
        
        # Vérifier que nous avons le même nombre de configurations que de lignes
        if len(fpack_configurations) != len(preview_data):
            raise HTTPException(
                status_code=400, 
                detail=f"Nombre de configurations ({len(fpack_configurations)}) != nombre de lignes ({len(preview_data)})"
            )
        
        # Variables pour les résultats
        processed_data = []
        all_unmatched_items = []
        summary = {
            "nb_fpacks": 0, 
            "nb_selections_potentielles": 0,
            "colonnes_mappables": [],
            "clients_count": 0,
            "templates_used": []
        }
        
        # Cache des templates pour éviter les requêtes répétées
        unique_template_ids = list(set(config["selectedFPackTemplate"] for config in fpack_configurations))
        templates_cache = {}
        
        for template_id in unique_template_ids:
            fpack_template = db.query(models.FPack).filter(
                models.FPack.id == template_id
            ).first()
            
            if not fpack_template:
                raise HTTPException(status_code=404, detail=f"Template F-Pack {template_id} non trouvé")
            
            templates_cache[template_id] = {
                'template': fpack_template,
                'groups': get_fpack_template_groups(template_id, db)
            }
        
        # Traitement ligne par ligne
        for row_index, (row_data, fpack_config) in enumerate(zip(preview_data, fpack_configurations)):
            processed_row = dict(row_data)  # Copie du dictionnaire
            status = "success"
            errors = []
            warnings = []
            
            # Récupération des informations du template
            template_id = fpack_config["selectedFPackTemplate"]
            template_info = templates_cache[template_id]
            fpack_groups = template_info['groups']
            group_names = [group['nom'] for group in fpack_groups]
            client_id = fpack_config["clientId"]
            
            # Analyse des colonnes
            for column_name, cell_value in row_data.items():
                if column_name.startswith('_') or not str(cell_value).strip():
                    continue
                
                cell_value = str(cell_value).strip()
                
                # Champs directs mappables
                direct_fields = [
                    'FPack_number', 'Robot_Location_Code', 'contractor',
                    'required_delivery_time', 'delivery_site', 'tracking'
                ]
                
                is_direct_field = (
                    column_name in direct_fields or 
                    any(field.lower() in column_name.lower() for field in direct_fields)
                )
                
                if is_direct_field:
                    # Éviter les doublons dans les colonnes mappables
                    if not any(col["column"] == column_name for col in summary["colonnes_mappables"]):
                        summary["colonnes_mappables"].append({
                            "column": column_name,
                            "type": "direct_field",
                            "target": column_name
                        })
                
                # Groupes du template F-Pack
                elif column_name in group_names:
                    try:
                        # Recherche de correspondances
                        matches = find_matching_items_for_group(
                            cell_value, column_name, fpack_groups, db, client_id
                        )
                        
                        if not matches:
                            suggestions = get_suggestions_for_group(
                                cell_value, column_name, fpack_groups, db, client_id
                            )
                            
                            all_unmatched_items.append({
                                "id": f"{row_index}_{column_name}",
                                "value": cell_value,
                                "column": column_name,
                                "group_name": column_name,
                                "client_id": client_id,
                                "fpack_template_id": template_id,
                                "suggestions": suggestions
                            })
                            warnings.append(f"Aucune correspondance pour '{cell_value}' dans '{column_name}'")
                        else:
                            summary["nb_selections_potentielles"] += 1
                        
                        # Ajouter aux colonnes mappables
                        if not any(col["column"] == column_name for col in summary["colonnes_mappables"]):
                            summary["colonnes_mappables"].append({
                                "column": column_name,
                                "type": "group",
                                "target": column_name,
                                "matches_found": len(matches) if matches else 0
                            })
                    
                    except Exception as e:
                        warnings.append(f"Erreur lors du traitement de '{column_name}': {str(e)}")
            
            # Validation des champs obligatoires
            if not get_cell_value_by_field(row_data, 'FPack_number'):
                status = "error"
                errors.append("FPack_number est requis")
            
            # Détermination du statut final
            if warnings and status == "success":
                status = "warning"
            
            # Enrichissement des données traitées
            processed_row.update({
                '_status': status,
                '_errors': errors,
                '_warnings': warnings,
                '_client_id': client_id,
                '_template_id': template_id
            })
            
            processed_data.append(processed_row)
        
        # Calcul des statistiques finales
        summary.update({
            "nb_fpacks": len([row for row in processed_data if row['_status'] != 'error']),
            "clients_count": len(set(config["clientId"] for config in fpack_configurations)),
            "templates_used": [
                {
                    "id": template_id,
                    "nom": templates_cache[template_id]['template'].nom,
                    "count": sum(1 for c in fpack_configurations if c["selectedFPackTemplate"] == template_id)
                }
                for template_id in unique_template_ids
            ]
        })
        
        # Groupes disponibles (tous les groupes de tous les templates)
        available_groups = list(set(
            group['nom']
            for template_info in templates_cache.values()
            for group in template_info['groups']
        ))
        
        return {
            "success": True,
            "processed_data": processed_data,
            "unmatched_items": all_unmatched_items,
            "summary": summary,
            "available_groups": available_groups
        }
        
    except HTTPException:
        # Re-lever les HTTPException telles quelles
        raise
    except Exception as e:
        # Logger l'erreur complète pour le débogage
        print(f"Erreur dans preview_import: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur interne du serveur: {str(e)}"
        )
        
@router.post("/import/execute")
async def execute_import(
    data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Exécution de l'import - Support multi-clients sans modèles Pydantic
    """
    try:
        # Validation des champs requis
        required_fields = ["file_data", "mapping_config", "fpack_configurations"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Champ requis manquant: {field}")
        
        file_data = data["file_data"]
        mapping_config = data["mapping_config"]
        fpack_configurations = data["fpack_configurations"]
        manual_matches = data.get("manual_matches", [])
        
        # Validation des configurations F-Pack
        if not isinstance(fpack_configurations, list):
            raise HTTPException(status_code=400, detail="fpack_configurations doit être une liste")
        
        for i, config in enumerate(fpack_configurations):
            required_config_fields = ["selectedProjetGlobal", "selectedSousProjet", "selectedFPackTemplate", "clientId"]
            for field in required_config_fields:
                if field not in config:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Configuration F-Pack {i}: champ requis manquant '{field}'"
                    )
        
        # Statistiques de l'import
        stats = {
            "created_projects": 0,
            "created_fpacks": 0,
            "created_selections": 0,
            "errors": [],
            "warnings": []
        }
        
        # Traitement des correspondances manuelles
        manual_matches_dict = {}
        for match in manual_matches:
            row_idx = match.get("row_index")
            column = match.get("column")
            if row_idx is not None and column:
                key = f"{row_idx}_{column}"
                manual_matches_dict[key] = match.get("selectedMatch")
        
        # Traitement ligne par ligne
        for row_index, (row_data, fpack_config) in enumerate(zip(file_data, fpack_configurations)):
            try:
                sous_projet_id = fpack_config["selectedSousProjet"]
                template_id = fpack_config["selectedFPackTemplate"]
                client_id = fpack_config["clientId"]
                
                # Vérification que le sous-projet existe
                sous_projet = db.query(models.SousProjet).filter(
                    models.SousProjet.id == sous_projet_id
                ).first()
                
                if not sous_projet:
                    stats["errors"].append(f"Ligne {row_index + 1}: Sous-projet {sous_projet_id} non trouvé")
                    continue
                
                # Création du SousProjetFpack
                fpack_data = {

                    "FPack_number": get_cell_value_by_field(row_data, "FPack_number") or "",
                    "Robot_Location_Code": get_cell_value_by_field(row_data, "Robot_Location_Code") or "",
                    "contractor": get_cell_value_by_field(row_data, "contractor"),
                    "required_delivery_time": get_cell_value_by_field(row_data, "required_delivery_time"),
                    "delivery_site": get_cell_value_by_field(row_data, "delivery_site"),
                    "tracking": get_cell_value_by_field(row_data, "tracking")
                }
                
                print(row_data)
                
                # Création du F-Pack dans la base
                new_fpack = models.SousProjetFpack(
                    **fpack_data,
                    sous_projet_id=sous_projet_id,
                    fpack_id=template_id
                )
                
                db.add(new_fpack)
                db.flush()  # Pour obtenir l'ID
                
                stats["created_fpacks"] += 1
                
                # Traitement des sélections (groupes)
                template_groups = get_fpack_template_groups(template_id, db)
                group_names = [group['nom'] for group in template_groups]
                
                for column_name, cell_value in row_data.items():
                    if column_name in group_names and str(cell_value).strip():
                        cell_value = str(cell_value).strip()
                        match_key = f"{row_index}_{column_name}"
                        
                        # Utiliser la correspondance manuelle si disponible
                        selected_item = manual_matches_dict.get(match_key)
                        
                        if not selected_item:
                            # Recherche automatique de correspondance
                            matches = find_matching_items_for_group(
                                cell_value, column_name, template_groups, db, client_id
                            )
                            if matches:
                                selected_item = matches[0]  # Prendre le meilleur match
                        
                        if selected_item:
                            try:
                                # Trouver le groupe correspondant
                                target_group = None
                                for group in template_groups:
                                    if group['nom'] == column_name:
                                        target_group = group
                                        break
                                
                                if target_group:
                                    # Créer la sélection
                                    new_selection = models.SousProjetFpackSelection(
                                        sous_projet_fpack_id=new_fpack.id,
                                        groupe_id=target_group['id'],
                                        groupe_nom=column_name,
                                        type_item=selected_item.get('type', 'unknown'),
                                        ref_id=selected_item['id'],
                                        item_nom=selected_item['nom']
                                    )
                                    
                                    db.add(new_selection)
                                    stats["created_selections"] += 1
                                
                            except Exception as e:
                                stats["warnings"].append(
                                    f"Ligne {row_index + 1}, colonne '{column_name}': Erreur lors de la création de la sélection: {str(e)}"
                                )
                        else:
                            stats["warnings"].append(
                                f"Ligne {row_index + 1}, colonne '{column_name}': Aucune correspondance trouvée pour '{cell_value}'"
                            )
                
            except Exception as e:
                stats["errors"].append(f"Ligne {row_index + 1}: Erreur lors du traitement: {str(e)}")
                continue
        
        # Compter les projets uniques créés/modifiés
        unique_projects = set(config["selectedProjetGlobal"] for config in fpack_configurations)
        stats["created_projects"] = len(unique_projects)
        
        # Validation finale et commit
        if stats["errors"]:
            db.rollback()
            return {
                "success": False,
                "detail": f"Import échoué avec {len(stats['errors'])} erreurs",
                "results": stats
            }
        else:
            db.commit()
            return {
                "success": True,
                "results": stats,
                "message": f"Import réalisé avec succès: {stats['created_fpacks']} F-Packs créés"
            }
            
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"Erreur dans execute_import: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne du serveur: {str(e)}"
        )
# Fonctions utilitaires

def get_fpack_template_groups(fpack_id: int, db: Session) -> List[Dict]:
    """Récupère les groupes configurés pour un template F-Pack"""
    try:
        # Récupérer les colonnes de configuration du F-Pack
        config_columns = db.query(models.FPackConfigColumn).filter(
            models.FPackConfigColumn.fpack_id == fpack_id,
            models.FPackConfigColumn.type == 'group'
        ).order_by(models.FPackConfigColumn.ordre).all()
        
        groups = []
        for config_col in config_columns:
            if config_col.ref_id:
                groupe = db.query(models.Groupes).filter(
                    models.Groupes.id == config_col.ref_id
                ).first()
                
                if groupe:
                    # Récupérer les items du groupe
                    groupe_items = db.query(models.GroupeItem).filter(
                        models.GroupeItem.group_id == groupe.id
                    ).all()
                    
                    groups.append({
                        "id": groupe.id,
                        "nom": groupe.nom,
                        "items": groupe_items,
                        "ordre": config_col.ordre
                    })
        
        return groups
        
    except Exception as e:
        return []

def find_matching_items_for_group(
    search_value: str, 
    group_name: str, 
    fpack_groups: List[Dict], 
    db: Session,
    client_id: int = None
) -> List[Dict]:
    """Trouve les items correspondants pour un groupe"""
    try:
        # Trouver le groupe cible
        target_group = None
        for group in fpack_groups:
            if group['nom'] == group_name:
                target_group = group
                break
        
        if not target_group:
            return []
        
        matches = []
        
        # Tables de recherche
        search_tables = {
            'robots': models.Robot,
            'equipements': models.Equipement, 
            'produits': models.Produit
        }
        
        for table_name, model_class in search_tables.items():
            try:
                query = db.query(model_class)
                
                # Filtrage par client si applicable et disponible
                if client_id and hasattr(model_class, 'client_id'):
                    query = query.filter(model_class.client_id == client_id)
                
                # Recherche par nom (case-insensitive)
                items = query.filter(model_class.nom.ilike(f"%{search_value}%")).limit(10).all()
                
                for item in items:
                    matches.append({
                        'id': item.id,
                        'nom': item.nom,
                        'type': table_name,
                        'client_id': getattr(item, 'client_id', None),
                        'score': calculate_similarity_score(search_value, item.nom)
                    })
                    
            except Exception as e:
                print(f"Erreur lors de la recherche dans {table_name}: {e}")
                continue
        
        # Tri par score de similarité
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:10]
        
    except Exception as e:
        print(f"Erreur dans find_matching_items_for_group: {e}")
        return []

        

def calculate_similarity_score(str1: str, str2: str) -> float:
    """Calcule un score de similarité entre deux chaînes"""
    try:
        from difflib import SequenceMatcher
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    except:
        return 0.0


def get_suggestions_for_group(
    search_value: str, 
    group_name: str, 
    fpack_groups: List[Dict], 
    db: Session,
    client_id: int = None,
    limit: int = 5
) -> List[Dict]:
    """Obtient des suggestions pour un groupe"""
    try:
        # Recherche avec le client spécifique
        matches = find_matching_items_for_group(search_value, group_name, fpack_groups, db, client_id)
        
        # Si pas assez de résultats, recherche sans filtre client
        if len(matches) < limit and client_id:
            additional_matches = find_matching_items_for_group(search_value, group_name, fpack_groups, db, None)
            for match in additional_matches:
                if not any(m['id'] == match['id'] and m['type'] == match['type'] for m in matches):
                    match['from_other_client'] = True
                    matches.append(match)
        
        return matches[:limit]
        
    except Exception as e:
        print(f"Erreur dans get_suggestions_for_group: {e}")
        return []


def get_cell_value_by_field(row_data: Dict[str, Any], field_name: str) -> Any:
    """Récupère la valeur d'un champ dans les données de ligne"""
    # Recherche directe
    if field_name in row_data:
        return row_data[field_name]
    
    # Recherche case-insensitive
    for key, value in row_data.items():
        if key.lower() == field_name.lower():
            return value
    
    # Recherche partielle
    for key, value in row_data.items():
        if field_name.lower() in key.lower():
            return value
    
    return None

def get_item_by_type_and_id(item_type: str, item_id: int, db: Session) -> Dict:
    """Récupère un item selon son type et son ID"""
    try:
        if item_type == "produits":
            item = db.query(models.Produit).filter(models.Produit.id == item_id).first()
        elif item_type == "equipements":
            item = db.query(models.Equipements).filter(models.Equipements.id == item_id).first()
        elif item_type == "robots":
            item = db.query(models.Robots).filter(models.Robots.id == item_id).first()
        else:
            return {}
        
        if item:
            return {
                "id": item.id,
                "nom": getattr(item, 'nom', ''),
                "description": getattr(item, 'description', ''),
                "reference": getattr(item, 'reference', ''),
                "type": item_type
            }
        
        return {}
        
    except Exception as e:
        return {}

def create_sous_projet_fpack_entry(row_data: Dict, sous_projet_id: int, fpack_id: int, 
                                  column_mapping: Dict, db: Session):
    """Crée une entrée SousProjetFpack depuis une ligne de données"""
    try:
        # Extraire les valeurs des champs directs
        fpack_data = {}
        
        direct_fields = ['FPack_number', 'Robot_Location_Code', 'contractor', 
                        'required_delivery_time', 'delivery_site', 'tracking']
        
        for field in direct_fields:
            value = get_cell_value_by_field(row_data, field, column_mapping)
            if value:
                fpack_data[field] = value
        
        # Vérifier que FPack_number est présent
        if not fpack_data.get('FPack_number'):
            raise ValueError("FPack_number est requis")
        
        # Créer l'entrée
        sous_projet_fpack = models.SousProjetFpack(
            sous_projet_id=sous_projet_id,
            fpack_id=fpack_id,
            FPack_number=fpack_data.get('FPack_number', ''),
            Robot_Location_Code=fpack_data.get('Robot_Location_Code', ''),
            contractor=fpack_data.get('contractor', 'N/A'),
            required_delivery_time=fpack_data.get('required_delivery_time', 'N/A'),
            delivery_site=fpack_data.get('delivery_site', 'N/A'),
            tracking=fpack_data.get('tracking', 'N/A')
        )
        
        db.add(sous_projet_fpack)
        db.flush()
        return sous_projet_fpack
        
    except Exception as e:
        raise ValueError(f"Erreur création entrée F-Pack: {str(e)}")

def get_cell_value_by_field(row_data: Dict, field_name: str, column_mapping: Dict = None) -> str:
    """Extrait une valeur de cellule selon le nom du champ"""
    try:
        # Si un mapping explicite existe
        if column_mapping and field_name in column_mapping:
            column_name = column_mapping[field_name]
            return str(row_data.get(column_name, "")).strip()
        
        # Chercher par nom exact
        if field_name in row_data:
            return str(row_data[field_name]).strip()
        
        # Chercher par correspondance partielle (insensible à la casse)
        for column_name in row_data.keys():
            if field_name.lower() in column_name.lower():
                return str(row_data[column_name]).strip()
        
        return ""
        
    except Exception as e:
        return ""

async def create_selections_from_row(row_data: Dict, row_index: int, sous_projet_fpack_id: int,
                                   fpack_groups: List[Dict], group_name_to_id: Dict,
                                   manual_matches: Dict, db: Session):
    """Crée les sélections depuis une ligne de données"""
    selections_created = []
    
    try:
        for column_name, cell_value in row_data.items():
            if column_name.startswith('_') or not str(cell_value).strip():
                continue
            
            cell_value = str(cell_value).strip()
            
            # Vérifier si cette colonne correspond à un groupe
            if column_name not in group_name_to_id:
                continue
            
            groupe_id = group_name_to_id[column_name]
            
            # Vérifier s'il y a une correspondance manuelle
            match_key = f"{row_index}_{column_name}"
            selected_item = manual_matches.get(match_key)
            
            if not selected_item:
                # Chercher automatiquement
                matches = await find_matching_items_for_group(
                    cell_value, column_name, fpack_groups, db
                )
                if matches:
                    selected_item = matches[0]  # Prendre le meilleur match
            
            if selected_item:
                # Créer la sélection
                selection = models.ProjetSelection(
                    sous_projet_fpack_id=sous_projet_fpack_id,
                    groupe_id=groupe_id,
                    type_item=selected_item['type'],
                    ref_id=selected_item['id']
                )
                
                db.add(selection)
                selections_created.append(selection)
        
        db.flush()
        return selections_created
        
    except Exception as e:
        raise e

# Routes utilitaires pour le frontend

@router.get("/import/sous-projets")
async def get_available_sous_projets(db: Session = Depends(get_db)):
    """Récupère la liste des sous-projets disponibles"""
    try:
        sous_projets = db.query(models.SousProjet).all()
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
    """Récupère la liste des templates F-Pack disponibles"""
    try:
        fpacks = db.query(models.FPack).all()
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
    """Récupère les groupes d'un template F-Pack"""
    try:
        groups = get_fpack_template_groups(fpack_id, db)
        return {
            "success": True,
            "groups": groups
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur : {str(e)}")