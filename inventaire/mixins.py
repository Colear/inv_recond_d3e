# inventaire/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from .models import Benevole

# Verification du statut actif du compte du bénévole
class BenevoleActifMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        try:
            return user.profile_benevole.actif
        except Benevole.DoesNotExist:
            return False

    def handle_no_permission(self):
        messages.error(self.request, "Accès refusé : ce compte est désactivé.")
        return redirect('login')

class StrictPermissionMixin(PermissionRequiredMixin):
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            # Cas 1 : Utilisateur connecté mais pas la permission -> 403
            raise PermissionDenied("Vous n'avez pas la permission d'accéder à cette partie de l'application.")
        else:
            # Cas 2 : Utilisateur NON connecté -> Redirection vers Login (comportement standard)
            # On utilise la helper de Django pour faire la redirection proprement avec le paramètre ?next=
            return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())
        
# On combine un mixin qui valide les permissions, le login puis vérifie que le compte bénévole est bien actif
class AuthBenevoleMixin(StrictPermissionMixin, LoginRequiredMixin, BenevoleActifMixin):
    pass

