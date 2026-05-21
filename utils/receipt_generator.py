"""
PDF Receipt Generator for Le Schéma School
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics import renderPDF
import qrcode
from datetime import datetime
from io import BytesIO


ORANGE = colors.HexColor("#FF6B00")
DARK = colors.HexColor("#1a1a2e")
GRAY = colors.HexColor("#64748b")
LIGHT_GRAY = colors.HexColor("#f8fafc")
WHITE = colors.white


def generate_qr_code(data, size=80):
    qr = qrcode.QRCode(version=1, box_size=3, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def generate_receipt(payment_data, student_data, settings, output_path):
    """
    Generate a professional PDF receipt
    
    payment_data: dict with payment info
    student_data: dict with student info
    settings: dict with school settings
    output_path: where to save the PDF
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A5,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )

    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "title", fontName="Helvetica-Bold", fontSize=18,
        textColor=ORANGE, alignment=TA_CENTER, spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        "subtitle", fontName="Helvetica", fontSize=9,
        textColor=GRAY, alignment=TA_CENTER, spaceAfter=2
    )
    header_style = ParagraphStyle(
        "header", fontName="Helvetica-Bold", fontSize=11,
        textColor=WHITE, alignment=TA_CENTER
    )
    normal_style = ParagraphStyle(
        "normal_custom", fontName="Helvetica", fontSize=9,
        textColor=DARK, spaceAfter=3
    )
    bold_style = ParagraphStyle(
        "bold_custom", fontName="Helvetica-Bold", fontSize=10,
        textColor=DARK
    )
    amount_style = ParagraphStyle(
        "amount", fontName="Helvetica-Bold", fontSize=16,
        textColor=ORANGE, alignment=TA_CENTER
    )

    # ─── HEADER ───
    logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "school_logo.png")
    
    header_data = []
    if os.path.exists(logo_path):
        logo = RLImage(logo_path, width=22*mm, height=22*mm)
        header_data = [[logo, [
            Paragraph(settings.get("school_name", "Le Schéma"), title_style),
            Paragraph(settings.get("school_slogan", "Innover - Créer - Exceller"), subtitle_style),
            Paragraph(settings.get("school_phone", ""), subtitle_style),
            Paragraph(settings.get("school_email", ""), subtitle_style),
        ]]]
        header_table = Table(header_data, colWidths=[25*mm, 105*mm])
    else:
        story.append(Paragraph(settings.get("school_name", "Le Schéma"), title_style))
        story.append(Paragraph(settings.get("school_slogan", ""), subtitle_style))
        header_table = None

    if header_table:
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ]))
        story.append(header_table)

    story.append(Spacer(1, 3*mm))

    # Receipt title banner
    receipt_title_data = [[Paragraph("REÇU DE PAIEMENT", header_style)]]
    receipt_title_table = Table(receipt_title_data, colWidths=[130*mm])
    receipt_title_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ORANGE),
        ("ROUNDEDCORNERS", [5]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(receipt_title_table)
    story.append(Spacer(1, 4*mm))

    # Receipt number and date
    receipt_num = payment_data.get("receipt_number", "REC-2026-000001")
    payment_date = payment_data.get("payment_date", datetime.now())
    if isinstance(payment_date, str):
        payment_date_str = payment_date
    else:
        payment_date_str = payment_date.strftime("%d/%m/%Y %H:%M")

    meta_data = [
        [Paragraph(f"<b>N° Reçu:</b> {receipt_num}", normal_style),
         Paragraph(f"<b>Date:</b> {payment_date_str}", normal_style)],
    ]
    meta_table = Table(meta_data, colWidths=[65*mm, 65*mm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, GRAY),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 4*mm))

    # Student information
    story.append(Paragraph("INFORMATIONS ÉLÈVE", ParagraphStyle(
        "section_title", fontName="Helvetica-Bold", fontSize=9,
        textColor=ORANGE, spaceAfter=3
    )))

    student_name = f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}"
    student_info = [
        ["Nom complet:", student_name, "Classe:", student_data.get("class_name", "")],
        ["Code élève:", student_data.get("student_code", ""), "Parent:", student_data.get("parent_name", "")],
    ]
    student_table = Table(student_info, colWidths=[28*mm, 40*mm, 20*mm, 42*mm])
    student_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 0), (0, -1), GRAY),
        ("TEXTCOLOR", (2, 0), (2, -1), GRAY),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
    ]))
    story.append(student_table)
    story.append(Spacer(1, 4*mm))

    # Payment details
    story.append(Paragraph("DÉTAILS DU PAIEMENT", ParagraphStyle(
        "section_title2", fontName="Helvetica-Bold", fontSize=9,
        textColor=ORANGE, spaceAfter=3
    )))

    payment_type_labels = {
        "monthly": "Frais Mensuel",
        "insurance": "Assurance Annuelle",
        "transport": "Transport Mensuel",
    }
    ptype = payment_data.get("payment_type", "monthly")
    ptype_label = payment_type_labels.get(ptype, ptype.capitalize())
    month_year = ""
    if payment_data.get("month"):
        month_year = f" - {payment_data['month']} {payment_data.get('year', '')}"

    payment_details = [
        ["Type de paiement:", f"{ptype_label}{month_year}"],
        ["Montant payé:", f"{payment_data.get('amount', 0):.2f} {settings.get('currency', 'MAD')}"],
    ]
    if payment_data.get("notes"):
        payment_details.append(["Notes:", payment_data["notes"]])

    payment_table = Table(payment_details, colWidths=[40*mm, 90*mm])
    payment_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
    ]))
    story.append(payment_table)
    story.append(Spacer(1, 4*mm))

    # Total amount highlighted
    amount = payment_data.get("amount", 0)
    currency = settings.get("currency", "MAD")
    story.append(Paragraph(f"TOTAL: {amount:.2f} {currency}", amount_style))
    story.append(Spacer(1, 5*mm))

    # QR Code and signature section
    qr_data = f"RECEIPT:{receipt_num}|STUDENT:{student_data.get('student_code', '')}|AMOUNT:{amount}|DATE:{payment_date_str}"
    qr_buffer = generate_qr_code(qr_data)
    qr_image = RLImage(qr_buffer, width=22*mm, height=22*mm)

    sig_style = ParagraphStyle("sig", fontName="Helvetica", fontSize=8, textColor=GRAY, alignment=TA_CENTER)
    footer_data = [
        [qr_image, Spacer(1, 1), Paragraph("Signature & Cachet\n\n\n_________________", sig_style)],
        [Paragraph("Scannez pour vérifier", sig_style), "", ""],
    ]
    footer_table = Table(footer_data, colWidths=[30*mm, 40*mm, 60*mm])
    footer_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("SPAN", (0, 0), (0, 0)),
    ]))
    story.append(footer_table)

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "Ce reçu est un document officiel. Veuillez le conserver.",
        ParagraphStyle("footer_note", fontName="Helvetica-Oblique", fontSize=7.5, textColor=GRAY, alignment=TA_CENTER)
    ))

    doc.build(story)
    return output_path


if __name__ == "__main__":
    # Test receipt generation
    settings = {
        "school_name": "Le Schéma",
        "school_slogan": "Innover - Créer - Exceller",
        "school_phone": "+212 000-000000",
        "school_email": "contact@leschema.ma",
        "currency": "MAD"
    }
    student = {
        "first_name": "Ahmed",
        "last_name": "Benali",
        "student_code": "STU-2026-001",
        "class_name": "CM1",
        "parent_name": "Mohamed Benali"
    }
    payment = {
        "receipt_number": "REC-2026-000001",
        "payment_type": "monthly",
        "amount": 500.00,
        "payment_date": datetime.now(),
        "month": "Mai",
        "year": 2026,
        "notes": ""
    }
    out = generate_receipt(payment, student, settings, "/tmp/test_receipt.pdf")
    print(f"Receipt generated: {out}")
