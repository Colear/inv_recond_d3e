from django.urls import path

from .views import (
    DefaultFormByFieldView,
    DefaultFormsetView,
    FormHorizontalView,
    FormInlineView,
    FormWithFilesView,
    HomePageView,
    MiscView,
    PaginationView,
    MaterielEnregistreView,
    nouveau_materiel,
    SortieMaterielView,
    inventaire,
    RepairConfigureView,
    BilanAnnuelView,
    BilanEcologicView,
    EtatStockView,
    MonCompteView,
    DetailsPcView,
    liste_stock,
    choix_type_ajout,
    ajouter_materiel,
    detail_materiel,
    ajouter_materiel_unifie,
    ajax_create_marque,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("formset", DefaultFormsetView.as_view(), name="formset_default"),
    path("nouveau_materiel", nouveau_materiel, name="nouveau_materiel"),
    path("sortie_materiel", SortieMaterielView.as_view(), name="sortie_materiel"),
    path("materiel_enregistre/<materiel_id>", MaterielEnregistreView.as_view(), name="materiel_enregistre"),
    path("inventaire", inventaire, name="inventaire"),
    path("reparer_et_configurer", RepairConfigureView.as_view(), name="reparer_et_configurer"),
    path("bilan_annuel", BilanAnnuelView.as_view(), name="bilan_annuel"),
    path("bilan_ecologic", BilanEcologicView.as_view(), name="bilan_ecologic"),
    path("etat_stock", EtatStockView.as_view(), name="etat_stock"),
    path("mon_compte", MonCompteView.as_view(), name="mon_compte"),
    path("details_pc/<materiel_id>", DetailsPcView.as_view(), name="details_pc"),
    path("form_by_field", DefaultFormByFieldView.as_view(), name="form_by_field"),
    path("form_horizontal", FormHorizontalView.as_view(), name="form_horizontal"),
    path("form_inline", FormInlineView.as_view(), name="form_inline"),
    path("form_with_files", FormWithFilesView.as_view(), name="form_with_files"),
    path("pagination", PaginationView.as_view(), name="pagination"),
    path("misc", MiscView.as_view(), name="misc"),

    # Page d'accueil du stock (liste globale)
    path('liste', liste_stock, name='liste_stock'),
    
    # Page intermédiaire pour choisir le type de matériel à ajouter
    path('ajouter/choix/', choix_type_ajout, name='choix_type_ajout'),
    
    # Vues d'ajout dynamiques selon le type
    # L'URL sera : /ajouter/ecran/ ou /ajouter/ordinateur/
    path('ajouter/<str:type_materiel>/', ajouter_materiel, name='ajouter_materiel'),

    # Vue dynamique d'ajout de matériel
    path('ajouter_materiel', ajouter_materiel_unifie, name='ajouter_materiel_unifie'),

    # Nouvelle route pour l'AJAX
    path('ajax/create-marque/', ajax_create_marque, name='ajax_create_marque'),
    
    # Détail d'un matériel spécifique
    # L'URL sera : /detail/1/ (où 1 est l'ID du matériel)
    path('detail/<int:pk>/', detail_materiel, name='detail_materiel'),
    
    # (Optionnel) URL pour l'assignation si vous la créez plus tard
    # path('<int:pk>/assigner/', assigner_materiel, name='assigner_materiel'),
]

