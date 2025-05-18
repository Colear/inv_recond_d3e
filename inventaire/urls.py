from django.urls import path

from .views import (
    DefaultFormByFieldView,
    DefaultFormsetView,
    NouveauMaterielView,
    FormHorizontalView,
    FormInlineView,
    FormWithFilesView,
    HomePageView,
    MiscView,
    PaginationView,
    MaterielEnregistreView,
    nouveau_materiel,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("formset", DefaultFormsetView.as_view(), name="formset_default"),
    path("nouveau_materiel", nouveau_materiel, name="nouveau_materiel"),
    path("materiel_enregistre/<materiel_id>", MaterielEnregistreView.as_view(), name="materiel_enregistre"),
    path("form_by_field", DefaultFormByFieldView.as_view(), name="form_by_field"),
    path("form_horizontal", FormHorizontalView.as_view(), name="form_horizontal"),
    path("form_inline", FormInlineView.as_view(), name="form_inline"),
    path("form_with_files", FormWithFilesView.as_view(), name="form_with_files"),
    path("pagination", PaginationView.as_view(), name="pagination"),
    path("misc", MiscView.as_view(), name="misc"),
]
