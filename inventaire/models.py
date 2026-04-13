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
        ('DIAG', 'Diagnostic et réparation'),
        ('CONFIG', 'Configuration OS et logicielle'),
        ('NOTE', 'Note de travail'),
        ('TRANSFERT', 'Transfert de prise en charge'),
        ('SORTIE', 'Sortie (don/recyclage)'),
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
        ('ENTREE', 'Attente de diagnostic'),
        ('DIAGNOSTIC', 'Diagnostic en cours'),
        ('ATTENTE_PIECES', 'En attente de pièces'),
        ('POUR_PIECES', 'Pour pièces'),
        ('EN_COURS_DEMONTAGE', 'Démontage en cours'),
        ('CONFIGURATION', 'Installation' ),
        ('PRET_A_DON', 'Prêt à donner'),
        ('DONNE', 'Donné'),
        ('RECYCLAGE', 'Recyclé'),
        ('PERDU', 'Perdu / volé'),
    ]

    # Les différents types de matériel possibles
    TYPE_CHOICES = [
        ('PC', 'Ordinateur'),
        ('ECRAN', 'Écran'),
        ('PERIPH', 'Périphérique'),
    ]

    CATEGORIES_PROVENANCE = [
        ('DECHETTERIE', 'Déchetterie'),
        ('PARTENARIAT', 'Partenariat'),
        ('DON', 'Don'),
    ]

    SOURCES_PROVENANCE = [
        # Déchetteries
        ('sictom_nogent', 'Sictom Nogent'),
        ('sictom_thirons', 'Sictom Thirons'),
        ('dechetterie_autre', 'Autre déchetterie'),
        # Partenariats
        ('lycee_sully', 'Lycée Sully'),
        ('partenariat_autre', 'Autre partenariat'),
        # Dons
        ('don_prive', 'Don privé'),
        ('don_public', 'Don du secteur public'),
        ('don_entreprise', "Don d'entreprise"),
        ('don_asso', "Don d'association"),
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


    # Provenance : on stocke uniquement la source précise (ex: 'sictom_nogent')
    # La catégorie (Déchetterie, ...) est facilement récupérable via le code
    provenance = models.CharField(
        max_length=30,
        choices=SOURCES_PROVENANCE,
        default='sictom_nogent', # Valeur par défaut sécurisée
        help_text="Origine du matériel"
    )
    # Optionnel : Un champ texte libre si "Autre" est sélectionné
    provenance_precisions = models.CharField(
        max_length=200,
        blank=True,
        help_text="Précisez le nom si 'Autre' est sélectionné"
    )

    # Flux & Poids
    date_entree = models.DateField(default=timezone.now)
    poids_entree_kg = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    rapport_diagnostic = models.TextField(blank=True)
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
    def save(self, *args, **kwargs):
        # 1. Génération automatique du numéro d'inventaire si vide
        if not self.numero_inventaire:
            self.numero_inventaire = self.generer_numero_inventaire()
        
        # 2. Gestion automatique de la sortie (Don/Recyclage)
        if self.statut in ['DONNE', 'RECYCLAGE']:
            if not self.date_sortie:
                self.date_sortie = timezone.now()
            # On ne force le poids de sortie que s'il est vraiment nul/absent
            # Cela laisse la possibilité de le modifier manuellement si besoin (ex: pièces retirées)
            if self.poids_sortie_kg is None or self.poids_sortie_kg == 0:
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
    
    # Récupération du type de provenance d'après la source précise
    def get_categorie_provenance(self):
        if self.provenance in ['sictom_nogent', 'sictom_thirons', 'dechetterie_autre']:
            return 'DECHETTERIE'
        elif self.provenance in ['lycee_sully', 'partenariat_autre']:
            return 'PARTENARIAT'
        else:
            return 'DON'

    class Meta:
        # Tri par défaut selon la date d'entrée
        ordering = ['-date_entree']
        # Permissions spécifiques qui vont s'ajouter aux CRUDs
        permissions = [
            ("can_print_labels", "Peut imprimer les étiquettes et rapports"),
            ("can_validate_don", "Peut valider les dons aux bénéficiaires"), # si l'on veut affiner les droits des admins
        ]



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

    '''
        Tous les choix utilisés dans les différents SELECT sont regroupés ici
        pour faciliter la maintenance ! 
    '''
    CATEGORIE_CHOICES = [ 
        ('FIXE', 'PC Fixe / Tour'),
        ('PORTABLE', 'PC Portable'),
        ('ALL_IN_ONE', 'All-in-One'),
    ]
    RAM_CHOICES = [
            ('DDR2', 'DDR2'), ('DDR3', 'DDR3'), ('DDR3L', 'DDR3 Low Voltage'),
            ('DDR4', 'DDR4'), ('DDR5', 'DDR5'), ('SODIMM', 'SODIMM'),
            ('INCONNUE', 'Inconnue')
    ]
    DISQUE_CHOICES = [
        ('HDD', 'HDD (Mécanique)'), ('SSD', 'SSD (SATA)'), 
        ('NVME', 'SSD (NVMe)'), ('HYBRIDE', 'SSHD')
    ]
    ECRAN_CHOICES = [ # pour les portables !
            ('12', '12"'),('13', '13"'), ('14', '14"'), ('15', '15.6" ou 16"'),
            ('17', '17"'), ('18', '18"'), ('AUTRE', 'Autre')        
    ]
    ETAT_BATTERIE_CHOICES = [
            ('N/A', 'Non concerné'), ('EXCELLENT', 'Comme neuve'), ('BON', 'Correcte'),
            ('FAIBLE', 'Faible'), ('HS', 'HS'), ('INCONNUE', 'Non testée')
    ]
    WIFI_CHOICES = [
        ('NON', '❌ Non / HS'),
        ('INTEGRE', '✅ Intégré (Carte mère)'),
        ('CARTE', '✅ Intégré (Carte fille)'),
        ('CLEF_ORIGINE', '🔑 Clef WiFi d\'origine fournie'),
        ('CLEF_ACHAT', '💰 Clef WiFi achetée (à facturer)')
    ]
    DISTRIB_CHOICES = [
        ('ANDUIN_LTS_1_1', 'AnduinOS LTS 1.1'), ('ANDUIN_1_4', 'AnduinOS 1.4'), ('ZORIN_18', 'Zorin OS 18 Core'), ('POPOS_LTS_24', 'Pop!_OS 24.04 LTS'), 
        ('POPOS_LTS_24_NVIDIA', 'Pop!_OS 24.04 LTS with NVIDIA'), ('UBUNTU_LTS_24', 'Ubuntu LTS 24'), ('UBUNTU_25', 'Ubuntu 25'),
        ('UBUNTU_SERVER_LTS_24', 'Ubuntu Server LTS 24'), ('AUTRE', 'Autre (préciser dans le rapport)')
    ]
    PHOTO_CHOICES = [('AUCUN', 'Aucun'), ('GIMP', 'GIMP'), ('DARKTABLE', 'Darktable'), ('PHOTOFLARE', 'Photoflare'), ('PINTA', 'Pinta')]
    MEDIA_CHOICES = [('DEFAULT', 'Défaut OS'), ('CELLULOID', 'Celluloid'), ('HARUNA', 'Haruna'), ('MPV', 'MPV'), ('VLC', 'VLC')]


    # ----- Type d'ordinateur
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='FIXE')
    
    # ----- CPU & RAM Détaillée
    cpu = models.CharField(max_length=100, blank=True)
    cpu_score = models.PositiveIntegerField(default=0)
    ram_go = models.PositiveIntegerField(default=0)
    ram_nb_barrettes = models.PositiveIntegerField(default=0)
    ram_type = models.CharField(max_length=20, choices=RAM_CHOICES, default='INCONNUE')

    # ----- Disques 
    disque_principal_type = models.CharField(max_length=10, choices=DISQUE_CHOICES, blank=True)    
    disque_principal_go = models.PositiveIntegerField(default=0)
    disque_secondaire_type = models.CharField(max_length=10, choices=DISQUE_CHOICES, blank=True)    
    disque_secondaire_go = models.PositiveIntegerField(default=0, blank=True)
    
    
    # ----- Spécifique Portable
    a_alimentation = models.BooleanField(default=True)
    etat_batterie = models.CharField(max_length=20, choices=ETAT_BATTERIE_CHOICES, default='N/A')
    ecran_diagonale_pouces = models.CharField(max_length=10, choices=ECRAN_CHOICES, blank=True)

    # ----- Autres infos hardware
    a_carte_graphique_dediee = models.BooleanField(default=False)
    modele_gpu = models.CharField(max_length=100, blank=True)   
    statut_wifi = models.CharField(max_length=20, choices=WIFI_CHOICES, default='NON')

    # ----- Linux & Logiciels
    linux_installe = models.BooleanField(default=False)
    linux_distro = models.CharField(max_length=50, blank=True, choices=DISTRIB_CHOICES)
    date_maj_os = models.DateField(null=True, blank=True)
    dns_configures = models.BooleanField(default=False)
    langue_configuree = models.BooleanField(default=False)
    onlyoffice_installe = models.BooleanField(default=False)
    firefox_configure = models.BooleanField(default=False)
    firefox_extensions = models.BooleanField(default=False)
    logiciel_photo = models.CharField(max_length=50, blank=True, choices=PHOTO_CHOICES)
    media_player = models.CharField(max_length=50, blank=True, choices=MEDIA_CHOICES)
    rapport_configuration = models.TextField(
        blank=True, 
        help_text="Merci d'indiquer les spécificités de configuration logicielle : distribution et version si non standard, autres logiciels installés, " \
            "autres comptes créés, problèmes rencontrés, etc."
    ) 

    # On force le type pour éviter les problèmes d'héritage (valeur par défaut dans la classe parente)
    def save(self, *args, **kwargs):
        self.type_materiel = 'PC'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Ordinateur"
        verbose_name_plural = "Ordinateurs"



"""====== Pièces détachées ====================================================
    Stockage et tracage des pièces détachées.
============================================================================""" 

class PieceDetachee(models.Model):
    
    CATEGORIE_CHOICES = [
        ('RAM', 'Barrette RAM'),
        ('DISQUE', 'Disque Dur / SSD'),
        ('ECRAN_PC', 'Écran de PC Portable'),
        ('BATTERIE', 'Batterie Portable'),
        ('ALIM', 'Alimentation Externe'),
        ('CARTE_WIFI', 'Carte WiFi'),
        ('CLEF_WIFI', 'Clef WiFi'),
        ('CARTE_GRAPHIQUE', 'Carte Graphique (Tour)'),
        ('CLAVIER', 'Clavier de PC Portable'),
        ('LECTEUR_OPTIQUE', 'Lecteur DVD/Blu-Ray'),
        ('DIVERS', 'Divers (Charnière, Nappe, Vis...)'),
    ]

    ETAT_CHOICES = [
        ('NON_TESTE', '❓ Non testé / Inconnu'),
        ('TESTE_BON', '✅ Testé & Fonctionnel'),
        ('NETTOYAGE', '🧼 En cours de nettoyage/effacement'),
        ('RESERVE', '🔒 Réservé pour un projet'),
        ('HS', '❌ HS / À recycler'),
    ]

    # ----- Numéro d'inventaire 
    # Format : PCD-XXXX (ex: PCD-0042)
    validateur_numero_piece = RegexValidator(
        regex=r'^PCD-\d{4}$',
        message="Le format doit être PCD- suivi de 4 chiffres (ex: PCD-0042)."
    )
    numero_inventaire = models.CharField(
        max_length=20,
        unique=True,
        blank=True,  # optionnel dans les formulaires
        null=True,   # optionnel dans la base de données (stocké comme NULL)
        validators=[validateur_numero_piece], # La validation ne s'applique que si le champ n'est pas vide
        verbose_name="N° Inventaire Pièce",
        help_text="Laisser vide pour l'instant. Sera généré automatiquement à l'étiquetage."
    )

    # ----- Identification
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES)
    marque = models.CharField(max_length=100, blank=True, help_text="Marque du composant")
    modele = models.CharField(max_length=100, blank=True, help_text="Référence constructeur")
    specifications = models.TextField(
        blank=True, 
        help_text="Détails techniques (Ex: 8Go DDR4, 500Go SSD, 15.6' FHD IPS, 65W)"
    )
    
    # ----- Traçabilité (origine & destination)
    pc_origine = models.ForeignKey(
        'Materiel', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='pieces_recuperees',
        help_text="PC d'origine (si récupération sur matériel)"
    )
    pc_destination = models.ForeignKey(
        'Materiel', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='pieces_installees',
        help_text="Installée dans le PC (si réemploi)"
    )

    # ----- État & stock
    etat = models.CharField(max_length=20, choices=ETAT_CHOICES, default='NON_TESTE')
    emplacement = models.CharField(
        max_length=50, 
        blank=True, 
        help_text="Localisation physique (Ex: Étagère A, Boîte RAM-DDR4)"
    )
    poids_kg = models.DecimalField(
        max_digits=6, 
        decimal_places=3, 
        default=0, 
        help_text="Poids de la pièce seule (pour bilan matière précis)"
    )
    cout_achat = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=0.00,
        help_text="Coût d'achat de la pièce (0 si issue du recyclage/cannibalisation)."
    )

    # ----- Dates
    date_entree_stock = models.DateTimeField(auto_now_add=True)
    date_sortie_stock = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text="Date d'installation ou de sortie définitive"
    )

    # ----- Génération du numéro d'inventaire
    def generer_numero_inventaire(self):
        """Génère le prochain numéro disponible de type PCD-XXXX."""
        prefix = "PCD-"
        
        # On récupère la dernière pièce créée ayant un numéro d'inventaire
        last_piece = PieceDetachee.objects.filter(
            numero_inventaire__isnull=False
        ).exclude(
            numero_inventaire=''
        ).order_by('-numero_inventaire').first()
        
        if last_piece and last_piece.numero_inventaire.startswith(prefix):
            try:
                # On extrait les 4 chiffres et on ajoute 1
                last_num = int(last_piece.numero_inventaire.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1
            
        return f"{prefix}{new_num:04d}"

    # ----- Surcharge de la sauvegarde
    def save(self, *args, **kwargs):
        # UNIQUEMENT si le champ est vide (None ou ''), on génère un numéro.
        # Si l'utilisateur a volontairement laissé vide, on ne fait rien (reste NULL).
        # Si l'utilisateur a mis un numéro manuellement, on ne fait rien (garde le sien).
        if not self.numero_inventaire:
            self.numero_inventaire = self.generer_numero_inventaire()
        
        super().save(*args, **kwargs)

    def __str__(self):
        origine = f" (ex-{self.pc_origine.numero_inventaire})" if self.pc_origine else ""
        destination = f" → {self.pc_destination.numero_inventaire}" if self.pc_destination else ""
        return f"{self.get_categorie_display()} - {self.specifications[:30]}{origine}{destination}"

    class Meta:
        verbose_name = "Pièce Détachée"
        verbose_name_plural = "Pièces Détachées"
        ordering = ['-date_entree_stock']
        indexes = [
            models.Index(fields=['categorie', 'etat']), # Optimisation des recherches
        ]

