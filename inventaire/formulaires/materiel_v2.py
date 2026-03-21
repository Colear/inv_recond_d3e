from django import forms
from ..models import Ecran, Ordinateur, Materiel

''' A virer
class MaterielBaseForm(forms.ModelForm):
    class Meta:
        model = Materiel
        fields = ['date_achat', 'statut', 'notes']
        widgets = {
            'date_achat': forms.DateInput(attrs={'type': 'date'}),
        }
'''
        
class TypeChoiceForm(forms.Form):
    TYPE_CHOICES = [
        ('', '--- Sélectionnez un type ---'),
        ('ecran', 'Écran'),
        ('ordinateur', 'Ordinateur'),
    ]
    type_materiel = forms.ChoiceField(choices=TYPE_CHOICES, label="Type de matériel")

class EcranForm(MaterielBaseForm):
    class Meta(MaterielBaseForm.Meta):
        model = Ecran
        fields = MaterielBaseForm.Meta.fields + ['marque', 'modele', 'diagonale_pouces', 'resolution', 'connectique']

class OrdinateurForm(MaterielBaseForm):
    class Meta(MaterielBaseForm.Meta):
        model = Ordinateur
        fields = MaterielBaseForm.Meta.fields + ['marque', 'modele', 'cpu', 'ram_go', 'stockage_go', 'type_stockage', 'systeme_exploitation']

