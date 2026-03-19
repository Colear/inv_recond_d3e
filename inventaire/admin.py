from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Categorie, MaterielReference, Equipement

@admin.register(Equipement)
class EquipementAdmin(admin.ModelAdmin):
    list_display = ('num_inventaire', 'reference', 'statut', 'utilisateur', 'date_entree')
    list_filter = ('statut', 'reference__categorie', 'reference__marque')
    search_fields = ('num_inventaire', 'reference__modele', 'utilisateur__username')
    raw_id_fields = ('utilisateur',)  # Plus efficace si beaucoup d'utilisateurs

admin.site.register(Categorie)
admin.site.register(MaterielReference)
