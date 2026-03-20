from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal



"""====== Marque ==============================================================
Table externe qui sera utilisé quelque soit le type de matériel pour choisir
la marque du matériel saisi.
============================================================================""" 

class Marque(models.Model):
    marque = models.CharField(max_length=100, unique=True)
    site_web = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.marque

    class Meta:
        ordering = ['marque']
        verbose_name_plural = "Marques"



"""====== Materiel ============================================================
    Classe parente pour tous les matériels.
============================================================================""" 

class Materiel(models.Model):
    STATUT_CHOICES = [
        ('STOCK', 'En stock'),
        ('ASSIGNE', 'Assigné'),
        ('PANNE', 'En panne'),
        ('RECYCLE', 'Recyclé'),
    ]

    # numéro unique généré automatiquement
    numero_inventaire = models.CharField(max_length=20, unique=True, blank=True, editable=False)
    
    date_achat = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='STOCK')
    utilisateur = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    date_attribution = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)


    # ----- surcharge de la méthode save du parent pour y ajouter la génération du numro d'inventaire

    def save(self, *args, **kwargs):
        if not self.numero_inventaire:
            self.numero_inventaire = self.generer_numero_inventaire()
        super().save(*args, **kwargs)


    # ----- génération du numéro d'inventaire, au format INV-0001

    def generer_numero_inventaire(self):
        prefix = "INV-"
        
        # Récupération du dernier matériel créé dans la base
        last_materiel = Materiel.objects.exclude(
            numero_inventaire__isnull=True
        ).exclude(
            numero_inventaire=''
        ).order_by('numero_inventaire').last()

        # Récupération de la partie numérique
        if last_materiel and last_materiel.numero_inventaire.startswith(prefix):
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


    # ----- affichage dans l'admin et les listes

    def __str__(self):
        return f"{self.numero_inventaire} - {self.get_type_display()}"


    # ----- affiche variable selon le type de matériel

    def get_type_display(self):
        if hasattr(self, 'ecran'):
            return f"Écran {self.ecran.marque} {self.ecran.modele}"
        elif hasattr(self, 'ordinateur'):
            return f"PC {self.ordinateur.marque} {self.ordinateur.modele}"
        return "Matériel"


    # ----- prise en charge d'un ordi par un bénévole

    def assigner_a(self, user):
        self.utilisateur = user
        self.statut = 'ASSIGNE'
        self.date_attribution = timezone.now()
        self.save()



"""====== Ecran ===============================================================
    Classe fille de Materiel destinée aux écrans.
============================================================================""" 

class Ecran(Materiel):

    # Solution un peu complexe pour pouvoir à la fois stocker la diagonale comme un nombre
    # décimal tout en profitant d'une liste de choix dans les formulaires : Django n'accepte 
    # que des keys / values en chaine dans les choices.
    # On va donc créer un tableau de décimal avec les tailles possibles qui sera converti
    # à la volée en une liste de choix en string, mais le stockage restera bien en décimal. 
    TAILLES_AUTORISEES = [21.5, 23.8, 24, 25, 27, 32, 34, 40, 43, 49, 55, 65, 75, 86, 98]
    DIAGONALE_CHOICES = [(Decimal(str(t)), f"{t} pouces") for t in TAILLES_AUTORISEES]
    diagonale_pouces = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        choices=DIAGONALE_CHOICES, 
        help_text="Sélectionnez la diagonale de l'écran"
    )

    # Pointeur sur la table des marques
    marque = models.ForeignKey(Marque, on_delete=models.PROTECT, related_name='ecrans')

    # Données optionnelles
    modele = models.CharField(max_length=100, blank=True)
    resolution = models.CharField(max_length=20, blank=True)
    connectique = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Écran"
        verbose_name_plural = "Écrans"
        # Optionnel : tri par taille par défaut
        ordering = ['diagonale_pouces']



"""====== Ordinateur ==========================================================
    Classe fille de Materiel destinée aux ordis.
============================================================================""" 

class Ordinateur(Materiel):

    # Pointeur sur la table des marques
    marque = models.ForeignKey(Marque, on_delete=models.PROTECT, related_name='ordinateurs')

    modele = models.CharField(max_length=100, blank=True)
    cpu = models.CharField(max_length=100, blank=True)
    ram_go = models.PositiveIntegerField()
    stockage_go = models.PositiveIntegerField()
    type_stockage = models.CharField(max_length=20, choices=[('SSD', 'SSD'), ('HDD', 'HDD'), ('NVMe', 'NVMe')], default='SSD')
    systeme_exploitation = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "Ordinateur"
        verbose_name_plural = "Ordinateurs"
