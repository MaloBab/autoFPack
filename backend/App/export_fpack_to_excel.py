import logging
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session
from App import models

# === Configuration du logger ===
logger = logging.getLogger("fpack_export")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("export_fpack.log", mode="w", encoding="utf-8")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(file_handler)


# === Utilitaire pour récupérer le nom lisible d’un item ===
def get_item_label(type_: str, ref_id: int, db: Session) -> str:
    try:
        if type_ == "produit":
            item = db.query(models.Produit).filter_by(id=ref_id).first()
            return item.nom if item else f"Produit {ref_id}"
        elif type_ == "equipement":
            item = db.query(models.Equipements).filter_by(id=ref_id).first()
            return item.nom if item else f"Équipement {ref_id}"
        elif type_ == "robot":
            item = db.query(models.Robots).filter_by(id=ref_id).first()
            return item.nom if item else f"Robot {ref_id}"
        else:
            return f"{type_} {ref_id}"
    except Exception as e:
        logger.error(f"[ERREUR get_item_label] type={type_}, ref_id={ref_id} → {e}")
        return f"{type_} {ref_id}"


# === Fonction interne d’export vers un onglet ===
def export_fpack_to_sheet(fpack_id: int, db: Session, ws):
    fpack = db.query(models.FPack).filter(models.FPack.id == fpack_id).first()
    ws.title = f"{fpack.nom[:31]} - {fpack.fpack_abbr}"

    ws["A1"].value = "F-Pack Matrix"
    ws["A2"].value = f"Nom: {fpack.nom}"
    ws["A3"].value = f"Abbr: {fpack.fpack_abbr}"
    ws["A4"].value = "Généré automatiquement"

    config_columns = (
        db.query(models.FPackConfigColumn)
        .filter(models.FPackConfigColumn.fpack_id == fpack_id)
        .order_by(models.FPackConfigColumn.ordre)
        .all()
    )

    for row in range(1, 5):
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=len(config_columns) + 3)
        cell = ws.cell(row=row, column=1)
        cell.font = Font(bold=True, size=14)
        cell.alignment = Alignment(horizontal="center")

    col_index = 1
    nb_col_groupes = 0

    for col in config_columns:
        if col.type != "group":
            continue

        groupe = db.query(models.Groupes).filter_by(id=col.ref_id).first()
        group_items = db.query(models.GroupeItem).filter_by(group_id=col.ref_id).all()

        options = [get_item_label(item.type, item.ref_id, db) for item in group_items if item]
        options = options[:30]

        header = ws.cell(row=5, column=col_index)
        header.value = groupe.nom if groupe else f"Groupe {col.ref_id}"
        header.font = Font(bold=True)
        header.alignment = Alignment(horizontal="center")
        header.fill = PatternFill("solid", fgColor="FFCC99")

        dv = DataValidation(type="list", formula1=f'"{','.join(options)}"')
        ws.add_data_validation(dv)
        row = 6
        dv.add(ws.cell(row=row, column=col_index))

        ws.column_dimensions[get_column_letter(col_index)].width = 24
        col_index += 1
        nb_col_groupes += 1

    produits_seuls = []
    equipements_seuls = []

    for col in config_columns:
        if col.type == "produit":
            item = db.query(models.Produit).filter_by(id=col.ref_id).first()
            produits_seuls.append(item.nom if item else f"Produit {col.ref_id}")
        elif col.type == "equipement":
            item = db.query(models.Equipements).filter_by(id=col.ref_id).first()
            equipements_seuls.append(item.nom if item else f"Équipement {col.ref_id}")

    ligne_depart = 5
    col_equipements = nb_col_groupes + 3
    col_produits = nb_col_groupes + 4

    header = ws.cell(row=ligne_depart, column=col_produits, value="Produits")
    header.font = Font(bold=True, color="FFFFFF")
    header.fill = PatternFill("solid", fgColor="4472C4")
    ws.column_dimensions[get_column_letter(col_produits)].width = 30
    for i, nom in enumerate(produits_seuls, start=1):
        ws.cell(row=ligne_depart + i, column=col_produits, value=nom)

    header = ws.cell(row=ligne_depart, column=col_equipements, value="Équipements")
    header.font = Font(bold=True, color="FFFFFF")
    header.fill = PatternFill("solid", fgColor="70AD47")
    ws.column_dimensions[get_column_letter(col_equipements)].width = 30
    for i, nom in enumerate(equipements_seuls, start=1):
        ws.cell(row=ligne_depart + i, column=col_equipements, value=nom)

    ws.freeze_panes = "A6"


# === Export d'une seule FPack (pour export individuel, bouton) ===
def export_fpack_config(fpack_id: int, db: Session) -> Workbook:
    wb = Workbook()
    ws = wb.active
    export_fpack_to_sheet(fpack_id, db, ws)
    return wb


# === Export de toutes les FPack dans un seul fichier ===
def export_all_fpacks(db: Session) -> Workbook:
    wb = Workbook()
    wb.remove(wb.active)

    fpacks = db.query(models.FPack).all()
    for fpack in fpacks:
        ws = wb.create_sheet()
        export_fpack_to_sheet(fpack.id, db, ws)

    logger.info(f"Export multiple terminé : {len(fpacks)} FPack dans un seul fichier.")
    return wb
