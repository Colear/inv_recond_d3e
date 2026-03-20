from django import forms
from ..models import Ecran, Ordinateur, Materiel

class MaterielBaseForm(forms.ModelForm):
    class Meta:
        model = Materiel
        fields = ['date_achat', 'statut', 'notes']
        widgets = {
            'date_achat': forms.DateInput(attrs={'type': 'date'}),
        }

class EcranForm(MaterielBaseForm):
    class Meta(MaterielBaseForm.Meta):
        model = Ecran
        fields = MaterielBaseForm.Meta.fields + ['marque', 'modele', 'diagonale_pouces', 'resolution', 'connectique']

class OrdinateurForm(MaterielBaseForm):
    class Meta(MaterielBaseForm.Meta):
        model = Ordinateur
        fields = MaterielBaseForm.Meta.fields + ['marque', 'modele', 'cpu', 'ram_go', 'stockage_go', 'type_stockage', 'systeme_exploitation']
