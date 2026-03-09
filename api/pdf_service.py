"""
Service for generating PDF reports for real estate properties.
"""

import os
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_pdf_report(
    properties: list,
    conversation_summary: str = "",
    client_criteria: dict = None,
    output_dir: str = "/tmp"
) -> str:
    """
    Generate a professional PDF report for properties.
    
    Args:
        properties: List of property dictionaries
        conversation_summary: Summary of the conversation
        client_criteria: Criteria used for search
        output_dir: Directory to save the PDF
    
    Returns:
        Path to the generated PDF file
    """
    
    if client_criteria is None:
        client_criteria = {}
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rapport_immobilier_{timestamp}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    # Create PDF document
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=30,
        alignment=TA_CENTER,
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2d5aa8'),
        spaceAfter=12,
        spaceBefore=12,
    )
    
    # Title
    story.append(Paragraph("📋 NidBot - Rapport d'Analyse Immobilière", title_style))
    story.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    # Client Criteria Section
    if client_criteria:
        story.append(Paragraph("Critères de Recherche", heading_style))
        criteria_data = [["Critère", "Valeur"]]
        for key, value in client_criteria.items():
            criteria_data.append([key.replace("_", " ").title(), str(value)])
        
        criteria_table = Table(criteria_data, colWidths=[2 * inch, 3 * inch])
        criteria_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d5aa8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(criteria_table)
        story.append(Spacer(1, 0.2 * inch))
    
    # Conversation Summary
    if conversation_summary:
        story.append(Paragraph("Résumé de la Consultation", heading_style))
        story.append(Paragraph(conversation_summary, styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))
    
    # Properties Table
    if properties:
        story.append(Paragraph(f"Propriétés Sélectionnées ({len(properties)} bien(s))", heading_style))
        
        # Create properties table
        prop_data = [[
            "Adresse",
            "Type",
            "Surface",
            "Pièces",
            "Prix",
            "€/m²",
            "État"
        ]]
        
        for prop in properties:
            undervalued_text = "✅ Sous-évalué" if prop.get("is_undervalued") else "Normal"
            prop_data.append([
                prop.get("address", "N/A"),
                prop.get("type", "N/A"),
                f"{prop.get('surface', 'N/A')}m²",
                str(prop.get("rooms", "N/A")),
                f"{prop.get('price', 0):,.0f}€",
                f"{prop.get('price_per_m2', 0):,.0f}€",
                undervalued_text,
            ])
        
        prop_table = Table(prop_data, colWidths=[1.8*inch, 0.8*inch, 0.8*inch, 0.6*inch, 1*inch, 0.8*inch, 1*inch])
        prop_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d5aa8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        story.append(prop_table)
        story.append(Spacer(1, 0.3 * inch))
    
    # Footer
    story.append(Spacer(1, 0.5 * inch))
    footer_text = "Ce rapport a été généré par NidBot - Conseiller Immobilier IA.<br/>Pour plus d'informations, consultez l'application."
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    try:
        doc.build(story)
        return filepath
    except Exception as e:
        print(f"Erreur lors de la génération du PDF: {e}")
        raise
