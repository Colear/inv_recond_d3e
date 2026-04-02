# inventaire/views.py
import io
import qrcode
from datetime import datetime, timedelta
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.urls import reverse_lazy
# from django.conf import settings
from django.db.models import Count, Sum, Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from .models import Ordinateur, Ecran, Peripherique, Materiel, Marque, Intervention, Beneficiaire
from .forms import NouveauMaterielForm, DiagnosticRepaForm, DisqueFormSet, BeneficiaireForm
from .decorators import benevole_actif_required
from .mixins import AuthBenevoleMixin



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



"""====== Login / logout ======================================================
    Pages de connexion / deconnexion.
============================================================================"""

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True  # Si déjà connecté, renvoie vers home
    # La redirection par défaut après login est gérée par LOGIN_REDIRECT_URL dans settings.py

class CustomLogoutView(LogoutView):
    # Redirige vers la page de login après déconnexion
    next_page = 'login' 



"""====== Home ===============================================================
    Affichage de la home page.
============================================================================"""

class HomePageView(AuthBenevoleMixin, TemplateView):
    template_name = "inventaire/home.html"

    # permissions nécessaires pour afficher la vue
    permission_required = 'inventaire.view_materiel'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # --- 1. Statistiques par Statut sur les ordinateurs
        stats_ordis = Ordinateur.objects.aggregate(
            en_attente=Count('id', filter=Q(statut='ENTREE')),
            en_diagnostic=Count('id', filter=Q(statut='DIAGNOSTIC')),
            en_reparation=Count('id', filter=Q(statut='REPARATION')),
            en_attente_pieces=Count('id', filter=Q(statut='ATTENTE_PIECES')),
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
        derniers_materiaux = Materiel.objects.select_related('marque', 
                                                             'benevole_en_charge',
                                                             'ordinateur',
                                                             'ecran',
                                                             'peripherique').order_by('-numero_inventaire')[:5]

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

class NouveauMaterielView(AuthBenevoleMixin, CreateView): 

    model = Materiel # On utilise le parent pour le formulaire, mais on sauvera dans l'enfant
    form_class = NouveauMaterielForm
    template_name = 'inventaire/nouveau_materiel.html'
    success_url = '/inventaire' # Redirige vers la liste après succès

    # permissions nécessaires pour afficher la vue
    permission_required = 'inventaire.add_materiel'

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
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Non authentifié'})
    
    try:
        if not request.user.profile_benevole.actif and not request.user.is_superuser:
            return JsonResponse({'success': False, 'error': 'Compte inactif'})
    except Benevole.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil introuvable'})
    
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

@login_required
@benevole_actif_required
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

@login_required
@benevole_actif_required
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

@login_required
@benevole_actif_required
def modifier_materiel(request, pk):
    materiel = get_object_or_404(Materiel, pk=pk)
    
    # Sécurité : Vérifier que c'est un ordinateur
    if not hasattr(materiel, 'ordinateur') or materiel.ordinateur is None:
        messages.error(request, "Ce matériel n'est pas un ordinateur.")
        return redirect('inventaire')
        
    ordinateur = materiel.ordinateur
    benevole = request.user
    redirect_to_inventory = False

    if request.method == 'POST':
        form = DiagnosticRepaForm(request.POST, instance=ordinateur)
        formset = DisqueFormSet(request.POST, instance=ordinateur)
        
        if form.is_valid() and formset.is_valid():
            action = request.POST.get('action')
            instance = form.save(commit=False)
            
            # 1. Gestion Marque/Modèle (Champs manuels du template)
            nom_marque = request.POST.get('input_marque', '').strip()
            nom_modele = request.POST.get('input_modele', '').strip()
            if nom_marque:
                marque_obj, _ = Marque.objects.get_or_create(nom=nom_marque)
                instance.materiel_ptr.marque = marque_obj
            if nom_modele:
                instance.materiel_ptr.modele = nom_modele
            instance.materiel_ptr.save()

            # 2. Logique des Actions
            commentaire_intervention = ""
            type_action = "NOTE"

            if action == 'start_diag':
                # Transition : ENTREE -> DIAGNOSTIC
                if materiel.statut == 'ENTREE':
                    instance.statut = 'DIAGNOSTIC'
                    instance.benevole_en_charge = benevole
                    instance.date_prise_en_charge = timezone.now()
                    type_action = 'DIAG'
                    commentaire_intervention = "Début du diagnostic. Prise en charge du dossier."
                    messages.success(request, "🔍 Diagnostic commencé. Vous êtes maintenant assigné à ce dossier.")
                else:
                    messages.warning(request, "Le statut ne permet pas de démarrer le diagnostic.")

            elif action == 'save_exit':
                # Sauvegarde brouillon : Reste en DIAGNOSTIC (ou passe de ENTREE à DIAGNOSTIC si premier sauvegarde)
                if materiel.statut == 'ENTREE':
                    instance.statut = 'DIAGNOSTIC'
                    instance.benevole_en_charge = benevole
                    instance.date_prise_en_charge = timezone.now()
                    type_action = 'DIAG'
                    commentaire_intervention = "Début du diagnostic (sauvegarde intermédiaire)."
                else:
                    type_action = 'NOTE'
                    commentaire_intervention = "Sauvegarde intermédiaire du diagnostic."
                
                messages.info(request, "💾 Travail enregistré. Vous pouvez revenir plus tard.")
                redirect_to_inventory = True # RETOUR LISTE

            elif action == 'validate_diag_release':
                # Validation + Libération : DIAGNOSTIC -> REPARATION (Sans bénévole)
                instance.statut = 'REPARATION'
                instance.benevole_en_charge = None # On libère
                type_action = 'TRANSFERT'
                commentaire_intervention = "Diagnostic validé. Dossier relâché pour la suite (spécialiste)."
                messages.success(request, "👋 Diagnostic validé et dossier relâché. Retour à l'inventaire.")
                redirect_to_inventory = True # RETOUR LISTE

            elif action == 'validate_diag_repa':
                # Validation + Continuité : DIAGNOSTIC -> REPARATION (Avec bénévole)
                if not instance.benevole_en_charge:
                    instance.benevole_en_charge = benevole
                    instance.date_prise_en_charge = timezone.now()
                instance.statut = 'REPARATION'
                type_action = 'DIAG'
                commentaire_intervention = "Diagnostic validé. Passage en phase de réparation/configuration."
                messages.success(request, "✅ Diagnostic validé. Vous pouvez maintenant configurer le logiciel.")
                # redirect_to_inventory = False (Reste sur page)

            elif action == 'recycle_now':
                # Recyclage immédiat : -> RECYCLAGE
                instance.statut = 'RECYCLAGE'
                if not instance.benevole_en_charge:
                    instance.benevole_en_charge = benevole
                type_action = 'SORTIE'
                raison = instance.rapport_diagnostic[:100] or "Non réparable (Décision diagnostic)"
                commentaire_intervention = f"Décision de recyclage : {raison}"
                messages.warning(request, "♻️ Matériel envoyé au recyclage.")
                redirect_to_inventory = True # RETOUR LISTE

            elif action == 'wait_parts':
                # Transition : -> ATTENTE_PIECES
                instance.statut = 'ATTENTE_PIECES'
                
                # LIBÉRATION DU BÉNÉVOLE
                # On note qui a fait la mise en attente dans l'historique, mais on vide le champ "en charge"
                ancien_benevole = instance.benevole_en_charge
                instance.benevole_en_charge = None 
                # On ne touche pas à date_prise_en_charge pour garder la trace de la première prise en charge
                
                raison = instance.rapport_diagnostic[:100] or "En attente de composants"
                Intervention.objects.create(
                    materiel=materiel,
                    benevole=benevole, # Celui qui clique maintenant
                    type_action='NOTE',
                    commentaire=f"Mise en attente de pièces par {benevole.get_full_name()}. (Dossier libéré). Raison : {raison}"
                )
                messages.info(request, "⏳ Matériel placé en attente de pièces. Le dossier a été libéré pour un futur spécialiste.")
                redirect_to_inventory = True

            elif action == 'reactivate_keep':
                # Option 1 : Réactiver et Garder (Je fais tout : Hardware + Software)
                if materiel.statut == 'ATTENTE_PIECES':
                    instance.statut = 'REPARATION'
                    instance.benevole_en_charge = benevole # Je me l'attribue
                    instance.date_prise_en_charge = timezone.now()
                    
                    Intervention.objects.create(
                        materiel=materiel,
                        benevole=benevole,
                        type_action='TRANSFERT',
                        commentaire="Réactivation et prise en charge complète (Hardware + Software)."
                    )
                    messages.success(request, "✅ Matériel réactivé. Vous restez en charge du dossier pour la configuration.")
                    # redirect_to_inventory = False (Reste sur la page)

            elif action == 'reactivate_release':
                # Option 2 : Réactiver et Relâcher (Je fais le Hardware, je laisse le Software à un autre)
                if materiel.statut == 'ATTENTE_PIECES':
                    instance.statut = 'REPARATION'
                    instance.benevole_en_charge = None # Je libère le dossier pour la suite
                    
                    Intervention.objects.create(
                        materiel=materiel,
                        benevole=benevole,
                        type_action='TRANSFERT',
                        commentaire=f"Réactivation Hardware par {benevole.get_full_name()}. Pièces installées. Dossier relâché pour configuration Linux."
                    )
                    messages.success(request, "🔧 Matériel réactivé (Hardware fait). Le dossier est retourné à l'inventaire pour un spécialiste Linux.")
                    redirect_to_inventory = True # Retour liste

            elif action == 'reactivate_repa':
                # Transition : ATTENTE_PIECES -> REPARATION
                if materiel.statut == 'ATTENTE_PIECES':
                    instance.statut = 'REPARATION'
                    
                    # On attribue le dossier au bénévole actuel s'il n'y en a pas, 
                    # ou on le laisse tel quel si c'est le même qui reprend son travail.
                    if not instance.benevole_en_charge:
                        instance.benevole_en_charge = benevole
                        instance.date_prise_en_charge = timezone.now()
                    
                    Intervention.objects.create(
                        materiel=materiel,
                        benevole=benevole,
                        type_action='TRANSFERT', # ou 'REPA'
                        commentaire="Réactivation du dossier : pièces manquantes installées. Passage en réparation."
                    )
                    messages.success(request, "✅ Matériel réactivé. Vous pouvez maintenant procéder à la configuration.")
                    # redirect_to_inventory = False (On reste sur la page pour travailler)
                else:
                    messages.warning(request, "Ce statut ne permet pas la réactivation.")

            elif action == 'validate_repa':
                # Fin de réparation : REPARATION -> PRET_A_DON
                instance.statut = 'PRET_A_DON'
                type_action = 'REPA'
                commentaire_intervention = "Réparation et configuration validées. Prêt à donner."
                messages.success(request, "🎉 Matériel prêt à être donné !")
                # redirect_to_inventory = False (Reste sur page, ou True si vous préférez)

            # 3. Sauvegarde Finale
            if instance.cout_reparation is None or instance.cout_reparation == '':
                instance.cout_reparation = Decimal('0.00')
            
            instance.save()
            formset.save()

            # 4. Création de l'historique (Intervention)
            if commentaire_intervention:
                Intervention.objects.create(
                    materiel=materiel,
                    benevole=benevole,
                    type_action=type_action,
                    commentaire=commentaire_intervention
                )

            # 5. Redirection
            if redirect_to_inventory:
                return redirect('inventaire')
            else:
                return redirect('modifier_materiel', pk=pk)

        else:
            # Debug erreurs
            if not form.is_valid():
                print(f"Erreurs Form : {form.errors}")
            if not formset.is_valid():
                print(f"Erreurs Formset : {formset.errors}")
            messages.error(request, "Une erreur est survenue dans le formulaire. Vérifiez les champs.")

    else:
        # GET
        form = DiagnosticRepaForm(instance=ordinateur)
        formset = DisqueFormSet(instance=ordinateur)

    context = {
        'materiel': materiel,
        'ordinateur': ordinateur,
        'form': form,
        'formset': formset,
    }
    return render(request, 'inventaire/modifier_materiel.html', context)



"""====== rapport_activite_pdf ================================================
    Exemple de rapport d'activité (démo).
============================================================================"""

@login_required
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



"""====== faire_un_don ========================================================
    Vue pour donner une configuration.
============================================================================"""

@login_required
def faire_un_don(request):
    print(f"--- DÉBUT VUE FAIRE_UN_DON ---")
    print(f"Méthode: {request.method}")
    print(f"Session avant: {request.session.items()}")

    # 1. Gestion de la session Bénéficiaire
    benef_id = request.session.get('don_beneficiaire_id')
    beneficiaire = None
    
    if benef_id:
        try:
            beneficiaire = Beneficiaire.objects.get(pk=benef_id)
            print(f"Bénéficiaire trouvé en session: {beneficiaire}")
        except Beneficiaire.DoesNotExist:
            print("Bénéficiaire en session inexistant, nettoyage.")
            request.session['don_beneficiaire_id'] = None
            beneficiaire = None

    benef_form = BeneficiaireForm()

    # 2. Traitement POST : Recherche/Création Bénéficiaire
    if request.method == 'POST' and 'action_benef' in request.POST:
        print("ACTION: Recherche/Création Bénéficiaire")
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        if nom and prenom:
            benefs = Beneficiaire.objects.filter(nom__iexact=nom, prenom__iexact=prenom)
            if not benefs.exists():
                # Essai plus large
                benefs = Beneficiaire.objects.filter(nom__icontains=nom, prenom__icontains=prenom)
            
            if benefs.exists():
                beneficiaire = benefs.first()
                request.session['don_beneficiaire_id'] = beneficiaire.id
                messages.success(request, f"Bénéficiaire trouvé : {beneficiaire}")
                print(f"Sélectionné: {beneficiaire.id}")
            else:
                beneficiaire = Beneficiaire.objects.create(nom=nom.upper(), prenom=prenom)
                request.session['don_beneficiaire_id'] = beneficiaire.id
                messages.success(request, f"Créé : {beneficiaire}")
                print(f"Créé: {beneficiaire.id}")
        return redirect('faire_un_don')

    # 3. Gestion du Panier (Session)
    panier_don = request.session.get('panier_don', [])
    print(f"Contenu du panier (Numéros Inv): {panier_don}")

    # Ajout au panier
    if request.method == 'POST' and 'action_ajout_materiel' in request.POST:
        print("ACTION: Ajout Matériel")
        inv_number = request.POST.get('numero_inventaire')
        if inv_number:
            try:
                materiel = Materiel.objects.get(numero_inventaire=inv_number)
                if materiel.statut != 'PRET_A_DON':
                    messages.error(request, f"Statut incorrect : {materiel.statut}")
                elif inv_number not in panier_don:
                    panier_don.append(inv_number)
                    request.session['panier_don'] = panier_don
                    request.session.modified = True # Force la sauvegarde de la session
                    messages.success(request, f"Ajouté : {inv_number}")
                    print(f"Ajouté au panier: {inv_number}")
                else:
                    messages.warning(request, "Déjà dans le panier")
            except Materiel.DoesNotExist:
                messages.error(request, "Matériel introuvable")
        return redirect('faire_un_don')

    # Récupération des objets pour l'affichage
    materiels_a_donner = Materiel.objects.filter(numero_inventaire__in=panier_don) if panier_don else []
    print(f"Objets à donner : {len(materiels_a_donner)}")

    # 4. Traitement POST : Validation Finale
    if request.method == 'POST' and 'action_valider_don' in request.POST:
        print("ACTION: Validation Finale du Don")
        
        # Vérif Bénéficiaire
        current_benef_id = request.session.get('don_beneficiaire_id')
        print(f"ID Bénéficiaire dans session: {current_benef_id}")
        
        if not current_benef_id:
            messages.error(request, "ERREUR CRITIQUE : Aucun bénéficiaire en session. Veuillez le re-sélectionner.")
            return redirect('faire_un_don')
        
        try:
            beneficiaire = Beneficiaire.objects.get(pk=current_benef_id)
        except Beneficiaire.DoesNotExist:
            messages.error(request, "ERREUR : Bénéficiaire introuvable en base.")
            request.session['don_beneficiaire_id'] = None
            return redirect('faire_un_don')

        # Vérif Panier
        if not panier_don:
            messages.error(request, "ERREUR : Le panier est vide.")
            return redirect('faire_un_don')
            
        print(f"Validation pour {beneficiaire} avec {len(panier_don)} articles...")
        
        ids_to_pdf = []
        for inv in panier_don:
            try:
                m = Materiel.objects.get(numero_inventaire=inv)
                m.statut = 'DONNE'
                m.beneficiaire = beneficiaire
                m.date_sortie = timezone.now()
                if not m.poids_sortie_kg:
                    m.poids_sortie_kg = m.poids_entree_kg # Correction typo potentielle ici si variable mal nommée
                    m.poids_sortie_kg = m.poids_entree_kg
                m.save()
                
                Intervention.objects.create(
                    materiel=m, benevole=request.user, type_action='SORTIE',
                    commentaire=f"Donné à {beneficiaire}"
                )
                ids_to_pdf.append(str(m.id))
                print(f"  - Sauvé : {m.numero_inventaire}")
            except Exception as e:
                messages.error(request, f"Erreur sur {inv}: {str(e)}")
                print(f"ERREUR SAUVEGARDE: {e}")

        # Nettoyage Panier
        request.session['panier_don'] = []
        request.session.modified = True
        
        # Construction URL PDF
        if ids_to_pdf:
            ids_str = ",".join(ids_to_pdf)
            print(f"REDIRECTION VERS PDF: benef={beneficiaire.id}, ids={ids_str}")
            from django.urls import reverse
            return redirect('generer_fiche_don_pdf', beneficiaire_id=beneficiaire.id, materiel_ids_str=ids_str)
        else:
            messages.error(request, "Aucun matériel n'a pu être validé.")
            return redirect('faire_un_don')

    context = {
        'beneficiaire': beneficiaire,
        'benef_form': benef_form,
        'panier_don': materiels_a_donner,
        'nb_materiels': len(panier_don),
    }
    return render(request, 'inventaire/faire_un_don.html', context)



"""====== generer_fiche_don_pdf ===============================================
    Génération de la fiche de don pour impression.
============================================================================"""

@login_required
def generer_fiche_don_pdf(request, beneficiaire_id, materiel_ids_str):
    """
    Génère la fiche de don PDF.
    materiel_ids_str : chaîne de caractères "1,2,3" contenant les IDs des matériels donnés.
    """
    try:
        beneficiaire = Beneficiaire.objects.get(pk=beneficiaire_id)
        ids = [int(x) for x in materiel_ids_str.split(',')]
        materiels = Materiel.objects.filter(id__in=ids).select_related('marque')
    except (Beneficiaire.DoesNotExist, ValueError):
        return HttpResponse("Erreur : Données invalides.", status=400)

    # Création du PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Fiche_Don_{beneficiaire.nom}_{beneficiaire.prenom}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()

    # Styles personnalisés
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=20, textColor=colors.darkblue, spaceAfter=20, alignment=TA_CENTER)
    sub_title_style = ParagraphStyle('SubTitle', parent=styles['Heading2'], fontSize=14, textColor=colors.grey, spaceAfter=10)
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.spaceAfter = 6

    # En-tête
    elements.append(Paragraph("FICHE DE DON DE MATÉRIEL INFORMATIQUE", title_style))
    elements.append(Paragraph("Atelier SICTOM / LBAO / CBE", sub_title_style))
    elements.append(Spacer(1, 0.5*cm))

    # Infos Bénéficiaire
    elements.append(Paragraph("<b>Bénéficiaire :</b>", normal_style))
    benef_info = f"""
    <b>Nom :</b> {beneficiaire.nom.upper()} {beneficiaire.prenom}<br/>
    <b>Date du don :</b> {beneficiaire.materiaux_recus.first().date_sortie.strftime('%d/%m/%Y') if beneficiaire.materiaux_recus.exists() else '...'}<br/>
    """
    # Note: Pour la date, on prend celle du premier matériel du lot, c'est approximatif mais suffit pour la démo.
    # Idéalement, on passerait la date en paramètre.
    
    elements.append(Paragraph(benef_info, normal_style))
    elements.append(Spacer(1, 0.5*cm))

    # Tableau du Matériel
    elements.append(Paragraph("<b>Matériel donné :</b>", normal_style))
    
    data = [['N° Inv.', 'Type', 'Marque', 'Modèle', 'Observations']]
    
    for m in materiels:
        # Récupération des observations (rapport diagnostic ou pièces changées)
        # Pour un PC, on peut aller chercher l'objet enfant
        obs = ""
        if hasattr(m, 'ordinateur') and m.ordinateur:
            obs = f"Linux: {m.ordinateur.linux_distro or 'Non'}"
            if m.ordinateur.ram_go:
                obs += f", RAM: {m.ordinateur.ram_go}Go"
        elif hasattr(m, 'ecran') and m.ecran:
             if m.ecran.diagonale_pouces:
                 obs = f"{m.ecran.diagonale_pouces} pouces"
        
        data.append([
            m.numero_inventaire,
            m.get_type_materiel_display(),
            m.marque.nom if m.marque else '-',
            m.modele or '-',
            obs
        ])

    t = Table(data, colWidths=[2.5*cm, 2.5*cm, 3*cm, 4*cm, 5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 1.5*cm))

    # Clause de responsabilité / Signature
    clause_text = """
    <b>Engagement du bénéficiaire :</b><br/><br/>
    Je soussigné(e), déclare recevoir le matériel listé ci-dessus en bon état de fonctionnement.
    Je m'engage à l'utiliser dans le respect de la législation en vigueur et à ne pas le revendre.
    Je comprends que ce don est fait à titre gratuit et solidaire.
    <br/><br/>
    Fait pour servir et valoir ce que de droit.
    """
    elements.append(Paragraph(clause_text, normal_style))
    elements.append(Spacer(1, 2*cm))

    # Zone de signature
    sig_data = [
        ["Signature du Responsable Association", "Signature du Bénéficiaire"],
        ["", ""],
        ["", ""],
        ["", ""],
        ["(Lu et approuvé)", "(Lu et approuvé)"]
    ]
    t_sig = Table(sig_data, colWidths=[7*cm, 7*cm])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 4), (-1, 4), 9),
        ('TOPPADDING', (0, 0), (-1, 0), 20),
        ('BOTTOMPADDING', (0, 4), (-1, 4), 10),
    ]))
    # On dessine une ligne pour signer (astuce avec GRID partiel ou dessin, ici on laisse blanc pour signer à la main)
    elements.append(t_sig)

    doc.build(elements)
    return response

