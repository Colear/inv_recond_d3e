from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Materiel(models.Model):
    STATUT_CHOICES = [
        ('STOCK', 'En stock'),
        ('ASSIGNE', 'Assigné'),
        ('PANNE', 'En panne'),
        ('RECYCLE', 'Recyclé'),
    ]

    # Le champ est unique, mais on ne le remplit pas manuellement (blank=True)
    numero_inventaire = models.CharField(max_length=20, unique=True, blank=True, editable=False)
    
    date_achat = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='STOCK')
    utilisateur = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    date_attribution = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # Si le numéro n'existe pas encore, on le génère
        if not self.numero_inventaire:
            self.numero_inventaire = self.generer_numero_inventaire()
        super().save(*args, **kwargs)

    def generer_numero_inventaire(self):
        """Génère un numéro global type INV-0001, INV-0002, etc."""
        prefix = "INV-"
        
        # On récupère le dernier matériel créé dans TOUTE la base
        last_materiel = Materiel.objects.exclude(
            numero_inventaire__isnull=True
        ).exclude(
            numero_inventaire=''
        ).order_by('numero_inventaire').last()

        if last_materiel and last_materiel.numero_inventaire.startswith(prefix):
            # On extrait la partie numérique à la fin (ex: "0001" -> 1)
            try:
                last_num = int(last_materiel.numero_inventaire.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                # En cas d'erreur de format sur le dernier élément, on repart à 1
                new_num = 1
        else:
            # Si c'est le tout premier élément
            new_num = 1

        # On formate avec 4 chiffres (ex: 1 -> "0001", 125 -> "0125")
        return f"{prefix}{new_num:04d}"

    def __str__(self):
        # Affiche le numéro d'inventaire directement dans l'admin/listes
        return f"{self.numero_inventaire} - {self.get_type_display()}"

    def get_type_display(self):
        if hasattr(self, 'ecran'):
            return f"Écran {self.ecran.marque} {self.ecran.modele}"
        elif hasattr(self, 'ordinateur'):
            return f"PC {self.ordinateur.marque} {self.ordinateur.modele}"
        return "Matériel"

    def assigner_a(self, user):
        self.utilisateur = user
        self.statut = 'ASSIGNE'
        self.date_attribution = timezone.now()
        self.save()

# Les modèles enfants n'ont pas besoin de changer, ils héritent de tout
class Ecran(Materiel):
    marque = models.CharField(max_length=100)
    modele = models.CharField(max_length=100)
    diagonale_pouces = models.DecimalField(max_digits=4, decimal_places=1)
    resolution = models.CharField(max_length=20, blank=True)
    connectique = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Écran"
        verbose_name_plural = "Écrans"

class Ordinateur(Materiel):
    marque = models.CharField(max_length=100)
    modele = models.CharField(max_length=100)
    cpu = models.CharField(max_length=100)
    ram_go = models.PositiveIntegerField()
    stockage_go = models.PositiveIntegerField()
    type_stockage = models.CharField(max_length=20, choices=[('SSD', 'SSD'), ('HDD', 'HDD'), ('NVMe', 'NVMe')], default='SSD')
    systeme_exploitation = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "Ordinateur"
        verbose_name_plural = "Ordinateurs"
