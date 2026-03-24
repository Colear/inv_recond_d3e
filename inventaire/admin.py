from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django import forms
from .models import (
    Marque, 
    Benevole, 
    Beneficiaire, 
    Intervention, 
    Ordinateur, 
    DisqueDur, 
    Ecran, 
    Peripherique
)



"""====== Benevole ============================================================
Extension de la partie utilisateur de Django pour y ajouter des données
sur les bénévoles.
On utilise dans l'admin un formulaire spécifique pour pouvoir utiliser les
cases à cocher des spécialités.
============================================================================""" 

class BenevoleForm(forms.ModelForm):
    class Meta:
        model = Benevole
        fields = '__all__'
        widgets = {
            # Force l'utilisation des cases à cocher
            'specialites': forms.CheckboxSelectMultiple(choices=Benevole.SPECIALITE_CHOICES),
        }

@admin.register(Benevole)
class BenevoleAdmin(admin.ModelAdmin):
    form = BenevoleForm  # <--- On assigne explicitement le formulaire personnalisé
    list_display = ('user', 'telephone', 'actif', 'get_specialites_display')
    list_filter = ('actif', 'specialites')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    
    def get_specialites_display(self, obj):
        if not obj.specialites:
            return "-"
        choices_dict = dict(Benevole.SPECIALITE_CHOICES)
        if isinstance(obj.specialites, list):
            return ", ".join([choices_dict.get(k, k) for k in obj.specialites])
        return "-"
    get_specialites_display.short_description = "Spécialités"



"""====== Beneficiaire ========================================================
Information sur les bénéficiaires de don.
============================================================================""" 

@admin.register(Beneficiaire)
class BeneficiaireAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'telephone', 'email', 'date_creation')
    search_fields = ('nom', 'prenom', 'email')
    list_filter = ('date_creation',)



"""====== Intervention ========================================================
Notes de travail et de prise en charge par les bénévoles. Plus de papier !
La class Inline permet l'ajout en ligne directement dans les ordis.
============================================================================""" 

class InterventionInline(admin.StackedInline):
    model = Intervention
    extra = 0
    fields = ('date_heure', 'benevole', 'type_action', 'commentaire')
    readonly_fields = ('date_heure', 'benevole')
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



"""====== Marque ==============================================================
Table externe qui sera utilisé quelque soit le type de matériel pour choisir
la marque du matériel saisi.
============================================================================"""

@admin.register(Marque)
class MarqueAdmin(admin.ModelAdmin):
    list_display = ('nom', 'site_web')
    search_fields = ('nom',)
    ordering = ('nom',)



"""====== DisqueDur ===========================================================
Permet de stocker les disques durs, avec éventuellement un numéro 
d'inventaire quand ils sont testés en remis en stock.
La class Inline permet l'ajout en ligne directement dans les ordis.
============================================================================"""

class DisqueDurInline(admin.TabularInline):
    model = DisqueDur
    extra = 1
    fields = ('type_disque', 'capacite_go', 'marque', 'est_sain', 'contient_donnees', 'numero_inventaire_disque')
    verbose_name = "Disque Dur"
    verbose_name_plural = "Disques Durs"

@admin.register(DisqueDur)
class DisqueDurAdmin(admin.ModelAdmin):
    list_display = ('numero_inventaire_disque', 'type_disque', 'capacite_go', 'marque', 'modele', 'est_sain', 'contient_donnees', 'ordinateur_link')
    list_filter = ('est_sain', 'type_disque', 'contient_donnees', 'numero_inventaire_disque')
    search_fields = ('numero_inventaire_disque', 'numero_serie', 'marque', 'modele')
    readonly_fields = ('numero_inventaire_disque',) # Optionnel : si vous voulez qu'il soit auto-généré aussi
    
    def ordinateur_link(self, obj):
        if obj.ordinateur:
            return format_html('<a href="../ordinateur/{}/change/">{}</a>', obj.ordinateur.id, obj.ordinateur.numero_inventaire)
        return "<span style='color:grey;'>En stock (Dissocié)</span>"
    ordinateur_link.short_description = "Ordinateur lié"

    actions = ['marquer_comme_sain_efface']

    def marquer_comme_sain_efface(self, request, queryset):
        queryset.update(est_sain=True, contient_donnees=False)
        self.message_user(request, f"{queryset.count()} disques marqués comme sains et effacés.")
    marquer_comme_sain_efface.short_description = "Marquer comme sain et effacé (Prêt stock)"



"""====== Ordinateur ==========================================================
    Classe fille de Materiel destinée aux ordis.
============================================================================""" 

@admin.register(Ordinateur)
class OrdinateurAdmin(admin.ModelAdmin):
    list_display = ('numero_inventaire', 'categorie', 'marque', 'modele', 'cpu_score', 'statut', 'linux_installe_col', 'benevole_en_charge')
    list_filter = ('statut', 'categorie', 'marque', 'linux_installe', 'a_carte_graphique_dediee', 'a_carte_wifi')
    search_fields = ('numero_inventaire', 'marque__nom', 'modele', 'cpu', 'numero_serie')
    
    inlines = [DisqueDurInline, InterventionInline]
    
    # AJOUT : Rendre le numéro d'inventaire visible en lecture seule
    readonly_fields = ('numero_inventaire', 'date_sortie') 

    fieldsets = (
        ('Identification & Flux', {
            # CORRECTION : 'numero_inventaire' retiré d'ici car il est en readonly_fields
            'fields': ('marque', 'modele', 'numero_serie', 'statut', 'date_entree', 'poids_entree_kg', 'provenance')
        }),
        ('Catégorie & Hardware de base', {
        #    'fields': ('type_materiel', 'categorie', 'cpu', 'ram_go', 'ram_nb_barrettes', 'ram_type', 'a_carte_graphique_dediee', 'modele_gpu')
            'fields': ('categorie', 'cpu', 'cpu_score', 'ram_go', 'ram_nb_barrettes', 'ram_type', 'a_carte_graphique_dediee', 'modele_gpu', 'a_carte_wifi')
        }),
        ('Spécifique PC Portable', {
            'fields': ('a_alimentation', 'etat_batterie', 'ecran_diagonale_pouces'),
            'classes': ('collapse',)
        }),
        ('Configuration Linux & Logiciels', {
            'fields': ('linux_installe', 'linux_distro', 'date_maj_os', 'onlyoffice_installe', 'logiciel_photo', 'media_player', 'firefox_configure'),
            'classes': ('collapse',)
        }),
        ('Gestion & Réparation', {
            'fields': ('benevole_en_charge', 'date_prise_en_charge', 'pieces_changees', 'cout_reparation'),
            'classes': ('collapse',)
        }),
        ('Sortie (Don / Recyclage)', {
            'fields': ('beneficiaire', 'organisme_recyclage', 'poids_sortie_kg', 'date_sortie'),
            'classes': ('collapse',)
        }),
    )

    def linux_installe_col(self, obj):
        if obj.linux_installe:
            # Affiche un tick vert avec le nom de la distrib
            return format_html('<span style="color:green; font-weight:bold;">✔ {}</span>', obj.linux_distro or "Linux")
        # Affiche une croix rouge
        return mark_safe('<span style="color:red;">✘ Non installé</span>')
    
    # Titre de la colonne dans l'admin
    linux_installe_col.short_description = "État Linux"



"""====== Ecran ===============================================================
    Classe fille de Materiel destinée aux écrans.
============================================================================"""

@admin.register(Ecran)
class EcranAdmin(admin.ModelAdmin):
    list_display = ('numero_inventaire', 'marque', 'modele', 'diagonale_pouces', 'statut', 'poids_entree_kg')
    list_filter = ('statut', 'marque', 'diagonale_pouces')
    search_fields = ('numero_inventaire', 'marque__nom', 'modele', 'numero_serie')
    
    readonly_fields = ('numero_inventaire', 'date_sortie')

    fieldsets = (
        ('Identification', {'fields': ('marque', 'modele', 'numero_serie', 'statut')}),
        ('Caractéristiques', {'fields': ('diagonale_pouces', 'resolution', 'connectique')}),
        ('Flux & Poids', {'fields': ('type_materiel', 'date_entree', 'poids_entree_kg', 'provenance', 'benevole_en_charge')}),
        ('Sortie', {'fields': ('beneficiaire', 'organisme_recyclage', 'poids_sortie_kg', 'date_sortie')}),
    )



"""====== Peripherique ========================================================
    Classe fille de Materiel destinée aux periphériques (clavier, ...).
============================================================================"""

@admin.register(Peripherique)
class PeripheriqueAdmin(admin.ModelAdmin):
    list_display = ('numero_inventaire', 'type_periph', 'marque', 'avec_cable', 'statut', 'poids_entree_kg')
    list_filter = ('statut', 'type_periph', 'avec_cable')
    search_fields = ('numero_inventaire', 'marque__nom', 'modele')

    readonly_fields = ('numero_inventaire', 'date_sortie')

    fieldsets = (
        ('Identification', {'fields': ('type_periph', 'marque', 'modele', 'numero_serie', 'statut')}),
        ('Détails', {'fields': ('connectique', 'avec_cable')}),
        ('Flux & Poids', {'fields': ('date_entree', 'poids_entree_kg', 'provenance', 'benevole_en_charge')}),
        ('Sortie', {'fields': ('beneficiaire', 'organisme_recyclage', 'poids_sortie_kg', 'date_sortie')}),
    )

