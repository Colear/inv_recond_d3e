from django import forms
from ..models import Ecran, Ordinateur, Materiel, Marque

class MaterielBaseForm(forms.ModelForm):
    class Meta:
        model = Materiel
        fields = ['date_achat', 'statut', 'notes']
        widgets = {
            'date_achat': forms.DateInput(attrs={'type': 'date'}),
        }

class EcranForm(MaterielBaseForm):
    class Meta:
        model = Ecran
        # On liste TOUS les champs SAUF 'marque'
        fields = [
            'modele', 'diagonale_pouces', 'resolution', 'connectique'
        ]

class OrdinateurForm(MaterielBaseForm):
    class Meta:
        model = Ordinateur
        # On liste TOUS les champs SAUF 'marque'
        fields = [
            'modele', 'cpu', 'ram_go', 'stockage_go', 'type_stockage', 'systeme_exploitation'
        ]

'''
class EcranForm(MaterielBaseForm):
    class Meta(MaterielBaseForm.Meta):
        model = Ecran
        fields = MaterielBaseForm.Meta.fields + ['marque', 'modele', 'diagonale_pouces', 'resolution', 'connectique']

class OrdinateurForm(MaterielBaseForm):
    class Meta(MaterielBaseForm.Meta):
        model = Ordinateur
        fields = MaterielBaseForm.Meta.fields + ['marque', 'modele', 'cpu', 'ram_go', 'stockage_go', 'type_stockage', 'systeme_exploitation']
'''

class MarqueForm(forms.ModelForm):
    class Meta:
        model = Marque
        fields = ['marque', 'site_web']
        # On peut rendre le site web optionnel même si le modèle l'autorise déjà
        widgets = {
            'marque': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Dell, HP, Apple...'}),
            'site_web': forms.URLInput(attrs={'class': 'form-control', 'placeholder': ''}),
        }
