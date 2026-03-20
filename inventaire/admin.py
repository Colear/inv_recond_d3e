from django.contrib import admin
from .models import Marque, Materiel, Ecran, Ordinateur

@admin.register(Marque)
class MarqueAdmin(admin.ModelAdmin):
    list_display = ('marque', 'site_web')
    search_fields = ('marque',)

@admin.register(Ecran)
class EcranAdmin(admin.ModelAdmin):
    list_display = ('numero_inventaire', 'marque', 'modele', 'diagonale_pouces', 'statut', 'utilisateur')
    list_filter = ('marque', 'statut', 'diagonale_pouces')
    search_fields = ('numero_inventaire', 'modele', 'numero_serie')
    raw_id_fields = ('utilisateur',) # Utile si beaucoup d'utilisateurs

@admin.register(Ordinateur)
class OrdinateurAdmin(admin.ModelAdmin):
    list_display = ('numero_inventaire', 'marque', 'modele', 'cpu', 'ram_go', 'statut', 'utilisateur')
    list_filter = ('marque', 'statut', 'type_stockage')
    search_fields = ('numero_inventaire', 'modele', 'cpu')
    raw_id_fields = ('utilisateur',)

# Optionnel : Si vous voulez toujours voir la table mère 'Materiel' dans l'admin
admin.site.register(Materiel)
