import random

from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models.fields.files import FieldFile
from django.views.generic import FormView
from django.views.generic.base import TemplateView

from django.http import HttpResponseRedirect


from .forms import ContactForm, ContactFormSet, FilesForm
from .formulaires.materiel import MaterielForm, PCForm
from .formulaires.filters import InventoryFilters

from django.shortcuts import render, redirect, get_object_or_404
from .models import Materiel, Ecran, Ordinateur
from .formulaires.materiel_v2 import EcranForm, OrdinateurForm


# http://yuji.wordpress.com/2013/01/30/django-form-field-in-initial-data-requires-a-fieldfile-instance/
class FakeField:
    storage = default_storage


fieldfile = FieldFile(None, FakeField, "dummy.txt")


class HomePageView(TemplateView):
    template_name = "inventaire/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        messages.info(self.request, "Bienvenue dans l'application d'inventaire de l'atelier reconditionnement numérique !")
        return context


class GetParametersMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["layout"] = self.request.GET.get("layout", None)
        context["size"] = self.request.GET.get("size", None)
        return context


class DefaultFormsetView(GetParametersMixin, FormView):
    template_name = "inventaire/formset.html"
    form_class = ContactFormSet


def nouveau_materiel(request):

    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = MaterielForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # l'enreigstrement du matériel a généré son ID, on va le
            # passer à la vue indiquant que le matos a bien été pris en compte
            # pour l'étiquetage
            materiel_id = random.randint (680, 999)
            
            # redirect to a new URL:
            return redirect('materiel_enregistre', materiel_id=materiel_id)
            # return HttpResponseRedirect("enregistrement_materiel")

    # if a GET (or any other method) we'll create a blank form
    else:
        form = MaterielForm()

    return render(request, "inventaire/nouveau_materiel.html", {"form": form})


class SortieMaterielView(TemplateView):
    template_name = "inventaire/sortie_materiel.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        messages.info(self.request, "Sortie d'un matériel")
        return context


class InventaireView(TemplateView):
    template_name = "inventaire/inventaire.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        messages.info(self.request, "Inventaire global")
        return context


class RepairConfigureView(TemplateView):
    template_name = "inventaire/repair_configure.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        messages.info(self.request, "Travailler sur un PC")
        return context


class BilanAnnuelView(TemplateView):
    template_name = "inventaire/bilan_annuel.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        messages.info(self.request, "Bilan annuel")
        return context

class BilanEcologicView(TemplateView):
    template_name = "inventaire/bilan_ecologic.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        messages.info(self.request, "Bilan de la convention Ecologic")
        return context

class EtatStockView(TemplateView):
    template_name = "inventaire/etat_stock.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        messages.info(self.request, "Etat du stock")
        return context

class MonCompteView(TemplateView):
    template_name = "inventaire/mon_compte.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        messages.info(self.request, "Mon compte")
        return context

    

# ----- fin du processus d'enregistrement d'un nouveau matériel ----------

class MaterielEnregistreView(TemplateView):
    template_name = "inventaire/materiel_enregistre.html"



# ----- liste des PCs non renseignés ----------

def inventaire(request):

    # c'est du maquettage, on commence par créer une liste bidon 
    marques = ["Asus", "HP", "Dell", "Lenovo", "Sony", "Custom", "Acer", "Samsung", "IBM"]
    modeles = ["X220", "Inspirion", "TUF", "Omen", "Victus", "Pavilion", "S12", "A440", "Thinkpad"]
    
    liste = []
    for _ in range(50):
        liste.append([random.randint (680, 999), random.choice(marques), random.choice(modeles), round(random.uniform(0.5,12), 2)])
    
    # formulaire de filtres
    inventory_filters = InventoryFilters()

    # gestion de la pagination, on affiche 15 PC par page
    paginator = Paginator(liste, 15)  
    page_number = request.GET.get("page")
    page_liste = paginator.get_page(page_number)

    # on affiche la liste en passant le tableau en contexte
    return render(request, "inventaire/inventaire.html", {"page_liste": page_liste, "inventory_filters": inventory_filters})



# ----- détail d'un PC ----------

class DetailsPcView(GetParametersMixin, FormView):
    template_name = "inventaire/details_pc.html"
    form_class= PCForm




def choix_type_ajout(request):
    """Page intermédiaire pour choisir le type de matériel à ajouter"""
    return render(request, 'inventaire/choix_type.html')

def ajouter_materiel(request, type_materiel):
    if type_materiel == 'ecran':
        model_class = Ecran
        form_class = EcranForm
        template = 'inventaire/form_ecran.html'
    elif type_materiel == 'ordinateur':
        model_class = Ordinateur
        form_class = OrdinateurForm
        template = 'inventaire/form_ordinateur.html'
    else:
        return redirect('choix_type_ajout')

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
            return redirect('liste_stock') # À créer
    else:
        form = form_class()

    return render(request, template, {'form': form, 'type': type_materiel})

def liste_stock(request):
    """Affiche tout le matériel avec un accès facile aux détails"""
    materiels = Materiel.objects.all().select_related('ecran', 'ordinateur')
    return render(request, 'inventaire/liste.html', {'materiaux': materiels})

def detail_materiel(request, pk):
    """Affiche les détails complets selon le type"""
    materiel = get_object_or_404(Materiel.objects.select_related('ecran', 'ordinateur'), pk=pk)
    
    contexte = {'materiel': materiel}
    
    if hasattr(materiel, 'ecran'):
        contexte['details'] = materiel.ecran
        contexte['type_template'] = 'inventaire/detail_ecran.html'
    elif hasattr(materiel, 'ordinateur'):
        contexte['details'] = materiel.ordinateur
        contexte['type_template'] = 'inventaire/detail_pc.html'
    else:
        contexte['type_template'] = 'inventaire/detail_generique.html'
        
    return render(request, 'inventaire/detail.html', contexte)


# ----- suite ... ----------

""" class DefaultFormView(GetParametersMixin, FormView):
    template_name = "inventaire/form.html"
    form_class = ContactForm
 """

class DefaultFormByFieldView(GetParametersMixin, FormView):
    template_name = "inventaire/form_by_field.html"
    form_class = ContactForm


class FormHorizontalView(GetParametersMixin, FormView):
    template_name = "inventaire/form_horizontal.html"
    form_class = ContactForm


class FormInlineView(GetParametersMixin, FormView):
    template_name = "inventaire/form_inline.html"
    form_class = ContactForm


class FormWithFilesView(GetParametersMixin, FormView):
    template_name = "inventaire/form_with_files.html"
    form_class = FilesForm

    def get_initial(self):
        return {"file4": fieldfile}


class PaginationView(TemplateView):
    template_name = "inventaire/pagination.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lines = []
        for i in range(200):
            lines.append(f"Line {i + 1}")
        paginator = Paginator(lines, 10)
        page = self.request.GET.get("page")
        try:
            show_lines = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            show_lines = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            show_lines = paginator.page(paginator.num_pages)
        context["lines"] = show_lines
        return context


class MiscView(TemplateView):
    template_name = "inventaire/misc.html"
