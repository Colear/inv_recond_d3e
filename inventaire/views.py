# inventaire/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import timedelta
from .models import Ordinateur, Ecran, Peripherique, Materiel, Marque
from .forms import NouveauMaterielForm



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
        derniers_materiaux = Materiel.objects.select_related('marque', 'benevole_en_charge').order_by('-date_entree')[:5]

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
    paginate_by = 25  # Nombre d'éléments par page

    def get_queryset(self):
        # On part de la base : tous les matériels ordonnés par date d'entrée (plus récent en premier)
        queryset = Materiel.objects.select_related('marque', 'benevole_en_charge', 'beneficiaire').order_by('-date_entree')

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
    success_url = '/inventaire/inventaire' # Redirige vers la liste après succès

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

