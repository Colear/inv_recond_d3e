from django import forms
from django.forms import inlineformset_factory
from ..models import Materiel, Marque, Ordinateur, Peripherique, DisqueDur



"""====== NouveauMateriel =====================================================
    Saisie rapide d'un nouveau matériel.
    Aller à l'essentiel, le reste sera renseigné dans l'étape diagnostic
============================================================================"""

class NouveauMaterielForm(forms.ModelForm):

    # Champs spécifiques à afficher conditionnellement
    categorie_pc = forms.ChoiceField(
        choices=Ordinateur.CATEGORIE_CHOICES,
        required=False,
        label="Catégorie (si PC)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    categorie_periph = forms.ChoiceField(
        choices=Peripherique.TYPE_PERIPH_CHOICES,
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



"""====== DiagnosticRepa ======================================================
    Formulaire commun pour le diagnostic et la réparation
============================================================================"""

# --- 1. Formulaire Principal (Diagnostic + Répa + Linux) ---
class DiagnosticRepaForm(forms.ModelForm):
    class Meta:
        model = Ordinateur
        # On sélectionne les champs pertinents pour cette phase
        fields = [
            'cpu', 'cpu_score', 
            'ram_go', 'ram_nb_barrettes', 'ram_type',
            'a_carte_wifi', 'a_carte_graphique_dediee', 'modele_gpu',
            'rapport_diagnostic', 
            'pieces_changees', 'cout_reparation',
            'linux_installe', 'linux_distro', 'date_maj_os',
            'onlyoffice_installe', 'logiciel_photo', 'media_player', 'firefox_configure',
            'statut' # Important pour savoir où on en est
        ]
        widgets = {
            'cpu': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Intel i5-8500'}),
            'cpu_score': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 8500'}),
            'ram_go': forms.NumberInput(attrs={'class': 'form-control'}),
            'ram_nb_barrettes': forms.NumberInput(attrs={'class': 'form-control'}),
            'ram_type': forms.Select(attrs={'class': 'form-select'}),
            'a_carte_wifi': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'a_carte_graphique_dediee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'rapport_diagnostic': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Problèmes constatés...'}),
            'pieces_changees': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'cout_reparation': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'linux_distro': forms.Select(attrs={'class': 'form-select'}),
            'date_maj_os': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'logiciel_photo': forms.Select(attrs={'class': 'form-select'}),
            'media_player': forms.Select(attrs={'class': 'form-select'}),
            'statut': forms.Select(attrs={'class': 'form-select fw-bold'}), # Pour changer le statut facilement
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Rendre ces champs optionnels au niveau du formulaire
        # Ainsi, même s'ils sont vides ou absents, la validation Python passera.
        self.fields['cout_reparation'].required = False
        self.fields['statut'].required = False
        # On peut même désactiver le select de statut dans le HTML pour forcer l'usage des boutons
        self.fields['statut'].widget.attrs['readonly'] = True 
        self.fields['statut'].help_text = "Ce champ est géré automatiquement par les boutons d'action."
        
        # Optionnel : mettre une valeur initiale visuelle pour cout_reparation
        if self.instance.pk and self.instance.cout_reparation == 0:
            self.fields['cout_reparation'].initial = 0



# --- 2. Formset pour les Disques Durs ---
# Permet d'ajouter/supprimer dynamiquement des lignes de disques
DisqueFormSet = inlineformset_factory(
    Ordinateur, 
    DisqueDur,
    fields=['type_disque', 'capacite_go', 'marque', 'modele', 'numero_serie', 'est_sain', 'contient_donnees', 'numero_inventaire_disque'],
    extra=1, # Nombre de lignes vides par défaut
    can_delete=True, # Permet de cocher une case pour supprimer un disque
    widgets={
        'type_disque': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        'capacite_go': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Go'}),
        'marque': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        'est_sain': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        'contient_donnees': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        'numero_inventaire_disque': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'DSK-####'}),
    }
)
