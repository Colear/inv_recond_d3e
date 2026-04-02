from django.contrib.auth.views import LoginView, LogoutView



"""====== Login / logout ======================================================
    Pages de connexion / deconnexion.
============================================================================"""

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True  # Si déjà connecté, renvoie vers home
    # La redirection par défaut après login est gérée par LOGIN_REDIRECT_URL dans settings.py

class CustomLogoutView(LogoutView):
    # Redirige vers la page de login après déconnexion
    next_page = 'login' 

