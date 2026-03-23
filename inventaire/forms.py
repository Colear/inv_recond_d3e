from django import forms
from .models import Benevole



"""====== BenevoleForm ========================================================
Formulaire la saisie des bénévoles, notamment dans l'admin, permettant de
saisir les spécialités sous forme de checkbox.
============================================================================"""

class BenevoleForm(forms.ModelForm):
    class Meta:
        model = Benevole
        fields = ['telephone', 'specialites', 'actif']
        widgets = {
            # Le widget CheckboxSelectMultiple affiche une case à cocher par choix
            'specialites': forms.CheckboxSelectMultiple,
            
            # Alternative : Une liste multiple avec Ctrl+Clic
            # 'specialites': forms.SelectMultiple, 
        }
