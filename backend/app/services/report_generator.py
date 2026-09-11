import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.units import cm
from reportlab.platypus.flowables import HRFlowable

from . import redaction_pges as redaction


#: Les libelles des statuts, tels qu'un rapport reglementaire les ecrit.
#:
#: Les statuts arrivent ici sous leur forme technique, soit une valeur
#: d'enumeration dont la conversion en chaine donne
#: « StatutSignalement.EN_TRAITEMENT ». Ce nom de classe Python n'a rien
#: a faire dans un document remis a l'agence de tutelle et au bailleur.
LIBELLES_STATUT = {
    "NOUVEAU": "Nouveau",
    "EN_TRAITEMENT": "En traitement",
    "CLOTURE": "Clôturé",
    "REJETE": "Rejeté",
    "RECU": "Reçue",
    "EN_COURS": "En cours",
    "RESOLU": "Traitée",
    "REJETEE": "Classée sans suite",
}


def _libelle_statut(valeur):
    """Le statut en clair, quelle que soit la forme recue.

    La valeur peut arriver en enumeration, en chaine, ou vide selon le
    circuit qui l'a produite. Un statut inconnu est rendu tel quel
    plutot que masque : mieux vaut une mention brute qu'une case vide
    dans un rapport de conformite.
    """
    if valeur is None:
        return ""
    brut = getattr(valeur, "value", None) or str(valeur)
    if "." in brut:
        brut = brut.rsplit(".", 1)[1]
    return LIBELLES_STATUT.get(brut, brut.replace("_", " ").capitalize())


def _extrait(texte, limite=110):
    """Une description ramenee a la longueur d'une cellule.

    La coupe se fait sur le dernier espace avant la limite, et non au
    caractere pres : « Sacs de ciment vides stockes a l'air libre.
    Retire » s'arretait au milieu d'un mot.
    """
    propre = " ".join(str(texte or "").split())
    if len(propre) <= limite:
        return propre
    tronque = propre[:limite]
    espace = tronque.rfind(" ")
    if espace > limite * 0.6:
        tronque = tronque[:espace]
    return tronque.rstrip(" ,;.") + "…"


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

    # Le style des cellules de detail. Une chaine posee dans un tableau
    # ne revient pas a la ligne ; un Paragraph, si.
    cellule_style = ParagraphStyle(
        'Cellule', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5,
        textColor=colors.HexColor('#3F3F46'), leading=11,
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
    
    # La troisieme colonne portait un libelle fixe, \u00ab Enregistre \u00bb,
    # \u00ab Surveille \u00bb, qui ne disait rien des donnees. Elle porte
    # desormais la part non close, seul chiffre que les compteurs
    # permettent d'etablir et que le lecteur cherche.
    total_traites = sum(c.get('nb_traites', 0) for c in chantiers_data)
    total_pl_ouvertes = sum(c.get('nb_plaintes_ouvertes', 0)
                            for c in chantiers_data)
    total_nc_ouvertes = sum(c.get('nb_nc_ouvertes', 0)
                            for c in chantiers_data)
    reste_sig = total_sig - total_traites

    summary_data = [
        ['Indicateur', 'Total', 'Dont non clos'],
        ['Signalements environnementaux', str(total_sig),
         str(reste_sig) if total_sig else '\u2014'],
        ['Alertes par franchissement de seuil', str(total_alertes), '\u2014'],
        ['Plaintes communautaires (MGP)', str(total_plaintes),
         str(total_pl_ouvertes) if total_plaintes else '\u2014'],
        ['Non-conformit\u00e9s (inspections)', str(total_nc),
         str(total_nc_ouvertes) if total_nc else '\u2014'],
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
        
        # Le tableau du chantier. La troisieme colonne portait un point
        # noir constant, identique sur chaque ligne : elle s'intitulait
        # \u00ab Tendance \u00bb sans en calculer aucune, ce qu'un lecteur attentif
        # releve aussitot.
        #
        # Elle porte desormais ce que les compteurs permettent
        # reellement de dire : la part traitee pour les signalements, la
        # part encore ouverte pour les plaintes et les non-conformites.
        nb_sig = chantier.get('nb_signalements', 0)
        nb_traites = chantier.get('nb_traites', 0)
        nb_plaintes = chantier.get('nb_plaintes', 0)
        nb_pl_ouvertes = chantier.get('nb_plaintes_ouvertes', 0)
        nb_nc = chantier.get('nb_non_conformites', 0)
        nb_nc_ouvertes = chantier.get('nb_nc_ouvertes', 0)

        etat_sig = (f"{nb_traites} cl\u00f4tur\u00e9{'s' if nb_traites > 1 else ''} "
                    f"sur {nb_sig}" if nb_sig else "aucun constat")
        etat_plaintes = (f"{nb_pl_ouvertes} en attente" if nb_pl_ouvertes
                         else ("toutes trait\u00e9es" if nb_plaintes
                               else "aucune plainte"))
        etat_nc = (f"{nb_nc_ouvertes} \u00e0 r\u00e9gulariser" if nb_nc_ouvertes
                   else ("toutes r\u00e9gularis\u00e9es" if nb_nc
                         else "aucun \u00e9cart"))

        data = [
            ['Indicateur', 'Quantit\u00e9', '\u00c9tat'],
            ['Signalements environnementaux', str(nb_sig), etat_sig],
            ['Alertes par franchissement de seuil',
             str(chantier.get('nb_alertes', 0)), 'diffus\u00e9es par courriel'],
            ['Plaintes communautaires (MGP)', str(nb_plaintes),
             etat_plaintes],
            ['Non-conformit\u00e9s (inspections)', str(nb_nc), etat_nc],
        ]

        t = Table(data, colWidths=[8.4*cm, 2.6*cm, 5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#004F9F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
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
            # La description est un Paragraph et non une chaine : une
            # cellule de tableau ne renvoie pas a la ligne toute seule,
            # et le texte debordait sur la colonne voisine.
            sig_data = [['Type', 'Description', 'Statut', 'Date']] + [
                [Paragraph(s['type'], cellule_style),
                 Paragraph(_extrait(s.get('desc')), cellule_style),
                 Paragraph(_libelle_statut(s.get('statut')), cellule_style),
                 Paragraph(s.get('date', ''), cellule_style)]
                for s in chantier['signalements_details']]
            t_sig = Table(sig_data, colWidths=[3.4*cm, 6.6*cm, 3.4*cm, 2.6*cm])
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
            pl_data = [['Plaignant', 'Description', 'Statut', 'Date']] + [
                [Paragraph(p['nom'], cellule_style),
                 Paragraph(_extrait(p.get('desc')), cellule_style),
                 Paragraph(_libelle_statut(p.get('statut')), cellule_style),
                 Paragraph(p.get('date', ''), cellule_style)]
                for p in chantier['plaintes_details']]
            t_pl = Table(pl_data, colWidths=[3.4*cm, 6.6*cm, 3.4*cm, 2.6*cm])
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
