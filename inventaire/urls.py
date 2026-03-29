from django.urls import path
from .views import HomePageView, InventaireListView, NouveauMaterielView, ajax_create_marque, imprimer_planche_etiquettes, search_by_inv, modifier_materiel, CustomLoginView, CustomLogoutView



urlpatterns = [

    # Pages de Connexion / Déconnexion
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

    path('', HomePageView.as_view(), name='home'),
    path('inventaire/', InventaireListView.as_view(), name='inventaire'),
    path('nouveau/', NouveauMaterielView.as_view(), name='nouveau_materiel'),
    path('ajax/create-marque/', ajax_create_marque, name='ajax_create_marque'),
    path('imprimer-planchette/', imprimer_planche_etiquettes, name='imprimer_planchette'),
    path('search-by-inv/<str:numero_inv>/', search_by_inv, name='search_by_inv'),
    path('modifier/<int:pk>/', modifier_materiel, name='modifier_materiel'),
    # path('etiquette/<int:pk>/', views.generer_etiquette_qr, name='etiquette_qr'),   
]

