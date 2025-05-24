import random

from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models.fields.files import FieldFile
from django.views.generic import FormView
from django.views.generic.base import TemplateView

from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect

from .forms import ContactForm, ContactFormSet, FilesForm
from .formulaires.materiel import MaterielForm, PCForm


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

class NouveauMaterielView(GetParametersMixin, FormView):
    template_name = "inventaire/nouveau_materiel.html"
    form_class = MaterielForm

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



# ----- fin du processus d'enregistrement d'un nouveau matériel ----------

class MaterielEnregistreView(TemplateView):
    template_name = "inventaire/materiel_enregistre.html"



# ----- liste des PCs non renseignés ----------

def pc_non_renseignes(request):

    # c'est du maquettage, on commence par créer une liste bidon 
    marques = ["Asus", "HP", "Dell", "Lenovo", "Sony", "Custom", "Acer", "Samsung", "IBM"]
    modeles = ["X220", "Inspirion", "TUF", "Omen", "Victus", "Pavilion", "S12", "A440", "Thinkpad"]
    
    liste = []
    for _ in range(50):
        liste.append([random.randint (680, 999), random.choice(marques), random.choice(modeles), round(random.uniform(0.5,12), 2)])
    
    # gestion de la pagination, on affiche 15 PC par page
    paginator = Paginator(liste, 15)  
    page_number = request.GET.get("page")
    page_liste = paginator.get_page(page_number)

    # on affiche la liste en passant le tableau en contexte
    return render(request, "inventaire/pc_non_renseignes.html", {"page_liste": page_liste})



# ----- détail d'un PC ----------

class DetailsPcView(GetParametersMixin, FormView):
    template_name = "inventaire/details_pc.html"
    form_class= PCForm



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
