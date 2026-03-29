# inventaire/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
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
        messages.error(self.request, "Accès refusé : Compte inactif ou inexistant.")
        return redirect('login')

# On combine un mixin qui valide le login puis vérifie que le compte bénévole est actif
class AuthBenevoleMixin(LoginRequiredMixin, BenevoleActifMixin):
    pass
