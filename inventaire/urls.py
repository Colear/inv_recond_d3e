from django.urls import path
from django.http import HttpResponse

# URLs temporaires pour permettre la migration
def placeholder(request):
    return HttpResponse("Application en maintenance - Migration en cours")

urlpatterns = [
    # path('', placeholder, name='home'), # Optionnel
]