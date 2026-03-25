from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from decimal import Decimal



"""====== Benevole ============================================================
Extension de la partie utilisateur de Django pour y ajouter des données
sur les bénévoles.
============================================================================""" 

class Benevole(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile_benevole')
    telephone = models.CharField(max_length=20, blank=True)
    
    SPECIALITE_CHOICES = [
        ('HW_TOUR', 'Hardware PC Tour'),
        ('HW_PORTABLE', 'Hardware PC Portable'),
        ('LINUX_INSTALL', 'Installation/Config Linux'),
        ('SHELL_DEV', 'Shell et Programmation'),
        ('ACCUEIL', 'Accueil et Logistique'),
        ('RECYCLAGE', 'Gestion Recyclage'),
    ]

    specialites = models.JSONField(
        "Spécialités",
        # choices=SPECIALITE_CHOICES,  => non sur les JSONField la validation doit être au niveau du formulaire
        default=list, 
        blank=True,
        help_text="Cochez les domaines de compétence"
    )
    
    actif = models.BooleanField(default=True)

    def __str__(self):
        # SÉCURITÉ : Gestion des cas vides ou None
        if not self.specialites:
            return f"{self.user.get_full_name() or self.user.username} (Bénévole)"
        
        # Création sécurisée du dictionnaire de choix
        choices_dict = dict(self.SPECIALITE_CHOICES)
        
        # Filtrage : on ne prend que les clés qui existent vraiment dans les choix
        # et on gère le cas où self.specialites ne serait pas une liste (ex: erreur de migration)
        noms = []
        if isinstance(self.specialites, list):
            noms = [choices_dict.get(k, k) for k in self.specialites if k in choices_dict]
        
        texte_specialites = ", ".join(noms) if noms else "Aucune spécialité"
        return f"{self.user.get_full_name() or self.user.username} ({texte_specialites})"

    class Meta:
        verbose_name = "Bénévole"
        verbose_name_plural = "Bénévoles"



"""====== Beneficiaire ========================================================
Information sur les bénéficiaires de don.
============================================================================""" 

class Beneficiaire(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.prenom} {self.nom}"



"""====== Intervention ========================================================
Notes de travail et de prise en charge par les bénévoles. Plus de papier !
============================================================================""" 

class Intervention(models.Model):
    TYPE_ACTION_CHOICES = [
        ('DIAG', 'Diagnostic'),
        ('REPA', 'Réparation'),
        ('NOTE', 'Note interne'),
        ('TRANSFERT', 'Transfert de prise en charge'),
        ('SORTIE', 'Sortie (Don/Recyclage)'),
    ]

    materiel = models.ForeignKey('Materiel', on_delete=models.CASCADE, related_name='interventions')
    benevole = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='interventions_faites')
    date_heure = models.DateTimeField(auto_now_add=True)
    type_action = models.CharField(max_length=20, choices=TYPE_ACTION_CHOICES, default='NOTE')
    commentaire = models.TextField()
    
    class Meta:
        ordering = ['-date_heure']
        verbose_name = "Intervention"
        verbose_name_plural = "Interventions"

    def __str__(self):
        return f"[{self.type_action}] {self.benevole} - {self.date_heure.strftime('%d/%m %H:%M')}"



"""====== Marque ==============================================================
Table externe qui sera utilisé quelque soit le type de matériel pour choisir
la marque du matériel saisi.
============================================================================""" 

class Marque(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    site_web = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.nom

    class Meta:
        ordering = ['nom']
        verbose_name_plural = "Marques"



"""====== Materiel ============================================================
Classe parente pour tous les matériels.
Contient notamment l'étape de workflow actuel et le numéro d'inventaire.   
============================================================================""" 

class Materiel(models.Model):

    # Les étapes du worklow
    STATUT_CHOICES = [
        ('ENTREE', 'En attente de diagnostic'),
        ('DIAGNOSTIC', 'En cours de diagnostic'),
        ('REPARATION', 'En cours de réparation'),
        ('PRET_A_DON', 'Réparé - Prêt à donner'),
        ('DONNE', 'Donné'),
        ('RECYCLAGE', 'Envoyé au recyclage'),
        ('PERDU', 'Perdu / Volé'),
    ]

    # Les différents types de matériel possibles
    TYPE_CHOICES = [
        ('PC', 'Ordinateur'),
        ('ECRAN', 'Écran'),
        ('PERIPH', 'Périphérique'),
    ]

    # Identification
    numero_inventaire = models.CharField(max_length=20, unique=True, blank=True, editable=False)
    type_materiel = models.CharField(max_length=10, choices=TYPE_CHOICES, default='PC')
    modele = models.CharField(max_length=100, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True)
    marque = models.ForeignKey(
        Marque, 
        on_delete=models.PROTECT, 
        related_name='materiaux',
        null=True, 
        blank=True,
        help_text="Marque du matériel"
    )

    # Flux & Poids
    date_entree = models.DateField(default=timezone.now)
    poids_entree_kg = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    provenance = models.CharField(max_length=200, blank=True)
    
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='ENTREE')
    
    # Gestion Bénévole
    benevole_en_charge = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='materiaux_en_charge')
    date_prise_en_charge = models.DateTimeField(null=True, blank=True)

    # Sortie
    date_sortie = models.DateTimeField(null=True, blank=True)
    poids_sortie_kg = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    
    beneficiaire = models.ForeignKey(Beneficiaire, null=True, blank=True, on_delete=models.SET_NULL, related_name='materiaux_recus')
    organisme_recyclage = models.CharField(max_length=100, blank=True)

    # Affichage en chaine dans liste et l'admin, exemple "INV-0004 - PC Lenovo Yoga Slim 7"
    def __str__(self):
        return f"{self.numero_inventaire} - {self.get_type_materiel_display()} ({self.marque} {self.modele})"

    # Surcharge de la fonction de sauvegarde avec :
    #   - si passage en DONNE ou RECYCLAGE :
    #     - renseignement auto de la date de sortie à la date du jour si info non fournie
    #     - renseignement auto du poid de sortie égal à poid d'entrée si non fourni
    def save(self, *args, **kwargs):
        if self.statut in ['DONNE', 'RECYCLAGE'] and not self.date_sortie:
            self.date_sortie = timezone.now()
            if not self.poids_sortie_kg:
                self.poids_sortie_kg = self.poids_entree_kg            
        super().save(*args, **kwargs)

    # Génération du numéro d'inventaire
    def generer_numero_inventaire(self):
        prefix = "INV-"
        last = Materiel.objects.exclude(numero_inventaire__isnull=True).exclude(numero_inventaire='').order_by('numero_inventaire').last()
        if last and last.numero_inventaire.startswith(prefix):
            try: new_num = int(last.numero_inventaire.split('-')[-1]) + 1
            except: new_num = 1
        else: new_num = 1
        return f"{prefix}{new_num:04d}"

    # Tri par défaut selon la date d'entrée
    class Meta:
        ordering = ['-date_entree']



"""====== Ecran ===============================================================
    Classe fille de Materiel destinée aux écrans.
============================================================================""" 

class Ecran(Materiel):

    DIAGONALE_CHOICES = [
        ('13.3', '13.3" (34 cm)'), ('14.0', '14.0" (36 cm)'), ('15.6', '15.6" (40 cm)'),
        ('21.5', '21.5" (55 cm)'), ('23.8', '23.8" (60 cm)'), ('24.0', '24" (61 cm)'),
        ('27.0', '27" (69 cm)'), ('32.0', '32" (81 cm)'), ('Autre', 'Autre')
    ]
    
    diagonale_pouces = models.CharField(max_length=10, choices=DIAGONALE_CHOICES, blank=True)
    resolution = models.CharField(max_length=20, blank=True)
    connectique = models.CharField(max_length=100, blank=True)

    # On force le type pour éviter les problèmes d'héritage (valeur par défaut dans la classe parente)
    def save(self, *args, **kwargs):
        self.type_materiel = 'ECRAN'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Écran"
        verbose_name_plural = "Écrans"



"""====== Peripherique ========================================================
    Classe fille de Materiel destinée aux periphériques (clavier, ...).
============================================================================""" 

class Peripherique(Materiel):

    TYPE_PERIPH_CHOICES = [
        ('CLAVIER', 'Clavier'), ('SOURIS', 'Souris'), ('WEBCAM', 'Webcam'),
        ('CASQUE', 'Casque'), ('ENCEINTES', 'Enceintes'), ('HUB', 'Hub USB'), ('AUTRE', 'Autre')
    ]
    
    type_periph = models.CharField(max_length=20, choices=TYPE_PERIPH_CHOICES, default='AUTRE')
    connectique = models.CharField(max_length=50, blank=True)
    avec_cable = models.BooleanField(default=True)

    # On force le type pour éviter les problèmes d'héritage (valeur par défaut dans la classe parente)
    def save(self, *args, **kwargs):
        self.type_materiel = 'PERIPH'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Périphérique"
        verbose_name_plural = "Périphériques"



"""====== Ordinateur ==========================================================
    Classe fille de Materiel destinée aux ordis.
============================================================================""" 

class Ordinateur(Materiel):

    CATEGORIE_CHOICES = [
        ('FIXE', 'PC Fixe / Tour'),
        ('PORTABLE', 'PC Portable'),
        ('ALL_IN_ONE', 'All-in-One'),
    ]
    
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='FIXE')
    
    # CPU & RAM Détaillée
    cpu = models.CharField(max_length=100, blank=True)
    cpu_score = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="Indice PassMark (https://www.cpubenchmark.net/). Si < 800 : recyclage recommandé."
    )
    ram_go = models.PositiveIntegerField(default=0)
    ram_nb_barrettes = models.PositiveIntegerField(default=1)
    ram_type = models.CharField(
        max_length=20, 
        choices=[
            ('DDR2', 'DDR2'), ('DDR3', 'DDR3'), ('DDR3L', 'DDR3 Low Voltage'),
            ('DDR4', 'DDR4'), ('DDR5', 'DDR5'), ('SODIMM', 'SODIMM'),
            ('INCONNUE', 'Inconnue')
        ],
        default='INCONNUE'
    )
    
    # Spécifique Portable
    a_alimentation = models.BooleanField(default=True)
    etat_batterie = models.CharField(
        max_length=20, 
        choices=[
            ('N/A', 'Non concerné'), ('EXCELLENT', 'Comme neuve'), ('BON', 'Correcte'),
            ('FAIBLE', 'Faible'), ('HS', 'HS'), ('INCONNUE', 'Non testée')
        ],
        default='N/A'
    )
    ecran_diagonale_pouces = models.CharField(
        max_length=10, 
        choices=[
            ('13.3', '13.3" (34 cm)'), ('14', '14" (36 cm)'), ('15.6', '15.6" (40 cm)'),
            ('16', '16" (40.6 cm)'), ('17.3', '17.3" (44 cm)'), ('AUTRE', 'Autre')
        ],
        blank=True
    )

    # Autres infos hardware
    a_carte_graphique_dediee = models.BooleanField(default=False)
    modele_gpu = models.CharField(max_length=100, blank=True)   
    a_carte_wifi = models.BooleanField(
        default=False, 
        help_text="Présence d'une carte WiFi (interne ou clé USB fournie). Crucial pour les Tours."
    )

    # Linux & Logiciels
    linux_installe = models.BooleanField(default=False)
    linux_distro = models.CharField(
        max_length=50, 
        blank=True, 
        choices=[
            ('ANDUIN', 'AnduinOS'), ('ZORIN', 'Zorin OS'), ('UBUNTU', 'Ubuntu'),
            ('LINUX_MINT', 'Linux Mint'), ('AUTRE', 'Autre'),
        ]
    )
    date_maj_os = models.DateField(null=True, blank=True)
    
    onlyoffice_installe = models.BooleanField(default=False)
    logiciel_photo = models.CharField(
        max_length=50, blank=True, 
        choices=[('AUCUN', 'Aucun'), ('GIMP', 'GIMP'), ('PHOTOFLARE', 'Photoflare'), ('DARKTABLE', 'Darktable')]
    )
    media_player = models.CharField(
        max_length=50, blank=True, 
        choices=[('VLC', 'VLC'), ('DEFAULT', 'Défaut OS'), ('MPV', 'MPV')]
    )
    firefox_configure = models.BooleanField(default=False)    

    # Réparation
    pieces_changees = models.TextField(blank=True)
    cout_reparation = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    # On force le type pour éviter les problèmes d'héritage (valeur par défaut dans la classe parente)
    def save(self, *args, **kwargs):
        self.type_materiel = 'PC'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Ordinateur"
        verbose_name_plural = "Ordinateurs"



"""====== DisqueDur ===========================================================
Permet de stocker les disques durs, avec éventuellement un numéro 
d'inventaire quand ils sont testés en remis en stock.
============================================================================"""

class DisqueDur(models.Model):

    # ForeignKey avec null=True pour permettre les disques en stock sans PC
    ordinateur = models.ForeignKey(
        Ordinateur, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='disques'
    )
    
    # Numéro d'inventaire disque, ne sera utilisé que si disque testé !
    validateur_numero_disque = RegexValidator(
        regex=r'^DSK-\d{4}$',
        message="Le format doit être DSK- suivi de 4 chiffres (ex: DSK-0042)."
    )
    numero_inventaire_disque = models.CharField(
        max_length=20, 
        unique=True, 
        null=True, 
        blank=True, 
        validators=[validateur_numero_disque], # <--- Application du validateur
        verbose_name="N° Inventaire Disque",
        help_text="Uniquement si testé! Format obligatoire : DSK-0001"
    )

    # Caractéristiques techniques    
    TYPE_CHOICES = [
        ('HDD', 'HDD (Mécanique)'), ('SSD', 'SSD (SATA)'), 
        ('NVME', 'SSD (NVMe)'), ('HYBRIDE', 'SSHD')
    ]
    
    capacite_go = models.PositiveIntegerField()
    type_disque = models.CharField(max_length=10, choices=TYPE_CHOICES, default='HDD')
    marque = models.CharField(max_length=100, blank=True)
    modele = models.CharField(max_length=100, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True)
    
    # Etat général après test
    est_sain = models.BooleanField(default=True)
    contient_donnees = models.BooleanField(default=False)

    def __str__(self):
        if self.numero_inventaire_disque:
            return f"[{self.numero_inventaire_disque}] {self.type_disque} {self.capacite_go}Go"
        return f"{self.type_disque} {self.capacite_go}Go - {self.marque}"

    class Meta:
        ordering = ['numero_inventaire_disque', 'type_disque']
        verbose_name = "Disque Dur"
        verbose_name_plural = "Disques Durs"

