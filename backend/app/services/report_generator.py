import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.units import cm
from reportlab.platypus.flowables import HRFlowable

from . import redaction_pges as redaction


def generate_pges_pdf(chantiers_data, start_date, end_date, entreprise_destinataire="ANDE"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'MainTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=18,
        textColor=colors.HexColor('#004F9F'),
        alignment=1, spaceAfter=20, leading=22
    )
    
    subtitle_style = ParagraphStyle(
        'SubTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=14,
        alignment=1, spaceAfter=15, leading=16
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=11,
        alignment=1, spaceAfter=10
    )
    
    box_style = ParagraphStyle(
        'BoxStyle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=12,
        alignment=1, leading=16,
        textColor=colors.black,
        backColor=colors.HexColor('#C5E0B3'),
        borderPadding=(15, 15, 15, 15)
    )
    
    normal_center = ParagraphStyle(
        'NormalCenter', parent=styles['Normal'],
        fontName='Helvetica', fontSize=11,
        alignment=1, spaceAfter=10
    )
    
    h2_style = ParagraphStyle(
        'H2', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=14,
        textColor=colors.HexColor('#004F9F'), spaceBefore=15, spaceAfter=10
    )

    h3_style = ParagraphStyle(
        'H3', parent=styles['Heading3'],
        fontName='Helvetica-Bold', fontSize=12,
        textColor=colors.HexColor('#18181B'), spaceBefore=10, spaceAfter=5
    )

    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10.5,
        textColor=colors.HexColor('#3F3F46'),
        alignment=4, spaceAfter=8, leading=15
    )

    story = []
    
    # --- PAGE DE GARDE ---
    story.append(Paragraph("MINISTERE DE L'EQUIPEMENT ET DE L'ENTRETIEN ROUTIER", header_style))
    story.append(Paragraph("----------------------", normal_center))
    story.append(Paragraph("AGENCE DE GESTION DES ROUTES (AGEROUTE)", header_style))
    story.append(Spacer(1, 1.5*cm))
    
    story.append(Paragraph("PROJET DE TRANSPORT URBAIN D'ABIDJAN<br/>------------------ PTUA -------------------", box_style))
    story.append(Spacer(1, 1.5*cm))
    
    # Le document produit ici n'est pas un PGES. Le Plan de Gestion
    # Environnementale et Sociale est un document de planification, etabli en
    # amont avec l'etude d'impact : il fixe les mesures d'attenuation, les
    # responsabilites, le programme de surveillance et son budget. Ce que le
    # systeme genere rend compte de sa mise en oeuvre sur une periode donnee.
    # Le PGES reste donc le referentiel cite, non le titre du rapport.
    story.append(Paragraph("RAPPORT DE SUIVI<br/>ENVIRONNEMENTAL ET SOCIAL", title_style))
    story.append(Spacer(1, 1*cm))

    story.append(Paragraph("MISE EN &Oelig;UVRE DU PLAN DE GESTION "
                           "ENVIRONNEMENTALE ET SOCIALE (PGES)", subtitle_style))
    story.append(Spacer(1, 0.5*cm))
    
    period_str = f"P\u00e9riode: {start_date} au {end_date}" if start_date and end_date else "P\u00e9riode Globale"
    date_str = datetime.now().strftime("%B %Y").capitalize()
    
    date_style = ParagraphStyle(
        'DateStyle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=12,
        textColor=colors.HexColor('#C62828'), alignment=2, spaceAfter=20
    )
    story.append(Paragraph(period_str, normal_center))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(date_str, date_style))
    story.append(Paragraph("Rapport final", subtitle_style))
    story.append(Spacer(1, 2*cm))
    
    story.append(Paragraph("PREPARE PAR : SI-ENV AUTOMATED SYSTEM", header_style))
    story.append(Paragraph(f"DESTINATAIRE : {entreprise_destinataire}", header_style))

    story.append(PageBreak())
    
    # --- SOMMAIRE ---
    # Un rapport remis a une tutelle se parcourt rarement de bout en bout : le
    # lecteur cherche une section precise. Le sommaire est donc construit a
    # partir du perimetre reel, chaque chantier y figurant nommement.
    story.append(Paragraph("SOMMAIRE", h2_style))
    story.append(HRFlowable(width='100%', thickness=1,
                            color=colors.HexColor('#004F9F'), spaceAfter=12))

    entrees = [
        ("1.", "Contexte et objectifs du suivi"),
        ("2.", "Synth\u00e8se de la p\u00e9riode"),
        ("3.", "Situation par chantier"),
    ]
    for i, ch in enumerate(chantiers_data, start=1):
        libelle = ch['nom']
        if ch.get('commune'):
            libelle += f" ({ch['commune']})"
        entrees.append((f"3.{i}", libelle))
    entrees.append(("4.", "Conclusion et recommandations"))

    sommaire_style = ParagraphStyle(
        'Sommaire', parent=styles['Normal'],
        fontName='Helvetica', fontSize=11,
        textColor=colors.HexColor('#3F3F46'), leading=20,
    )
    sommaire_sous_style = ParagraphStyle(
        'SommaireSous', parent=sommaire_style,
        fontSize=10, leftIndent=18,
        textColor=colors.HexColor('#71717A'),
    )
    for numero, libelle in entrees:
        style = sommaire_sous_style if numero.count('.') > 1 else sommaire_style
        story.append(Paragraph(f"<b>{numero}</b>&nbsp;&nbsp;{libelle}", style))

    story.append(Spacer(1, 0.6*cm))
    story.append(Paragraph(
        "Ce rapport est \u00e9tabli \u00e0 partir des donn\u00e9es consign\u00e9es dans le syst\u00e8me "
        "d'information environnemental de l'AGEROUTE. Les effectifs indiqu\u00e9s "
        "correspondent aux enregistrements horodat\u00e9s sur la p\u00e9riode retenue.",
        ParagraphStyle('NoteSommaire', parent=body_style,
                       fontSize=9.5, textColor=colors.HexColor('#71717A')),
    ))
    story.append(PageBreak())

    # --- INTRODUCTION ---
    story.append(Paragraph("1. CONTEXTE ET OBJECTIFS DU SUIVI", h2_style))
    story.append(Paragraph(
        redaction.introduction(chantiers_data, start_date, end_date,
                               entreprise_destinataire),
        body_style,
    ))
    story.append(Spacer(1, 0.3*cm))

    # --- SYNTHESE ---
    story.append(Paragraph("2. SYNTHESE DE LA PERIODE", h2_style))
    # Le commentaire precede les chiffres : il indique au lecteur ce qu'il doit
    # y chercher, alors qu'un tableau seul le laisse face a des volumes bruts.
    story.append(Paragraph(
        redaction.synthese(chantiers_data, start_date, end_date), body_style,
    ))
    story.append(Spacer(1, 0.4*cm))
    
    total_sig = sum(c.get('nb_signalements', 0) for c in chantiers_data)
    total_alertes = sum(c.get('nb_alertes', 0) for c in chantiers_data)
    total_plaintes = sum(c.get('nb_plaintes', 0) for c in chantiers_data)
    total_nc = sum(c.get('nb_non_conformites', 0) for c in chantiers_data)
    
    summary_data = [
        ['Indicateur', 'Total', 'Statut'],
        ['Signalements environnementaux', str(total_sig), 'Enregistr\u00e9'],
        ['Alertes (capteurs/IoT)', str(total_alertes), 'Surveill\u00e9'],
        ['Plaintes communautaires (MGP)', str(total_plaintes), 'Suivi PAP/BAD'],
        ['Non-conformit\u00e9s (inspections)', str(total_nc), 'Contr\u00f4l\u00e9'],
    ]
    
    t_summary = Table(summary_data, colWidths=[10*cm, 3*cm, 4*cm])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#004F9F')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F8F9')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E4E4E7')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 0.5*cm))
    
    # --- MATRICE DES DONNEES ---
    story.append(Paragraph("3. SITUATION PAR CHANTIER", h2_style))
    
    for index, chantier in enumerate(chantiers_data, start=1):
        story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#E4E4E7'), spaceBefore=4, spaceAfter=8))
        commune = chantier.get('commune') or 'commune non renseignée'
        story.append(Paragraph(f"3.{index}. {chantier['nom']} ({commune})", h3_style))
        # Le commentaire ouvre la sous-section : le lecteur sait ce que les
        # tableaux qui suivent vont confirmer.
        story.append(Paragraph(redaction.commentaire_chantier(chantier), body_style))
        story.append(Spacer(1, 0.25*cm))
        
        # Table of metrics for this chantier
        data = [
            ['Indicateur', 'Valeur / Quantit\u00e9', 'Tendance'],
            ['Signalements Environnementaux', str(chantier.get('nb_signalements', 0)), '\u25cf'],
            ['Alertes (Capteurs/IoT)', str(chantier.get('nb_alertes', 0)), '\u25cf'],
            ['Plaintes Communautaires', str(chantier.get('nb_plaintes', 0)), '\u25cf'],
            ['Non-Conformit\u00e9s (Inspections)', str(chantier.get('nb_non_conformites', 0)), '\u25cf']
        ]
        
        t = Table(data, colWidths=[9*cm, 4*cm, 4*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#004F9F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F4F4F5')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E4E4E7')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4*cm))
        
        # Details des signalements
        if chantier.get('signalements_details'):
            story.append(Paragraph("D\u00e9tail des derniers signalements:", ParagraphStyle('Sub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#004F9F'))))
            sig_data = [['Type', 'Description', 'Statut', 'Date']] + [[s['type'], str(s.get('desc', ''))[:50], s['statut'], s.get('date', '')] for s in chantier['signalements_details']]
            t_sig = Table(sig_data, colWidths=[3.5*cm, 7.5*cm, 3*cm, 3*cm])
            t_sig.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEF1F8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#004F9F')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(t_sig)
            story.append(Spacer(1, 0.4*cm))
            
        # Details des plaintes
        if chantier.get('plaintes_details'):
            story.append(Paragraph("D\u00e9tail des derni\u00e8res plaintes (MGP):", ParagraphStyle('Sub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#F37021'))))
            pl_data = [['Plaignant', 'Description', 'Statut', 'Date']] + [[p['nom'], str(p.get('desc', ''))[:50], p['statut'], p.get('date', '')] for p in chantier['plaintes_details']]
            t_pl = Table(pl_data, colWidths=[3.5*cm, 7.5*cm, 3*cm, 3*cm])
            t_pl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FEF3E8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#F37021')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(t_pl)
        
        story.append(Spacer(1, 0.8*cm))
        
    # --- CONCLUSION ---
    story.append(Paragraph("4. CONCLUSION ET RECOMMANDATIONS", h2_style))
    # Les recommandations decoulent des chiffres constates : un rapport ou
    # tout est clos ne peut pas se conclure comme un rapport ou des
    # non-conformites restent ouvertes.
    story.append(Paragraph(
        redaction.conclusion(chantiers_data, start_date, end_date), body_style,
    ))
    story.append(Spacer(1, 0.5*cm))
    
    # Signature block
    sig_style = ParagraphStyle('Sig', parent=styles['Normal'], fontName='Helvetica', fontSize=10, alignment=2, spaceBefore=20)
    story.append(Paragraph("Fait \u00e0 Abidjan, le " + datetime.now().strftime("%d/%m/%Y"), sig_style))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Sp\u00e9cialiste Environnemental \u2014 AGEROUTE / PTUA", sig_style))

    doc.build(story)
    
    buffer.seek(0)
    return buffer
