from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Field
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
            'categorie', 'modele',
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
            'linux_installe', 'linux_distro', 'date_maj_os', 'dns_configures', 'langue_configuree',
            'onlyoffice_installe', 'firefox_configure', 'firefox_extensions', 'logiciel_photo', 'media_player',
            'rapport_configuration'
        ]
        widgets = {
            # les widgets qui ne font que passer des class sont inutiles !
            'cpu': forms.TextInput(attrs={'placeholder': 'Ex: Intel i5-8500'}),
            'rapport_diagnostic': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Problèmes constatés, tests...'}),
            'date_maj_os': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'rapport_configuration': forms.Textarea(attrs={'rows': 3}),            
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
        self.fields['linux_distro'].required = False
        self.fields['date_maj_os'].required = False
        self.fields['logiciel_photo'].required = False
        self.fields['media_player'].required = False
        self.fields['rapport_configuration'].required = False

        # Layout simplifié : juste les champs, la mise
        # en page est faite dans le template
        self.helper.layout = Layout(
            Fieldset( "Diagnostic & configuration logicielle",
                'categorie', 'modele',
                # Hardware
                'cpu', 'cpu_score', 'ram_go', 'ram_nb_barrettes', 'ram_type', 
                'statut_wifi', 'disque_principal_type','disque_principal_go','disque_secondaire_type','disque_secondaire_go','a_carte_graphique_dediee', 'modele_gpu',
                'rapport_diagnostic', 'a_alimentation', 'etat_batterie',
                # Software
                'linux_installe', 'linux_distro', 'date_maj_os', 'dns_configures', 'langue_configuree', 
                'onlyoffice_installe', 'logiciel_photo', 'media_player', 'firefox_configure', 'firefox_extensions',
                'rapport_configuration',
            )
        )


    def clean(self):
        cleaned_data = super().clean()
        
        # Récupération du statut cible (si la vue le passe dans le form ou via POST)
        # Astuce: On peut regarder dans self.data directement
        action = self.data.get('action')
        
        # Initialisation du tableau des erreurs
        errors = []

        # Définition des actions qui nécessitent un diagnostic complet avant la bascule de statut
        actions_diag_complete = ['validate_diag_and_release', 'validate_diag_and_config', 'validate_config'] 
        
        # Pour ces actions on vérifie que les champs du diagnostic hardware soient bien remplis
        if action in actions_diag_complete:
            
            if not cleaned_data.get('cpu'):
                errors.append("Le processeur (CPU) est obligatoire pour valider le diagnostic.")
            if not cleaned_data.get('cpu_score'):
                errors.append("L'indice de performance CPU est obligatoire pour valider le diagnostic.")
            if not cleaned_data.get('ram_go'):
                errors.append("La quantité de RAM est obligatoire pour valider le diagnostic.")
            if not cleaned_data.get('disque_principal_type'):
                errors.append("Le type du disque principal est obligatoire pour valider le diagnostic.")
            if not cleaned_data.get('disque_principal_go'):
                errors.append("La taille du disque principal est obligatoire pour valider le diagnostic.")
            if not cleaned_data.get('rapport_diagnostic'):
                errors.append("Un rapport de diagnostic est obligatoire.")

        # Pour validate_config il faut également que les champs logiciels soient valides
        if action == 'validate_config':
            linux_installe = cleaned_data.get('linux_installe')

            if not linux_installe:
                errors.append("Linux doit être installé pour valider la configuration logicielle.")
            else:
                if not cleaned_data.get('linux_distro'):
                    errors.append("La distribution Linux est obligatoire pour valider la configuration logicielle.")
                if not cleaned_data.get('date_maj_os'):
                    errors.append("La date de mise à jour de la distribution Linux est obligatoire pour valider la configuration logicielle.")
                if not cleaned_data.get('dns_configures'):
                    errors.append("Les DNS doivent être configurés pour valider la configuration logicielle.")
                if not cleaned_data.get('langue_configuree'):
                    errors.append("La langue anglaise doit être retirée des paramètres pour valider la configuration logicielle.")
                if not cleaned_data.get('onlyoffice_installe'):
                    errors.append("Only Office doit être installé pour valider la configuration logicielle.")
                if not cleaned_data.get('firefox_configure'):
                    errors.append("Firefox doit être configuré pour valider la configuration logicielle.")
                if not cleaned_data.get('firefox_extensions'):
                    errors.append("Les extensions de Firefox doit être installées pour valider la configuration logicielle.")
                if not cleaned_data.get('logiciel_photo'):
                    errors.append("Préciser l'option retenue pour le logiciel de dessin afin de valider la configuration logicielle.")
                if not cleaned_data.get('media_player'):
                    errors.append("Préciser l'option retenue pour le media player afin de valider la configuration logicielle.")
                if not cleaned_data.get('rapport_configuration'):
                    errors.append("Le rapport d'installation OS et de configuration est obligatoire pour valider la configuration logicielle.")            

        if errors:
            raise forms.ValidationError(errors)
               
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
            'connectique': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            # 'connectique': forms.TextInput(attrs={'class': 'form-control'}),
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
            Field('connectique', template='crispy/forms/checkboxselectmultiple.html'),  
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
        fields = ['type_periph', 'connectique', 'rapport_diagnostic']
        widgets = {
            'rapport_diagnostic': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'type_periph': forms.Select(attrs={'class': 'form-select'}),
            # 'avec_cable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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
            # 'avec_cable',
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

