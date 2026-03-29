# inventaire/decorators.py
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from .models import Benevole

def benevole_actif_required(view_func):
    """
    Vérifie que l'utilisateur connecté a un profil Benevole et qu'il est actif.
    Sinon, le déconnecte et l'invite à contacter l'admin.
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login') # Ou votre page de login
        
        try:
            profile = request.user.profile_benevole
            if not profile.actif:
                # Compte désactivé
                from django.contrib.auth import logout
                logout(request)
                messages.error(request, "Votre compte a été désactivé. Veuillez contacter un responsable.")
                return redirect('login')
        except Benevole.DoesNotExist:
            # Utilisateur sans profil bénévole (ex: superuser sans profil, ou compte mal créé)
            # Si c'est un superuser, on laisse passer. Sinon, blocage.
            if not request.user.is_superuser:
                messages.error(request, "Profil bénévole introuvable. Contactez un responsable.")
                return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return wrapper
