from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Ordinateur, Ecran

admin.site.register(Ordinateur)
admin.site.register(Ecran)
