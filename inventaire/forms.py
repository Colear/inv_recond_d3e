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

    # Champ virtuel pour la catégorie (n'existe pas dans le modèle)
    categorie_provenance = forms.ChoiceField(
        choices=Materiel.CATEGORIES_PROVENANCE,
        label="Type de provenance",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_categorie_provenance'})
    )

    class Meta:
        model = Materiel
        fields = ['poids_entree_kg', 'type_materiel', 'provenance', 'provenance_precisions', 'marque', 'modele']
        widgets = {
            'poids_entree_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': 'Ex: 2.5'}),
            'type_materiel': forms.Select(attrs={'class': 'form-select', 'id': 'id_type_materiel'}),
            'provenance': forms.Select(attrs={'class': 'form-select', 'id': 'id_provenance'}),
            'provenance_precisions': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom précis...'}),
            'marque': forms.Select(attrs={'class': 'form-select', 'id': 'id_marque'}),
            'modele': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optionnel'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Rendre les champs optionnels
        self.fields['marque'].required = False
        self.fields['modele'].required = False
        self.fields['provenance_precisions'].required = False
        
        # Améliorer le champ Marque avec tri alphabétique
        self.fields['marque'].queryset = Marque.objects.order_by('nom')
        
        # S'assurer que le widget a bien la classe Bootstrap (au cas où le Meta ne suffise pas)
        self.fields['marque'].widget.attrs.update({'class': 'form-select'})
        
        # Optionnel : ajouter une valeur vide explicite "-----"
        # (Django le fait souvent par défaut pour les champs non-required, mais c'est plus clair ainsi)
        self.fields['marque'].empty_label = "Inconnue / Sans marque"
    