from django.db.models import Count, Sum, Q
from django.views.generic import TemplateView
from django.utils import timezone
from django.contrib import messages
from ..mixins import AuthBenevoleMixin
from ..models import Ordinateur, Materiel



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

