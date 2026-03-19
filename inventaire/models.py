from django.db import models

from django.db import models
from django.contrib.auth.models import User

class Categorie(models.Model):
    nom = models.CharField(max_length=100)  # Ex: Ordinateur, Écran, Clavier

    def __str__(self):
        return self.nom

class MaterielReference(models.Model):
    """Définit le type de matériel (le modèle)"""
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE)
    marque = models.CharField(max_length=100)
    modele = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.marque} {self.modele}"

class Equipement(models.Model):
    """Instance physique unique dans le stock"""
    STATUT_CHOICES = [
        ('STOCK', 'En stock'),
        ('EN_COURS', 'En cours'),
        ('POUR_PIECE', 'Pour pièce'),
        ('A_RECYCLER', 'A recycler'),
    ]

    reference = models.ForeignKey(MaterielReference, on_delete=models.CASCADE)
    num_inventaire = models.CharField(max_length=100, unique=True)
    date_entree = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='STOCK')
    
    # Champs optionnels pour le suivi
    utilisateur = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    date_attribution = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.reference} - {self.numero_serie}"
    
