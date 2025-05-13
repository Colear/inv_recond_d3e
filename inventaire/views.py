from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def index(request):
    return HttpResponse("Hello, world ! Bienvenue à la racine de notre application d'inventaire !")
