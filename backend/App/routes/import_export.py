from fastapi import APIRouter, Depends, HTTPException 
from sqlalchemy.orm import Session 
from App.database import SessionLocal
from sqlalchemy import inspect 
from sqlalchemy.orm import selectinload
from App.export_fpack_to_excel import export_fpack_config, export_all_fpacks
from fastapi.responses import StreamingResponse
from io import BytesIO
import os
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from App.routes.projets import get_projet_facture

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#EXPORT FPACK TO EXCEL
@router.post("/export-fpack/{fpack_id}")
def export_fpack(fpack_id: int, db: Session = Depends(get_db)):
    wb = export_fpack_config(fpack_id, db)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    headers = {
        'Content-Disposition': f'attachment; filename="F-Pack-{fpack_id}.xlsx"'
    }

    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

@router.get("/export-fpacks/all")
def export_all_fpacks_route(db: Session = Depends(get_db)):
    wb = export_all_fpacks(db)
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    headers = {
        'Content-Disposition': 'attachment; filename="FPacks-All.xlsx"'
    }

    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)


#FACTURE PROJET

@router.get("/projets/{id}/facture-pdf")
def export_projet_facture_pdf(id: int, db: Session = Depends(get_db)):
    facture = get_projet_facture(id, db)
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4)

    elements = []
    styles = getSampleStyleSheet()

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(BASE_DIR, "frontend", "assets", "FANUCLOGO.jpg")
    if os.path.exists(logo_path):
        img = Image(logo_path, width=100, height=40)
        elements.append(img)

    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"<b>FACTURE - {facture['nom_projet']}</b>", styles['Title']))
    elements.append(Spacer(1, 12))

    data = [["Produit", "Quantité", "Prix Unité", "Transport", "Commentaire", "Total ligne"]]
    for ligne in facture["lines"]:
        data.append([
            ligne.get("nom", ""),
            ligne.get("qte", 0),
            f"{ligne.get('prix_produit', 0)} €",
            f"{ligne.get('prix_transport', 0)} €",
            ligne.get("commentaire", ""),
            f"{ligne.get('total_ligne', 0)} €"
        ])

    table = Table(data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.yellow),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.red),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 24))

    for label, value in facture["totaux"].items():
        elements.append(Paragraph(f"<b>{label.title()} :</b> {value} €", styles['Normal']))

    doc.build(elements)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="facture-projet-{id}.pdf"'}
    )

@router.get("/projets/{id}/facture-excel")
def export_projet_facture_excel(id: int, db: Session = Depends(get_db)):
    facture = get_projet_facture(id, db)
    wb = Workbook()
    ws = wb.active
    ws.title = "Facture Projet"

    ws.merge_cells("C2:F2")
    cell = ws["C2"]
    cell.value = f"FACTURE - {facture['nom_projet']}"
    cell.font = Font(size=14, bold=True)
    cell.alignment = Alignment(horizontal="center")

    headers = ["Produit", "Quantité", "Prix Unité", "Transport", "Commentaire", "Total ligne"]
    ws.append([""] * len(headers))  
    ws.append(headers)
    header_row = ws.max_row
    header_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=header_row, column=col)
        cell.font = Font(bold=True, color="AA0000")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    for ligne in facture["lines"]:
        ws.append([
            ligne.get("nom", ""),
            ligne.get("qte", 0),
            float(ligne.get("prix_produit") or 0),
            float(ligne.get("prix_transport") or 0),
            ligne.get("commentaire", ""),
            float(ligne.get("total_ligne") or 0)
        ])

    ws.append([])
    ws.append(["", "", "", "", "Total produit", facture["totaux"]["produit"]])
    ws.append(["", "", "", "", "Total transport", facture["totaux"]["transport"]])
    ws.append(["", "", "", "", "Total global", facture["totaux"]["global"]])

    for i in range(1, 8):
        ws.column_dimensions[chr(64 + i)].width = 25

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="facture-projet-{id}.xlsx"'}
    )
