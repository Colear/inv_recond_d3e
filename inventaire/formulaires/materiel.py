import datetime

from django import forms
from django.forms import TextInput

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


TYPE_MATERIEL = (
    ("PC", (("tour", "Tour"), ("portable", "Portable"))),
    ("Périphérique", (("ecran", "Ecran"), ("clavier", "Clavier"), ("souris", "Souris"))),
    ("Composant", (("carte_graphique", "Carte graphique"), ("carte_wifi", "Carte WiFi"), ("disque_hdd", "Disque HDD"), ("disque_ssd", "Disque SSD 2,5 pouces"))),
    ("Alimentation", (("alim_19v", "Alimentation 19 volts"), ("alim_usb", "Alimentation USB"), ("alim_autre", "Autre alimentation"), ("batterie", "Batterie de portable"), ("onduleur", "Onduleur"))),
    ("Autre matériel", (("cable", "Cable"), ("imprimante", "Imprimante"), ("reseau", "Equipement réseau"), ("divers_ecran", "Matériel divers avec écran"), ("divers_sans_ecran", "Matériel divers sans écran"))),
)
ORIG_MATERIEL = (
    ("Déchetterie", (("sictom_nogent", "Sictom de Nogent"), ("sictom_thirons", "Sictom de Thirons"), ("autre_dechetterie", "Autre déchetterie"))),
    ("Partenariats", (("part_sully", "Lycée Sully"), ("part_autre", "Autre partenariat"))),
    ("Don", (("don_prive", "Don privé"), ("don_public", "Don du secteur public"), ("don_entreprise", "Don d'entreprise"), ("don_asso", "Don d'association"))),
)

# ----- formulaire pour la saisie d'un nouveau matériel ----------

class MaterielForm(forms.Form):

    date = forms.DateField(label="Date d'entrée",  
                           required=True, 
                           initial=datetime.date.today,
                           widget=TextInput(attrs={"type": "date"}))
    type = forms.ChoiceField(label="Type de matériel", choices=TYPE_MATERIEL, required=True)
    poids = forms.DecimalField(label="Poids",
                               required=False, 
                               decimal_places=2, 
                               min_value=0,
                               initial=0.0, 
                               widget=forms.NumberInput(attrs={"step": 0.10, "addon_after": "Kg"}))
    marque = forms.CharField(label="Marque", required=False, max_length=50, widget=forms.TextInput(attrs={"placeholder": ""}))
    ref = forms.CharField(label="Référence", required=False, max_length=50, widget=forms.TextInput(attrs={"placeholder": ""}))
    provenance = forms.ChoiceField(label="Provenance", choices=ORIG_MATERIEL, required=True)
    donateur = forms.CharField(label="Nom donateur", required=False, max_length=100, disabled=True, widget=forms.TextInput(attrs={"placeholder": ""}))



# ----- formulaire affichant les données détailles d'un PC ----------

class PCForm(forms.Form):
    
    marque = forms.CharField(label="Marque", required=False, max_length=50, widget=forms.TextInput(attrs={"placeholder": ""}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-exampleForm'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'
        self.helper.form_action = 'submit_survey'

        self.helper.add_input(Submit('submit', 'Submit'))
