from django.urls import path
from .views import HomePageView, InventaireListView, NouveauMaterielView, ajax_create_marque


urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('inventaire/', InventaireListView.as_view(), name='inventaire'),
    path('nouveau/', NouveauMaterielView.as_view(), name='nouveau_materiel'),
    path('ajax/create-marque/', ajax_create_marque, name='ajax_create_marque'),    
]

