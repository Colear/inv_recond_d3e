from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from django.utils import timezone
from django.db.models import Sum
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
from ..decorators import benevole_actif_required
from ..models import Materiel, Ordinateur



"""====== rapport_activite_pdf ================================================
    Exemple de rapport d'activité (démo).
============================================================================"""

@login_required
@benevole_actif_required
@permission_required('inventaire.can_print_labels', raise_exception=True)
def rapport_activite_pdf(request):
  
    # ===== 1. Récupération des données

    # Déterminer la période (Mois précédent)
    aujourdhui = timezone.now() 
    # temporaire => on teste depuis le premier mars (mois forcé)
    debut_mois = aujourdhui.replace(month=3, day=1, hour=0, minute=0, second=0, microsecond=0)
    fin_mois = aujourdhui  # Jusqu'à maintenant
    
    # Récupération des données brutes
    # A. Par Provenance
    stats_provenance = Materiel.objects.filter(date_entree__gte=debut_mois).values('provenance').annotate(total_poids=Sum('poids_entree_kg'))
    
    # B. Par Type de Matériel
    stats_type = Materiel.objects.filter(date_entree__gte=debut_mois).values('type_materiel').annotate(total_poids=Sum('poids_entree_kg'))
    
    # C. Total Global
    total_global = Materiel.objects.filter(date_entree__gte=debut_mois).aggregate(Sum('poids_entree_kg'))['poids_entree_kg__sum'] or 0
    
    # D. Nombre de PC donnés ce mois-ci (Impact social)
    pc_donnes = Ordinateur.objects.filter(statut='DONNE', date_sortie__gte=debut_mois).count()


    # ===== 2. Création du PDF

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Rapport_Activite_{aujourdhui.strftime("%Y_%m")}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=landscape(A4), rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    # --- Titres
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.darkblue, spaceAfter=30, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=14, textColor=colors.grey, spaceAfter=20, alignment=TA_CENTER)
    
    elements.append(Paragraph(f"Rapport d'activité mensuel - Atelier reconditionnement CBE / LBAO / SICTOM", title_style))
    elements.append(Paragraph(f"Période : {debut_mois.strftime('%d/%m/%Y')} au {aujourdhui.strftime('%d/%m/%Y')}", subtitle_style))
    
    # --- KPIs (Indicateurs Clés)
    kpi_data = [
        [f"Poids Total Entré", f"{total_global:.1f} kg"],
        [f"PC Donnés ce mois", f"{pc_donnes} unités"],
        [f"Matériaux sauvés", f"{total_global:.1f} kg de DEEE évités"]
    ]
    kpi_table = Table(kpi_data, colWidths=[5*cm, 5*cm])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 1*cm))
    
    # --- Graphiques (Camemberts)
    
    # Graphique 1 : Par Provenance --
    elements.append(Paragraph("Répartition par Provenance (Poids)", styles['Heading2']))
    
    drawing_prov = Drawing(width=400, height=200)
    pie_prov = Pie()
    pie_prov.x = 50
    pie_prov.y = 0
    pie_prov.height = 180
    pie_prov.width = 180
    
    data_prov = [float(item['total_poids']) for item in stats_provenance if item['total_poids']]
    labels_prov = [dict(Materiel.SOURCES_PROVENANCE).get(item['provenance'], item['provenance']) for item in stats_provenance if item['total_poids']]
    
    # Si pas de données, on met une valeur par défaut pour ne pas casser le graph
    if not data_prov:
        data_prov = [1]
        labels_prov = ["Aucune donnée"]
        
    pie_prov.data = data_prov
    pie_prov.labels = labels_prov
    pie_prov.slices.strokeWidth = 0.5

    # Couleurs dynamiques pour éviter les erreurs d'index si peu de données
    colors_list = [colors.darkblue, colors.green, colors.orange, colors.red, colors.purple, colors.brown, colors.pink]
    for i in range(len(data_prov)):
        pie_prov.slices[i].fillColor = colors_list[i % len(colors_list)]
    
    drawing_prov.add(pie_prov)
    elements.append(drawing_prov)
    elements.append(Spacer(1, 1*cm))
    
    # -- Graphique 2 : Par Type de Matériel --
    elements.append(Paragraph("Répartition par Type de Matériel (Poids)", styles['Heading2']))
    
    drawing_type = Drawing(width=400, height=200)
    pie_type = Pie()
    pie_type.x = 50
    pie_type.y = 0
    pie_type.height = 180
    pie_type.width = 180
    
    data_type = [float(item['total_poids']) for item in stats_type if item['total_poids']]
    labels_type = [dict(Materiel.TYPE_CHOICES).get(item['type_materiel'], item['type_materiel']) for item in stats_type if item['total_poids']]
    
    if not data_type:
        data_type = [1]
        labels_type = ["Aucune donnée"]
        
    pie_type.data = data_type
    pie_type.labels = labels_type
    pie_type.slices.strokeWidth = 0.5

    colors_list_type = [colors.blue, colors.green, colors.yellow, colors.orange, colors.red]
    for i in range(len(data_type)):
        pie_type.slices[i].fillColor = colors_list_type[i % len(colors_list_type)]
    
    drawing_type.add(pie_type)
    elements.append(drawing_type)
    elements.append(Spacer(1, 1*cm))
    
    # Tableau de détail (Optionnel, liste des dernières entrées)
    elements.append(Paragraph("Dernières entrées du mois", styles['Heading2']))
    dernieres_entrees = Materiel.objects.filter(date_entree__gte=debut_mois).order_by('-date_entree')[:10]
    
    data_table = [['Date', 'Inventaire', 'Type', 'Provenance', 'Poids (kg)']]
    for m in dernieres_entrees:
        data_table.append([
            m.date_entree.strftime('%d/%m'),
            m.numero_inventaire,
            m.get_type_materiel_display(),
            m.get_provenance_display(),
            f"{m.poids_entree_kg:.2f}"
        ])
    
    t = Table(data_table, colWidths=[2*cm, 2.5*cm, 3*cm, 5*cm, 2*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(t)
    
    # Footer
    elements.append(Spacer(1, 2*cm))
    footer = Paragraph(f"<i>Généré le {aujourdhui.strftime('%d/%m/%Y à %H:%M')}.</i>", styles['Normal'])
    elements.append(footer)
    
    doc.build(elements)
    return response

