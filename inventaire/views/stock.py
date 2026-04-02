import io
import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import Image, SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required, permission_required
from ..mixins import AuthBenevoleMixin
from ..decorators import benevole_actif_required
from ..models import Materiel



"""====== InventaireList ======================================================
    Affichage du stock.
    Utilisation d'une class ListView qui supporte nativement la pagination
============================================================================"""

class InventaireListView(AuthBenevoleMixin, ListView):
    model = Materiel
    template_name = 'inventaire/inventaire_list.html'
    context_object_name = 'materiaux'
    paginate_by = 20  # Nombre d'éléments par page

    # permissions nécessaires pour afficher la vue
    permission_required = 'inventaire.view_materiel'

    def get_queryset(self):
        # On part de la base : tous les matériels ordonnés par date d'entrée (plus récent en premier)
        queryset = Materiel.objects.select_related('marque', 
                                                   'benevole_en_charge', 
                                                   'beneficiaire',
                                                   'ordinateur',
                                                   'ecran',
                                                   'peripherique').order_by('-numero_inventaire')

        # --- FILTRE : RECHERCHE TEXTE ---
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(numero_inventaire__icontains=search_query) |
                Q(marque__nom__icontains=search_query) |
                Q(modele__icontains=search_query) |
                Q(numero_serie__icontains=search_query)
            )

        # --- FILTRE : STATUT ---
        statut_filter = self.request.GET.get('statut', '')
        if statut_filter:
            queryset = queryset.filter(statut=statut_filter)

        # --- FILTRE : TYPE DE MATÉRIEL ---
        type_filter = self.request.GET.get('type_materiel', '')
        if type_filter:
            queryset = queryset.filter(type_materiel=type_filter)

        # --- FILTRE : BÉNÉVOLE ---
        benevole_id = self.request.GET.get('benevole_id', '')
        if benevole_id:
            queryset = queryset.filter(benevole_en_charge_id=benevole_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # On passe les filtres actuels au template pour maintenir les valeurs dans le formulaire après rechargement
        context['search_query'] = self.request.GET.get('q', '')
        context['statut_filter'] = self.request.GET.get('statut', '')
        context['type_filter'] = self.request.GET.get('type_materiel', '')
        
        # On passe aussi la liste des choix pour les <option> du formulaire
        context['statut_choices'] = Materiel.STATUT_CHOICES
        context['type_choices'] = Materiel.TYPE_CHOICES
        
        return context



"""====== imprimer_planche_etiquette ==========================================
    Imprime une planche de  étiquettes avec QRCode. Par défaut les 10
    étiquettes suivant le dernier numéro d'inventaire entré mais peut
    se paramétrer via l'URL de la requête GET.
============================================================================"""

@login_required
@benevole_actif_required
@permission_required('inventaire.can_print_labels', raise_exception=True)
def imprimer_planche_etiquettes(request):

    # 1. Définir la plage d'étiquettes à imprimer
    # On prend les 10 prochains numéros à partir du dernier existant + 1
    # Ou vous pouvez passer des paramètres GET ?start=100&end=110
    
    # Récupérer le dernier numéro pour calculer le suivant
    last_mat = Materiel.objects.filter(numero_inventaire__isnull=False).order_by('-numero_inventaire').first()
    
    start_num = 1
    if last_mat:
        try:
            last_id = int(last_mat.numero_inventaire.split('-')[-1])
            start_num = last_id + 1
        except:
            pass
            
    end_num = start_num + 9  # Une planche de 10
    
    etiquette_data = []
    
    # 2. Préparer les données pour les 10 étiquettes
    for i in range(start_num, end_num + 1):
        num_inv = f"INV-{i:04d}"

        # URL qui sera contenue dans le QRCode                      
        url_cible = request.build_absolute_uri(f'/inventaire/search-by-inv/{num_inv}/')
        
        # Générer le QR Code en mémoire
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(url_cible)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        # Sauvegarder dans un buffer BytesIO pour ReportLab
        buffer = io.BytesIO()
        img_qr.save(buffer, format='PNG')
        buffer.seek(0)
        
        etiquette_data.append([Image(buffer, width=3*cm, height=3*cm), f"{num_inv}"])

    # 3. Créer le PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="planche_etiquettes_{start_num}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm, leftMargin=1*cm, rightMargin=1*cm)
    elements = []
    
    styles = getSampleStyleSheet()
    style_num = ParagraphStyle('Numero', parent=styles['Heading2'], alignment=TA_CENTER, fontSize=14, spaceAfter=5)
    
    # Créer une table de 2 colonnes et 5 lignes (10 étiquettes)
    # Chaque cellule contient : [Image QR, Texte Numéro]
    # On va construire une liste de listes pour la table ReportLab
    table_data = []
    row = []
    
    for i, data in enumerate(etiquette_data):
        qr_img, num_text = data
        # Cellule complète : QR + Numéro
        cell_content = [qr_img, Paragraph(num_text, style_num)]
        row.append(cell_content)
        
        if len(row) == 2: # 2 colonnes
            table_data.append(row)
            row = []
            # Ajouter un espace entre les lignes d'étiquettes
            table_data.append([Spacer(1, 0.5*cm)]) 
            
    if row: # Si la dernière ligne n'est pas pleine
        table_data.append(row)

    # Construire la table finale
    # Largeur totale page ~19cm. 2 colonnes => ~9cm par cellule.
    t = Table(table_data, colWidths=[9*cm, 9*cm])
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1, colors.black), # Cadre autour de chaque étiquette
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    
    elements.append(t)
    doc.build(elements)
    
    return response



"""====== search_by_inv =======================================================
    Vue qui reçoit un numéro d'inventaire et qui route vers la page d'édition
    de ce matériel (temporairement l'admin) ou une page d'erreur.
============================================================================"""

@login_required
@benevole_actif_required
@permission_required('inventaire.change_materiel', raise_exception=True)
def search_by_inv(request, numero_inv):

    try:
        # On essaie de trouver le matériel
        materiel = Materiel.objects.get(numero_inventaire=numero_inv)
        
        # SUCCÈS : Redirection immédiate vers la fiche d'édition dans l'Admin
        # return redirect('admin:inventaire_materiel_change', pk=materiel.pk)
        return redirect('modifier_materiel', pk=materiel.pk)
        
    except Materiel.DoesNotExist:
        # ÉCHEC : On affiche simplement une page d'information
        context = {
            'numero_inv': numero_inv,
            'message': f"Le numéro d'inventaire <strong>{numero_inv}</strong> n'est pas encore attribué à un matériel."
        }
        return render(request, 'inventaire/etiquette_non_trouvee.html', context)

