from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset
from ..models import Ordinateur, Ecran, Peripherique



"""====== DiagnosticRepa ======================================================
    Formulaire commun pour le diagnostic et la réparation
============================================================================"""

class DiagnosticRepaForm(forms.ModelForm):
    
    # Champs virtuels pour aider à la validation conditionnelle (optionnel, mais utile)
    # On pourra s'en servir dans le clean() pour savoir quel bouton a été cliqué si besoin
    
    class Meta:
        model = Ordinateur
        # On inclut TOUS les champs nécessaires (Hardware + Software)
        fields = [
            # Type d'ordi
            'categorie',
            # Hardware - Diagnostic
            'cpu', 'cpu_score', 'ram_go', 'ram_nb_barrettes', 'ram_type',
            'statut_wifi', 'a_carte_graphique_dediee', 'modele_gpu',
            'rapport_diagnostic',
            # Hardware - Disques
            'disque_principal_type', 'disque_principal_go',
            'disque_secondaire_type', 'disque_secondaire_go',
            # Hardware - Portables
            'a_alimentation', 'etat_batterie', 'ecran_diagonale_pouces',
            # Software - Configuration
            'linux_installe', 'linux_distro', 'date_maj_os',
            'onlyoffice_installe', 'logiciel_photo', 'media_player', 'firefox_configure',
        ]
        widgets = {
            'cpu': forms.TextInput(attrs={'placeholder': 'Ex: Intel i5-8500'}),
            'rapport_diagnostic': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Problèmes constatés, tests...'}),
            'pieces_changees': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Liste des pièces remplacées'}),
            'etat_batterie': forms.Select(attrs={'class': 'form-select'}),
            'linux_distro': forms.Select(attrs={'class': 'form-select'}),
            'date_maj_os': forms.DateInput(attrs={'type': 'date'}),
            'disque_principal_type': forms.Select(attrs={'class': 'form-select'}),
            'disque_secondaire_type': forms.Select(attrs={'class': 'form-select'}),
            'disque_principal_go': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 500'}),
            'disque_secondaire_go': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 500'}),
        }

    def __init__(self, *args, **kwargs):
        self.action = kwargs.pop('action', None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'

        # Utilisation custom de crispy :
        #  - crispy ne doit pas afficher les tags <form> pour nous permettre de gérer les
        #    champs un par un avec |as_crispy_field
        #  - crispy ne doit pas afficher les labels, on les gère dans le template (permet
        #    de crontrôler les * des champs obligatoires)
        self.helper.form_tag = False
        self.helper.form_show_labels = False

        # Pour que ce soit le clean qui gère les champs obligatoire plutôt que Django, on
        # met tous les champs traités par le clean comme facultatif
        self.fields['cpu'].required = False
        self.fields['cpu_score'].required = False
        self.fields['ram_go'].required = False
        self.fields['disque_principal_type'].required = False        
        self.fields['disque_principal_go'].required = False
        self.fields['rapport_diagnostic'].required = False

        # Layout simplifié : juste les champs, la mise
        # en page est faite dans le template
        self.helper.layout = Layout(
            Fieldset( "Diagnostic & configuration logicielle",
                # Hardware
                'cpu', 'cpu_score', 'ram_go', 'ram_nb_barrettes', 'ram_type', 
                'statut_wifi', 'disque_principal_type','disque_principal_go','disque_secondaire_type','disque_secondaire_go','a_carte_graphique_dediee', 'modele_gpu',
                'rapport_diagnostic', 'a_alimentation', 'etat_batterie',
                # Software
                'linux_installe', 'linux_distro', 'date_maj_os',
                'onlyoffice_installe', 'logiciel_photo', 'media_player', 'firefox_configure',
            )
        )


    def clean(self):
        cleaned_data = super().clean()
        
        # Récupération du statut cible (si la vue le passe dans le form ou via POST)
        # Astuce: On peut regarder dans self.data directement
        action = self.data.get('action')
        
        # Définition des actions qui nécessitent un diagnostic COMPLET
        actions_completes = ['validate_diag_release', 'validate_diag_repa', 'validate_repa'] 
        
        if action in actions_completes:
            # Si on veut passer en Réparation/Config, les champs Hardware sont OBLIGATOIRES
            errors = []
            if not cleaned_data.get('cpu'):
                errors.append("Le processeur (CPU) est obligatoire pour valider le diagnostic.")
            if not cleaned_data.get('cpu_score'):
                errors.append("L'indice Passmak est obligatoire pour valider le diagnostic. Allez sur https://www.cpubenchmark.net/cpu-list pour le trouver.")
            if not cleaned_data.get('ram_go'):
                errors.append("La quantité de RAM est obligatoire pour valider le diagnostic.")
            if not cleaned_data.get('disque_principal_type'):
                errors.append("Le type du disque principal est obligatoire pour valider le diagnostic.")
            if not cleaned_data.get('disque_principal_go'):
                errors.append("La taille du disque principal est obligatoire pour valider le diagnostic.")
            if not cleaned_data.get('rapport_diagnostic'):
                errors.append("Un rapport de diagnostic est obligatoire.")
            
            if errors:
                raise forms.ValidationError(errors)
        
        # Si l'action est 'wait_parts' ou 'save_exit', on ne bloque pas (champs optionnels)
        
        return cleaned_data



"""====== DiagnosticEcran =====================================================
    Formulaire pour la mise en diagnostic des écrans
============================================================================"""

class DiagnosticEcranForm(forms.ModelForm):
    class Meta:
        model = Ecran
        fields = ['diagonale_pouces', 'resolution', 'connectique', 'rapport_diagnostic']
        widgets = {
            'rapport_diagnostic': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'diagonale_pouces': forms.Select(attrs={'class': 'form-select'}),
            'resolution': forms.TextInput(attrs={'class': 'form-control'}),
            'connectique': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.action = kwargs.pop('action', None)
        super().__init__(*args, **kwargs)

        # le rapport de diag doit être optionnel pour permettre le workflow
        self.fields['rapport_diagnostic'].required = False 

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'diagonale_pouces',
            'resolution',
            'connectique', 
            'rapport_diagnostic',
        )

    def clean(self):
        cleaned_data = super().clean()

        action = self.data.get('action')
        
        # Liste des actions qui exigent un rapport
        actions_exigeantes = [
            'validate_diag_ok', 
            'validate_diag_parts', 
            'validate_diag_recycle',
            'wait_dismantling'
        ]
        
        if action in actions_exigeantes:
            if not cleaned_data.get('rapport_diagnostic'):
                raise forms.ValidationError("Le rapport de diagnostic est obligatoire.")
        return cleaned_data



"""====== DiagnosticPeripherique ==============================================
    Formulaire pour la mise en diagnostic des périphériques
============================================================================"""

class DiagnosticPeripheriqueForm(forms.ModelForm):
    class Meta:
        model = Peripherique
        fields = ['type_periph', 'avec_cable', 'connectique', 'rapport_diagnostic']
        widgets = {
            'rapport_diagnostic': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'type_periph': forms.Select(attrs={'class': 'form-select'}),
            'avec_cable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'connectique': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.action = kwargs.pop('action', None)
        super().__init__(*args, **kwargs)
        
        # le rapport de diag doit être optionnel pour permettre le workflow
        self.fields['rapport_diagnostic'].required = False 

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'type_periph',
            'avec_cable',
            'connectique',
            'rapport_diagnostic',
        )

    def clean(self):
        cleaned_data = super().clean()

        action = self.data.get('action')
        
        # Liste des actions qui exigent un rapport
        actions_exigeantes = [
            'validate_diag_ok', 
            'validate_diag_parts', 
            'validate_diag_recycle',
            'wait_dismantling'
        ]
        
        if action in actions_exigeantes:
            if not cleaned_data.get('rapport_diagnostic'):
                raise forms.ValidationError("Le rapport de diagnostic est obligatoire.")
        return cleaned_data

