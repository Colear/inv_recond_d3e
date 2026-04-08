# inventaire/forms/__init__.py

# ==============================================================================
# 1. FORMULAIRES DE STOCK (Entrée, Étiquettes)
# ==============================================================================
from .stock import (
    NouveauMaterielForm,
)

# ==============================================================================
# 2. FORMULAIRES DE WORKFLOW (Diagnostic, Réparation, Disques)
# ==============================================================================
from .workflow import (
    DiagnosticRepaForm,
    DiagnosticEcranForm,
    DiagnosticPeripheriqueForm,
)

# ==============================================================================
# 3. FORMULAIRES DE DONS & BÉNÉFICIAIRES
# ==============================================================================
from .dons import (
    BeneficiaireForm,
    # Ajoutez ici un éventuel formulaire de recherche de bénéficiaire si nécessaire
)

# ==============================================================================
# 4. AUTHENTIFICATION (Optionnel)
# ==============================================================================
# Si vous avez créé un formulaire de login personnalisé avec Crispy, décommentez ci-dessous :
# from .auth import CustomLoginForm

# ==============================================================================
# NOTE POUR L'UTILISATION AVEC CRISPY-FORMS
# ==============================================================================
# Une fois django-crispy-forms installé, vous pourrez modifier les classes
# dans les fichiers ci-dessus (stock.py, workflow.py, etc.) pour ajouter :
#   from crispy_forms.helper import FormHelper
#   from crispy_forms.layout import Layout, Row, Column...
#
# Exemple dans workflow.py :
# class DiagnosticRepaForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.helper = FormHelper()
#         self.helper.layout = Layout(...)
