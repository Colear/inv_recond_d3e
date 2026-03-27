# inventaire/views.py
import io
import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.db.models import Count, Sum, Q
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from .models import Ordinateur, Ecran, Peripherique, Materiel, Marque, Intervention
from .forms import NouveauMaterielForm, DiagnosticRepaForm, DisqueFormSet



"""
Pour référence, conseil pour l'utilisation de class ou de fonction pour les vues : 

    Pour la Page d'Accueil (home) :
        La Classe (TemplateView) est très appropriée ici. Pourquoi ? Parce que votre page d'accueil va probablement évoluer pour afficher des statistiques (nombre de PC en stock, poids recyclé, etc.).
        Avec une CBV (ClassBasedView), la méthode get_context_data est l'endroit naturel et propre pour ajouter ces statistiques dynamiques au contexte avant l'affichage.
        Verdict : Gardez votre approche Classe. C'est propre et évolutif.

    Pour les Formulaires Complexes (ex: Saisie de matériel avec disques) :
        Une Fonction (FBV) est souvent plus lisible quand la logique de sauvegarde est très spécifique (gestion de plusieurs formulaires, transactions atomiques, messages d'erreur complexes).
        Verdict : Privilégiez les Fonctions pour la logique métier complexe de saisie/traitement.

    Pour les Listes (ex: Inventaire global) :
        Django fournit ListView (une CBV). C'est très puissant (pagination, filtrage, tri inclus).
        Verdict : Essayez les Classes (ListView) pour vos listes d'inventaire.
"""



"""====== Home ===============================================================
    Affichage de la home page.
============================================================================"""

class HomePageView(TemplateView):
    template_name = "inventaire/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # --- 1. Statistiques par Statut sur les ordinateurs
        stats_ordis = Ordinateur.objects.aggregate(
            en_attente=Count('id', filter=Q(statut='ENTREE')),
            en_diagnostic=Count('id', filter=Q(statut='DIAGNOSTIC')),
            en_reparation=Count('id', filter=Q(statut='REPARATION')),
            pret_a_don=Count('id', filter=Q(statut='PRET_A_DON')),
            total=Count('id')
        )

        # --- 2. Poids du mois en entrée, tous matériels confondus
        aujourdhui = timezone.now()
        debut_mois = aujourdhui.replace(day=1, hour=0, minute=0, second=0, microsecond=0)       
        poids_mois = Materiel.objects.filter(
            date_entree__gte=debut_mois
        ).aggregate(
            total_kg=Sum('poids_entree_kg')
        )['total_kg'] or 0

        # --- 3. Derniers matériels ajoutés (tous types) ---
        derniers_materiaux = Materiel.objects.select_related('marque', 'benevole_en_charge').order_by('-numero_inventaire')[:5]

        # --- 4. Injection dans le contexte ---
        context['stats_ordis'] = stats_ordis
        context['poids_mois'] = poids_mois
        context['derniers_materiaux'] = derniers_materiaux
        context['date_du_jour'] = aujourdhui.strftime("%d/%m/%Y")

        # --- 5. Message de bienvenue --- 
        messages.info(self.request, "Bienvenue dans l'outil de gestion de l'atelier !")
        
        return context



"""====== InventaireList ======================================================
    Affichage du stock.
    Utilisation d'une class ListView qui supporte nativement la pagination
============================================================================"""

class InventaireListView(ListView):
    model = Materiel
    template_name = 'inventaire/inventaire_list.html'
    context_object_name = 'materiaux'
    paginate_by = 20  # Nombre d'éléments par page

    def get_queryset(self):
        # On part de la base : tous les matériels ordonnés par date d'entrée (plus récent en premier)
        queryset = Materiel.objects.select_related('marque', 'benevole_en_charge', 'beneficiaire').order_by('-numero_inventaire')

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

        # --- FILTRE : BÉNÉVOLE (Optionnel, pour voir ce qu'un bénévole a en charge) ---
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



"""====== NouveauMateriel =====================================================
    Formulaire de saisie rapide d'un nouveau matériel.
    Contient également une vue Ajax pour ajouter une marque à la volée.
============================================================================"""

class NouveauMaterielView(CreateView):
    model = Materiel # On utilise le parent pour le formulaire, mais on sauvera dans l'enfant
    form_class = NouveauMaterielForm
    template_name = 'inventaire/nouveau_materiel.html'
    success_url = '/inventaire' # Redirige vers la liste après succès

    def form_valid(self, form):
        type_materiel = form.cleaned_data['type_materiel']
        categorie_pc = form.cleaned_data.get('categorie_pc')
        categorie_periph = form.cleaned_data.get('categorie_periph')
        
        # 1. Création de l'instance en mémoire (pas encore en base)
        instance = form.save(commit=False)
        instance.date_entree = timezone.now().date()
        
        # 2. Génération du numéro
        instance.numero_inventaire = instance.generer_numero_inventaire()
        
        # 3. Sauvegarde initiale (Crée la ligne avec un ID)
        # On essaie de sauver normalement d'abord
        instance.save()
        
        # 4. Création de l'enfant (Nécessite que le parent ait un ID)
        if type_materiel == 'PC':
            if not categorie_pc:
                return self.form_invalid(form)
            Ordinateur.objects.create(materiel_ptr=instance, categorie=categorie_pc)
        elif type_materiel == 'ECRAN':
            Ecran.objects.create(materiel_ptr=instance)
        elif type_materiel == 'PERIPH':
            if not categorie_periph:
                return self.form_invalid(form)
            Peripherique.objects.create(materiel_ptr=instance, type_periph=categorie_periph)
            
        # 5. CORRECTION GLOBALE (Le "Silver Bullet")
        # On force l'écriture de TOUS les champs critiques en une seule requête SQL
        # Cela contourne tous les problèmes de commit=False, editable, etc.
        Materiel.objects.filter(pk=instance.pk).update(
            numero_inventaire=instance.numero_inventaire,
            poids_entree_kg=instance.poids_entree_kg,
            provenance=instance.provenance,
            marque_id=instance.marque_id, # Attention : utiliser l'ID pour une ForeignKey
            modele=instance.modele,
            type_materiel=instance.type_materiel,
            date_entree=instance.date_entree,
            statut=instance.statut,
            benevole_en_charge_id=instance.benevole_en_charge_id,
        )

        return redirect(self.success_url)


# --- Vue AJAX pour permettre l'ajout de marque à la volée ---
def ajax_create_marque(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        if nom:
            marque, created = Marque.objects.get_or_create(nom=nom)
            return JsonResponse({'success': True, 'id': marque.id, 'nom': marque.nom})
    return JsonResponse({'success': False, 'error': 'Nom requis'})



"""====== imprimer_planche_etiquette ==========================================
    Imprime une planche de  étiquettes avec QRCode. Par défaut les 10
    étiquettes suivant le dernier numéro d'inventaire entré mais peut
    se paramétrer via l'URL de la requête GET.
============================================================================"""

def imprimer_planche_etiquettes(request):

    # 1. Définir la plage d'étiquettes à imprimer
    # On prend les 10 prochains numéros à partir du dernier existant + 1
    # Ou vous pouvez passer des paramètres GET ?start=100&end=110
    
    # Récupérer le dernier numéro pour calculer le suivant
    from .models import Materiel
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



"""====== modifier_materiel ===================================================
    Vue commune au diagnostic et à la réparation / configuration d'ordis.
============================================================================"""

@login_required # Sécurité : seul un connecté peut modifier
def modifier_materiel(request, pk):
    materiel = get_object_or_404(Materiel, pk=pk)
    
    if not hasattr(materiel, 'ordinateur') or materiel.ordinateur is None:
        messages.warning(request, "Ce matériel n'est pas un ordinateur.")
        return redirect('home')
        
    ordinateur = materiel.ordinateur
    benevole = request.user # Le bénévole connecté

    if request.method == 'POST':
        form = DiagnosticRepaForm(request.POST, instance=ordinateur)
        formset = DisqueFormSet(request.POST, instance=ordinateur)
        
        if form.is_valid() and formset.is_valid():  
            action = request.POST.get('action')
            instance = form.save(commit=False)
            
            # --- TRAITEMENT DES CHAMPS MANUELS (MARQUE/MODELE) ---
            nom_marque = request.POST.get('input_marque', '').strip()
            nom_modele = request.POST.get('input_modele', '').strip()
            
            # Gestion de la Marque (Création si n'existe pas, ou récupération)
            if nom_marque:
                marque_obj, created = Marque.objects.get_or_create(nom=nom_marque)
                instance.materiel_ptr.marque = marque_obj # Accès au parent via materiel_ptr
            
            # Gestion du Modèle
            if nom_modele:
                instance.materiel_ptr.modele = nom_modele
            
            # Sauvegarde du parent (Materiel) avec les nouvelles infos
            instance.materiel_ptr.save()
            
            # --- LOGIQUE MÉTIER PAR BOUTON ---
            
            # 1. COMMENCER LE DIAGNOSTIC (Transition ENTREE -> DIAGNOSTIC)
            if action == 'start_diag':
                if materiel.statut == 'ENTREE':
                    instance.statut = 'DIAGNOSTIC'
                    instance.benevole_en_charge = benevole # Attribution auto
                    instance.date_prise_en_charge = timezone.now()
                    
                    # Historique
                    Intervention.objects.create(
                        materiel=materiel,
                        benevole=benevole,
                        type_action='DIAG',
                        commentaire="Début du diagnostic. Prise en charge du dossier."
                    )
                    messages.success(request, f"🔍 Diagnostic commencé par {benevole.get_full_name()}.")
                else:
                    messages.info(request, "Le diagnostic est déjà en cours ou validé.")

            # 2. VALIDER ET PASSER EN RÉPARATION (DIAGNOSTIC -> REPARATION)
            elif action == 'validate_diag_repa':
                # On s'assure que le bénévole est bien attribué (s'il ne l'était pas avant)
                if not instance.benevole_en_charge:
                    instance.benevole_en_charge = benevole
                    instance.date_prise_en_charge = timezone.now()
                
                instance.statut = 'REPARATION'
                
                # Historique
                Intervention.objects.create(
                    materiel=materiel,
                    benevole=benevole,
                    type_action='DIAG',
                    commentaire="Diagnostic validé. Passage en phase de réparation."
                )
                messages.success(request, "✅ Diagnostic validé. Passage en mode Réparation.")

            # 3. VALIDER ET RELÂCHER (DIAGNOSTIC -> ENTREE ou REPARATION sans bénévole)
            elif action == 'validate_diag_release':
                # On valide le diagnostic techniquement, mais on libère le bénévole
                # Le statut passe à REPARATION (prêt pour le suivant) ou reste DIAGNOSTIC si vous préférez
                # Ici, je le passe en REPARATION pour dire "Prêt pour la suite" mais sans propriétaire
                instance.statut = 'REPARATION'
                instance.benevole_en_charge = None # Libération
                # On ne touche pas à date_prise_en_charge (on garde la trace de qui a commencé)
                
                Intervention.objects.create(
                    materiel=materiel,
                    benevole=benevole,
                    type_action='TRANSFERT',
                    commentaire="Diagnostic terminé. Dossier relâché pour la suite."
                )
                messages.success(request, "👐 Diagnostic validé et dossier relâché. Un autre bénévole pourra prendre la suite.")

            # 4. ENREGISTRER ET QUITTER (Sauvegarde brouillon)
            elif action == 'save_exit':
                # Si c'était en ENTREE, on passe en DIAGNOSTIC car on a commencé à travailler dessus
                if materiel.statut == 'ENTREE':
                    instance.statut = 'DIAGNOSTIC'
                    instance.benevole_en_charge = benevole
                    instance.date_prise_en_charge = timezone.now()
                    
                    Intervention.objects.create(
                        materiel=materiel,
                        benevole=benevole,
                        type_action='NOTE',
                        commentaire="Début du diagnostic (sauvegarde intermédiaire)."
                    )
                else:
                    messages.info(request, "💾 Modifications enregistrées.")

            # 5. VALIDER RÉPARATION FINALE (REPARATION -> PRET_A_DON)
            elif action == 'validate_repa':
                instance.statut = 'PRET_A_DON'
                Intervention.objects.create(
                    materiel=materiel,
                    benevole=benevole,
                    type_action='REPA',
                    commentaire="Réparation et configuration validées. Prêt à donner."
                )
                messages.success(request, "🎉 Réparation validée ! Prêt à donner.")

            # --- SAUVEGARDE COMMUNE ---
            # Nettoyage des champs numériques vides
            if instance.cout_reparation is None or instance.cout_reparation == '':
                instance.cout_reparation = Decimal('0.00')
            
            instance.save()
            formset.save()
            
            # Redirection intelligente
            if action == 'save_exit':
                return redirect('inventaire') # Retour liste
            else:
                return redirect('modifier_materiel', pk=pk) # Reste sur la page pour continuer

        else:
            # Debug si erreur
            if not form.is_valid(): print(f"Erreurs Form : {form.errors}")
            if not formset.is_valid(): print(f"Erreurs Formset : {formset.errors}")
            messages.error(request, "Une erreur est survenue dans le formulaire. Vérifiez les champs.")

    else:
        # GET : Initialisation
        form = DiagnosticRepaForm(instance=ordinateur)
        formset = DisqueFormSet(instance=ordinateur)

    context = {
        'materiel': materiel,
        'ordinateur': ordinateur,
        'form': form,
        'formset': formset,
        'benevole_actuel': benevole,
    }
    return render(request, 'inventaire/modifier_materiel.html', context)
