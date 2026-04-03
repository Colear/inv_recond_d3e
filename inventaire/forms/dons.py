from django import forms
from ..models import Beneficiaire



"""====== BeneficiaireForm ====================================================
    !!! Pas encore utilisée pour le moment ! (en dur dans le template pour
    la démo...) !!!
============================================================================"""

class BeneficiaireForm(forms.ModelForm):
    class Meta:
        model = Beneficiaire
        fields = ['prenom', 'nom', 'email', 'telephone', 'adresse']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Dupont',
                'autocomplete': 'family-name'
            }),
            'prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Jean',
                'autocomplete': 'given-name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'jean.dupont@exemple.com',
                'type': 'email',  # Force le clavier email sur mobile
                'autocomplete': 'email'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '06 12 34 56 78',
                'type': 'tel',  # Force le clavier numérique/téléphone sur mobile
                'autocomplete': 'tel',
                'pattern': '[0-9\s\+\-\(\)]+' # Indice visuel pour le format
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse postale complète',
                'autocomplete': 'street-address'
            }),
        }        
