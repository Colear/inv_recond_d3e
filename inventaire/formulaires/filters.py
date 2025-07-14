from django import forms
from django.forms import TextInput

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Fieldset, Row, Column, Submit, Button
from crispy_forms.bootstrap import AppendedText
from crispy_bootstrap5.bootstrap5 import FloatingField



# ----- filtres pour l'inventaire ----------

CATEGORIE_MATERIEL = (("pc_tour", "PC tours"), ("pc_portable", "PC portables"), ("ecran", "Ecrans"), ("souris_clavier", "Souris et claviers", ("autre_materiel", "Autre matériels")))

class InventoryFilters(forms.Form):

    type = forms.ChoiceField(label="Catégorie de matériel", choices=CATEGORIE_MATERIEL, required=False)
