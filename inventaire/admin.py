from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum 
from django.utils.safestring import mark_safe
from django import forms
from .models import (
    Marque, 
    Benevole, 
    Beneficiaire, 
    Intervention, 
    Ordinateur, 
    Ecran, 
    Peripherique,
    PieceDetachee,
)

# ==============================================================================
# BENEVOLE
# ==============================================================================
class BenevoleForm(forms.ModelForm):
    class Meta:
        model = Benevole
        fields = '__all__'
        widgets = {
            'specialites': forms.CheckboxSelectMultiple(choices=Benevole.SPECIALITE_CHOICES),
        }

@admin.register(Benevole)
class BenevoleAdmin(admin.ModelAdmin):
    form = BenevoleForm
    list_display = ('user', 'get_prenom', 'get_groups_display', 'actif', 'get_specialites_display')
    list_filter = ('actif', 'specialites')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    
    def get_prenom(self, obj):
        prenom = obj.user.first_name
        if prenom:
            return prenom
        else:
            return ''
    get_prenom.short_description = "Prénom"
    get_prenom.admin_order_field = 'user__first_name'

    def get_groups_display(self, obj):
        groups = obj.user.groups.all()
        if not groups:
            return "-"
        return ", ".join([g.name for g in groups])
    get_groups_display.short_description = "Groupes"

    def get_specialites_display(self, obj):
        if not obj.specialites:
            return "-"
        choices_dict = dict(Benevole.SPECIALITE_CHOICES)
        if isinstance(obj.specialites, list):
            return ", ".join([choices_dict.get(k, k) for k in obj.specialites])
        return "-"
    get_specialites_display.short_description = "Spécialités"

# ==============================================================================
# BENEFICIAIRE
# ==============================================================================
@admin.register(Beneficiaire)
class BeneficiaireAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'telephone', 'email', 'date_creation')
    search_fields = ('nom', 'prenom', 'email')
    list_filter = ('date_creation',)

# ==============================================================================
# INTERVENTION
# ==============================================================================
class InterventionInline(admin.StackedInline):
    model = Intervention
    extra = 0
    fields = ('date_heure', 'benevole', 'type_action', 'commentaire')
    readonly_fields = ('date_heure', 'benevole') # Le bénévole connecté sera défini automatiquement si besoin
    verbose_name = "Journal d'interventions"
    verbose_name_plural = "Journal d'interventions"
    classes = ('collapse',)

@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    list_display = ('date_heure', 'materiel', 'benevole', 'type_action', 'commentaire_court')
    list_filter = ('type_action', 'date_heure', 'benevole')
    search_fields = ('materiel__numero_inventaire', 'commentaire', 'benevole__username')
    readonly_fields = ('date_heure', 'materiel', 'benevole', 'type_action', 'commentaire')
    
    def commentaire_court(self, obj):
        return (obj.commentaire[:50] + '...') if len(obj.commentaire) > 50 else obj.commentaire
    commentaire_court.short_description = "Commentaire"

# ==============================================================================
# MARQUE
# ==============================================================================
@admin.register(Marque)
class MarqueAdmin(admin.ModelAdmin):
    list_display = ('nom', 'site_web')
    search_fields = ('nom',)
    ordering = ('nom',)

# ==============================================================================
# MATERIEL (Parent commun pour Ordinateur, Ecran, Peripherique)
# ==============================================================================
# Nous utilisons une classe de base pour éviter de répéter les inlines et configurations communes
class MaterielParentAdmin(admin.ModelAdmin):
    inlines = [InterventionInline]
    readonly_fields = ('numero_inventaire', 'date_sortie', 'get_categorie_provenance') # Ajout de l'affichage de la catégorie
    
    # On retire les save_model personnalisés car la logique est maintenant dans modele.py (Materiel.save)

@admin.register(Ordinateur)
class OrdinateurAdmin(MaterielParentAdmin):

    # Liste d'inventaire
    list_display = ('numero_inventaire', 'categorie', 'marque', 'modele', 'cpu_score', 'ram_go', 'statut', 'cout_reparation_total_col', 'linux_installe_col', 'benevole_en_charge')
    list_filter = ('statut', 'categorie', 'marque', 'linux_installe')
    search_fields = ('numero_inventaire', 'marque__nom', 'modele', 'cpu', 'numero_serie')

    # Calcul de la somme des coûts des pièces détachées liées à cet ordinateur
    def cout_reparation_total_col(self, obj):
        total = obj.pieces_installees.aggregate(total=Sum('cout_achat'))['total']
        
        if total is None:
            return "0,00 €"
        
        return f"{total:.2f} €"
    
    cout_reparation_total_col.short_description = "Coût Pièces"
    cout_reparation_total_col.admin_order_field = None 

    # Fiche d'édition
    fieldsets = (
        ('Identification & Flux', {
            'fields': ('marque', 'modele', 'numero_serie', 'statut', 'date_entree', 'poids_entree_kg', 'provenance', 'provenance_precisions', 'get_categorie_provenance')
        }),
        ('Catégorie & Hardware de base', {
            'fields': ('categorie', 'cpu', 'cpu_score', 'ram_go', 'ram_nb_barrettes', 'ram_type')
        }),
        ('Disques', {
            'fields': ('disque_principal_type', 'disque_principal_go', 'disque_secondaire_type', 'disque_secondaire_go')
        }),
        ('Spécifique PC Portable', {
            'fields': ('a_alimentation', 'etat_batterie', 'ecran_diagonale_pouces'),
            'classes': ('collapse',)
        }),
        ('Détail hardware', {
            'fields': ('statut_wifi', 'a_carte_graphique_dediee', 'modele_gpu')
        }),
        ('Configuration Linux & Logiciels', {
            'fields': ('linux_installe', 'linux_distro', 'date_maj_os', 'onlyoffice_installe', 'logiciel_photo', 'media_player', 'firefox_configure'),
            'classes': ('collapse',)
        }),
        ('Sortie (Don / Recyclage)', {
            'fields': ('beneficiaire', 'organisme_recyclage', 'poids_sortie_kg', 'date_sortie'),
            'classes': ('collapse',)
        }),
    )

    def linux_installe_col(self, obj):
        if obj.linux_installe:
            return format_html('<span style="color:green; font-weight:bold;">✔ {}</span>', obj.linux_distro or "Linux")
        return mark_safe('<span style="color:red;">✘ Non installé</span>')
    linux_installe_col.short_description = "État Linux"



@admin.register(Ecran)
class EcranAdmin(MaterielParentAdmin):
    list_display = ('numero_inventaire', 'marque', 'modele', 'diagonale_pouces', 'statut', 'poids_entree_kg')
    list_filter = ('statut', 'marque', 'diagonale_pouces')
    search_fields = ('numero_inventaire', 'marque__nom', 'modele', 'numero_serie')

    fieldsets = (
        ('Identification', {'fields': ('marque', 'modele', 'numero_serie', 'statut')}),
        ('Caractéristiques', {'fields': ('diagonale_pouces', 'resolution', 'connectique')}),
        ('Flux & Poids', {'fields': ('date_entree', 'poids_entree_kg', 'provenance', 'provenance_precisions', 'benevole_en_charge')}),
        ('Sortie', {'fields': ('beneficiaire', 'organisme_recyclage', 'poids_sortie_kg', 'date_sortie')}),
    )
    # PAS DE save_model ICI -> Géré par le modèle

@admin.register(Peripherique)
class PeripheriqueAdmin(MaterielParentAdmin):
    list_display = ('numero_inventaire', 'type_periph', 'marque', 'avec_cable', 'statut', 'poids_entree_kg')
    list_filter = ('statut', 'type_periph', 'avec_cable')
    search_fields = ('numero_inventaire', 'marque__nom', 'modele')

    fieldsets = (
        ('Identification', {'fields': ('type_periph', 'marque', 'modele', 'numero_serie', 'statut')}),
        ('Détails', {'fields': ('connectique', 'avec_cable')}),
        ('Flux & Poids', {'fields': ('date_entree', 'poids_entree_kg', 'provenance', 'provenance_precisions', 'benevole_en_charge')}),
        ('Sortie', {'fields': ('beneficiaire', 'organisme_recyclage', 'poids_sortie_kg', 'date_sortie')}),
    )
    # PAS DE save_model ICI -> Géré par le modèle



# ==============================================================================
# PIÈCES DÉTACHÉES
# ==============================================================================
@admin.register(PieceDetachee)
class PieceDetacheeAdmin(admin.ModelAdmin):
    list_display = ('numero_inventaire', 'categorie', 'specifications_courtes', 'etat', 'cout_achat', 'pc_destination_link', 'date_entree_stock')
    list_filter = ('categorie', 'etat', 'pc_origine', 'pc_destination')
    search_fields = ('numero_inventaire', 'marque', 'modele', 'specifications', 'pc_origine__numero_inventaire')
    
    readonly_fields = ('numero_inventaire', 'date_entree_stock', 'date_sortie_stock')
    
    fieldsets = (
        ('Identification', {
            'fields': ('numero_inventaire', 'categorie', 'marque', 'modele', 'specifications')
        }),
        ('Traçabilité', {
            'fields': ('pc_origine', 'pc_destination')
        }),
        ('État & Stock', {
            'fields': ('etat', 'emplacement', 'poids_kg', 'cout_achat')
        }),
        ('Dates', {
            'fields': ('date_entree_stock', 'date_sortie_stock'),
            'classes': ('collapse',)
        }),
    )

    def specifications_courtes(self, obj):
        return (obj.specifications[:40] + '...') if len(obj.specifications) > 40 else obj.specifications
    specifications_courtes.short_description = "Spécifications"

    def pc_origine_link(self, obj):
        if obj.pc_origine:
            return format_html('<a href="/admin/votre_app_nom/materiel/{}/change/">{}</a>', 
                               obj.pc_origine.id, obj.pc_origine.numero_inventaire)
        return "-"
    pc_origine_link.short_description = "PC Origine"

    def pc_destination_link(self, obj):
        if obj.pc_destination:
            return format_html('<a href="/admin/votre_app_nom/materiel/{}/change/">{}</a>', 
                               obj.pc_destination.id, obj.pc_destination.numero_inventaire)
        return "-"
    pc_destination_link.short_description = "PC Destination"

    # Ajout d'un bouton d'action rapide dans la fiche
    def generate_inv_button(self, obj):
        if obj.numero_inventaire:
            return format_html('<span style="color:green;">✅ {}</span>', obj.numero_inventaire)
        
        # Si pas de numéro, on affiche un lien/bouton pour en générer un
        # (Nécessite une vue personnalisée ou une action admin)
        return format_html('<a href="?action=generate_inv&ids={}">🏷️ Générer N°</a>', obj.pk)
    
    generate_inv_button.short_description = "Inventaire"

    # Ou plus simplement, utiliser les "actions" en masse pour générer les numéros de plusieurs pièces d'un coup
    actions = ['generer_numeros_pour_selection']

    def generer_numeros_pour_selection(self, request, queryset):
        count = 0
        for piece in queryset:
            if not piece.numero_inventaire:
                piece.numero_inventaire = piece.generer_numero_inventaire()
                piece.save()
                count += 1
        self.message_user(request, f"{count} numéros d'inventaire générés avec succès.")
    
    generer_numeros_pour_selection.short_description = "🏷️ Générer N° Inventaire pour les pièces sélectionnées"

    # PAS DE save_model ICI -> Géré par le modèle PieceDetachee.save()
