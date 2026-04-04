from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Fieldset, Submit, HTML, Div, Field
from ..models import Ordinateur, DisqueDur



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
            # Hardware - Diagnostic
            'cpu', 'cpu_score', 'ram_go', 'ram_nb_barrettes', 'ram_type',
            'a_carte_wifi', 'a_carte_graphique_dediee', 'modele_gpu',
            'rapport_diagnostic',
            # Hardware - Réparation
            'pieces_changees', 'cout_reparation',
            'a_alimentation', 'etat_batterie', # Champs Portables
            # Software - Configuration
            'linux_installe', 'linux_distro', 'date_maj_os',
            'onlyoffice_installe', 'logiciel_photo', 'media_player', 'firefox_configure',
            'statut' 
        ]
        labels = {
            'ram_go': "RAM installée (en Go) ",
            'ram_nb_barrettes': "Nb de barrettes",
            'ram_type': "Type de RAM",
        }
        widgets = {
            'cpu': forms.TextInput(attrs={'placeholder': 'Ex: Intel i5-8500'}),
            'rapport_diagnostic': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Problèmes constatés, tests...'}),
            'pieces_changees': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Liste des pièces remplacées'}),
            'etat_batterie': forms.Select(attrs={'class': 'form-select'}),
            'linux_distro': forms.Select(attrs={'class': 'form-select'}),
            'date_maj_os': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        # Récupérer l'action (bouton cliqué) si passée en argument par la vue
        self.action = kwargs.pop('action', None) 
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'diagnostic-form'
        
        # Définition de la mise en page (Layout)
        self.helper.layout = Layout(
            Fieldset("🔍 Diagnostic & Réparation Hardware",
                Row(
                    Column('cpu', css_class='col-md-6'),
                    Column('cpu_score', css_class='col-md-6'),
                ),
                Row(
                    Column('ram_go', css_class='col-md-3'),
                    Column('ram_nb_barrettes', css_class='col-md-3'),
                    Column('ram_type', css_class='col-md-3'),
                    Column('a_carte_wifi', css_class='col-md-3'),
                ),
                Div(
                    HTML("<h6 class='mt-3 text-primary'>Spécifique PC Portable</h6>"),
                    Row(
                        Column('a_alimentation', css_class='col-md-6'),
                        Column('etat_batterie', css_class='col-md-6'),
                    ),
                    css_class='p-3 bg-light border rounded mt-2',
                ),
                Row(Column('rapport_diagnostic', css_class='col-12')),
                Div(
                    HTML("<h6 class='mt-4 text-warning'>🛠️ Réparation Matérielle</h6>"),
                    Row(
                        Column('pieces_changees', css_class='col-md-8'),
                        Column('cout_reparation', css_class='col-md-4'),
                    ),
                    css_class='mt-3 p-3 border-top'
                ),
            ),
            Fieldset("🐧 Configuration Logicielle (Linux)",
                Row(Column('linux_installe', css_class='col-md-12')),
                Div(
                    Row(
                        Column('linux_distro', css_class='col-md-4'),
                        Column('date_maj_os', css_class='col-md-4'),
                        Column('onlyoffice_installe', css_class='col-md-4'),
                    ),
                    Row(
                        Column('logiciel_photo', css_class='col-md-4'),
                        Column('media_player', css_class='col-md-4'),
                        Column('firefox_configure', css_class='col-md-4'),
                    ),
                    css_class='mt-2',
                ),
                css_id="linux-config-section", # Important pour le JS
            ),
            'statut',
            Submit('submit', 'Sauvegarder', css_class='btn btn-primary d-none') # Bouton caché, on utilise les nôtres dans le template
        )


    def clean(self):
        cleaned_data = super().clean()
        
        # Récupération du statut cible (si la vue le passe dans le form ou via POST)
        # Astuce: On peut regarder dans self.data directement
        action = self.data.get('action')
        
        # Définition des actions qui nécessitent un diagnostic COMPLET
        actions_completes = ['validate_diag_repa', 'validate_repa'] 
        
        if action in actions_completes:
            # Si on veut passer en Réparation/Config, les champs Hardware sont OBLIGATOIRES
            errors = []
            if not cleaned_data.get('cpu'):
                errors.append("Le processeur (CPU) est obligatoire pour valider le diagnostic.")
            if not cleaned_data.get('ram_go'):
                errors.append("La quantité de RAM est obligatoire pour valider le diagnostic.")
            if not cleaned_data.get('rapport_diagnostic'):
                errors.append("Un rapport de diagnostic est obligatoire.")
            
            if errors:
                raise forms.ValidationError(errors)
        
        # Si l'action est 'wait_parts' ou 'save_exit', on ne bloque pas (champs optionnels)
        
        return cleaned_data



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
