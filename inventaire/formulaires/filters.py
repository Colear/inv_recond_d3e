from django import forms
from django.forms import TextInput

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Fieldset, Row, Column, Submit, Button
from crispy_forms.bootstrap import AppendedText
from crispy_bootstrap5.bootstrap5 import FloatingField



# ----- filtres pour l'inventaire ----------

CATEGORIE_MATERIEL = (("all", "Tout matériel"), ("pc_tour", "PC tours"), ("pc_portable", "PC portables"), ("ecran", "Ecrans"), ("souris_clavier", "Souris et claviers"), ("autre_materiel", "Autre matériels"))
STATUT = (("all", "Tout statut"), ("non_pese", "Matériels non pesés"), ("pc_unknown", "PC non renseignés"), ("en_cours", "PC en cours"), ("sortis", "Sortis du stock"))
INTERVENANT = (("all", ""), ("christophe", "Christophe"), ("jacques", "Jacques"), ("louis_theo", "Louis Théo"), ("philippe", "Philippe"))

class InventoryFilters(forms.Form):

    type = forms.ChoiceField(label="Catégorie de matériel", choices=CATEGORIE_MATERIEL, required=False) 
    statut = forms.ChoiceField(label="Statut", choices=STATUT, required=False)
    numero = forms.IntegerField(label="Numéro", required=False, min_value=0, widget=forms.NumberInput(attrs={"step": 1}))
    intervenant = forms.ChoiceField(label="Intervenant", choices=INTERVENANT, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-inventory_filters'

        self.helper.layout = Layout(
            Div(
                Row(
                    Column(FloatingField('type'), css_class='col-md-6 col-lg-3'),
                    Column(FloatingField('statut'), css_class='col-md-6 col-lg-3'),
                    Column(FloatingField('numero'), css_class='col-md-6 col-lg-3'),
                    Column(FloatingField('intervenant'), css_class='col-md-6 col-lg-3')
                ),
                css_class='pt-5 pb-3'
            )      
        )
