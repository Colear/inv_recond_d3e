import datetime

from django import forms
from django.forms import TextInput

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Fieldset, Row, Column, Submit, Button
from crispy_forms.bootstrap import AppendedText
from crispy_bootstrap5.bootstrap5 import FloatingField



# ----- données pour alimentation des selects dans le cadre du prototypage ----------

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

MARQUES_PC = (("lenovo", "Lenovo"), ("samsung", "Samsung"))
MARQUES_CPU = (("amd", "AMD"), ("intel", "Intel"))
FORMAT_RAM = (("dimm", "DIMM"), ("so-dimm", "SO-DIMM"), ("soudee", "Soudée"), ("mixte", "Mixte"))
ZERO_TO_EIGHT = (("0", "0"),("1", "1"),("2", "2"),("3", "3"),("4", "4"),("5", "5"),("6", "6"),("7", "7"),("8", "8"))
TYPE_DISK = (
    ("Disque dur", (("hdd_35", "Format standard (3.5 pouces)"), ("hdd_25", "Format portable (2.5 pouces)"))),
    ("SSD", (("ssd_25", "Format disque 2.5"), ("m2", "Format carte M2")))
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
    
    marque = forms.ChoiceField(
        label="Marque", 
        required=True,
        choices=MARQUES_PC 
        )
    
    modele = forms.CharField(
        label="Modèle", 
        required=True, 
        max_length=50, 
        widget=forms.TextInput(attrs={"placeholder": ""})
        )
    
    cpu_marque = forms.ChoiceField(
        label="Marque", 
        required=False,
        choices=MARQUES_CPU 
        )
    
    cpu_modele = forms.CharField(
        label="Modèle", 
        required=False, 
        max_length=50, 
        widget=forms.TextInput(attrs={"placeholder": ""})
        )
    
    cpu_freq = forms.DecimalField(
        label="Fréquence",
        required=False, 
        decimal_places=2, 
        min_value=0,
        initial=0.0, 
        widget=forms.NumberInput(attrs={"step": 0.10})
        )
    
    cpu_perf = forms.IntegerField(
        label="Performance",
        required=False,
        min_value=0
    )

    ram_type = forms.ChoiceField(
        label="Format", 
        required=False,
        choices=FORMAT_RAM 
        )
    
    ram_qte = forms.IntegerField(
        label="Quantité",
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"step": 128})
    )

    ram_nb = forms.TypedChoiceField(
        label="Barettes",
        coerce=int,
        required=False,
        choices=ZERO_TO_EIGHT
    )

    ram_libre = forms.TypedChoiceField(
        label="Emplacements libres",
        coerce=int,
        required=False,
        choices=ZERO_TO_EIGHT
    )

    disk_number = forms.IntegerField(
        label="Disque",
        initial=1,
        disabled=True,
        required=False,
        widget=forms.TextInput()
    )

    disk_type = forms.ChoiceField(
        label="Type", 
        required=False,
        choices=TYPE_DISK 
    )

    disk_size = forms.IntegerField(
        label="Taille",
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"step": 10})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        #self.helper.form_id = 'id-exampleForm'
        #self.helper.form_class = 'blueForms'
        #self.helper.form_method = 'post'
        #self.helper.form_action = 'submit_survey'

        self.helper.layout = Layout(
            Div(

                Row(
                    Column(FloatingField('marque'), css_class='col-md-6'),
                    Column(FloatingField('modele'), css_class='col-md-6')
                ),
                Fieldset(
                    'CPU',
                    Row(
                        Column('cpu_marque', css_class='col-md-6 col-lg-3'),
                        Column('cpu_modele', css_class='col-md-6 col-lg-3'),
                        Column(AppendedText('cpu_freq', 'Ghz'), css_class='col-md-6 col-lg-3'),
                        Column('cpu_perf', css_class='col-md-6 col-lg-3'),
                    ),
                    css_class='border pt-2 px-2 mb-4'
                ),
                Fieldset(
                    'RAM',
                    Row(
                        Column('ram_type', css_class='col-md-3'),
                        Column(AppendedText('ram_qte', 'Mo'), css_class='col-md-3'),
                        Column('ram_nb', css_class='col-md-3'),
                        Column('ram_libre', css_class='col-md-3'),
                    ),
                    css_class='border pt-2 px-2 mb-4'
                ),
                Fieldset(
                    'Stockage',
                    Row(
                        Column('disk_number', css_class='col-md-2'),
                        Column('disk_type', css_class='col-md-5'),
                        Column(AppendedText('disk_size', 'Go'), css_class='col-md-5')
                    ),
                    Row(
                        Column(
                            Button('add_disk', 'Ajouter un disque', css_class='btn btn-warning'),
                            css_class='text-center mb-4'
                        )
                    ),
                    css_class='border pt-2 px-2 mb-4'
                ),
                css_class='pt-5'
            )
        )
        self.helper.add_input(Submit('submit', 'Submit'))
