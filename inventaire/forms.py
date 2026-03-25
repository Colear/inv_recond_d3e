# inventaire/forms.py
from django import forms
from .models import Materiel, Marque



"""====== NouveauMateriel =====================================================
    Saisie rapide d'un nouveau matériel.
    Aller à l'essentiel, le reste sera renseigné dans l'étape diagnostic
============================================================================"""

class NouveauMaterielForm(forms.ModelForm):
    # Champs spécifiques à afficher conditionnellement
    categorie_pc = forms.ChoiceField(
        choices=[('FIXE', 'PC Fixe'), ('PORTABLE', 'PC Portable'), ('ALL_IN_ONE', 'All-in-One')],
        required=False,
        label="Catégorie (si PC)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    categorie_periph = forms.ChoiceField(
        choices=[
            ('CLAVIER', 'Clavier'), ('SOURIS', 'Souris'), ('WEBCAM', 'Webcam'),
            ('CASQUE', 'Casque'), ('ENCEINTES', 'Enceintes'), ('HUB', 'Hub USB'), ('AUTRE', 'Autre')
        ],
        required=False,
        label="Type (si Périphérique)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Materiel
        fields = ['poids_entree_kg', 'type_materiel', 'provenance', 'marque', 'modele']
        widgets = {
            'poids_entree_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': 'Ex: 2.5'}),
            'type_materiel': forms.Select(attrs={'class': 'form-select', 'id': 'id_type_materiel'}),
            'provenance': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Don de M. Dupont, Collecte Mairie...'}),
            'marque': forms.Select(attrs={'class': 'form-select', 'id': 'id_marque'}),
            'modele': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optionnel'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Rendre les champs optionnels (comme prévu)
        self.fields['marque'].required = False
        self.fields['modele'].required = False
        
        # 2. Améliorer le champ Marque
        # Ordonner les choix par nom (A-Z) pour faciliter la recherche
        self.fields['marque'].queryset = Marque.objects.order_by('nom')
        
        # S'assurer que le widget a bien la classe Bootstrap (au cas où le Meta ne suffise pas)
        self.fields['marque'].widget.attrs.update({'class': 'form-select'})
        
        # 3. Optionnel : Ajouter une valeur vide explicite "-----"
        # (Django le fait souvent par défaut pour les champs non-required, mais c'est plus clair ainsi)
        self.fields['marque'].empty_label = "Inconnue / Sans marque"
    