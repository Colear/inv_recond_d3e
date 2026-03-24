
🛠️ Outil de Gestion - Atelier de Reconditionnement Numérique (LBAO)

Application web de gestion de stock et de suivi de flux pour l'association LBAO. Elle permet de tracer le parcours complet d'un matériel informatique, de sa récupération jusqu'à son don à un particulier ou son recyclage, en passant par le diagnostic et la réparation.
🎯 Objectifs du Projet

    Traçabilité totale : Savoir où est chaque machine, qui s'en occupe, et quelles interventions ont été réalisées.
    Optimisation du flux : Identifier rapidement les goulots d'étranglement (ex: machines en attente de diagnostic).
    Conformité & Écologie : Suivre les poids entrants/sortants pour les conventions de recyclage et garantir la qualité du matériel donné (critères de performance).
    Travail collaboratif : Permettre à plusieurs bénévoles de travailler simultanément sur le parc avec un suivi des compétences.

🏗️ Architecture Technique

    Backend : Python 3.x + Django 5.x
    Base de données : SQLite (Développement) / PostgreSQL (Production)
    Frontend : Templates Django + Bootstrap 5 (via django-bootstrap5)
    Authentification : Système d'utilisateurs Django étendu avec profils bénévoles.

Modèle de Données

Le cœur du système repose sur une gestion hiérarchique du matériel (Materiel parent, Ordinateur/Écran/Périphérique enfants) et une traçabilité fine via un journal d'interventions.

mermaid
erDiagram
    USER ||--|| BENEVOLE : "a un profil"
    USER ||--o{ INTERVENTION : "réalise"
    USER ||--o{ MATERIEL : "prend en charge"
    MARQUE ||--o{ MATERIEL : "équipe"
    BENEFICIAIRE ||--o{ MATERIEL : "reçoit"
    
    MATERIEL ||--|| ORDINATEUR : "hérite"
    MATERIEL ||--|| ECRAN : "hérite"
    MATERIEL ||--|| PERIPHERIQUE : "hérite"
    
    MATERIEL ||--o{ INTERVENTION : "possède"
    ORDINATEUR |o--o{ DISQUE_DUR : "contient"

    MATERIEL {
        string numero_inventaire "INV-XXXX"
        string statut "ENTREE, DIAG, REPA, DON, RECY"
        decimal poids_entree_kg
        decimal poids_sortie_kg
    }
    ORDINATEUR {
        int cpu_score "Seuil 800"
        boolean a_carte_wifi
        boolean linux_installe
    }
    DISQUE_DUR {
        string numero_inventaire_disque "DSK-####"
        boolean est_sain
    }

📋 Règles Métier Importantes

Ces règles sont codées en dur dans l'application (models.py et views.py) et sont cruciales pour l'activité de l'association.
1. Critère de Performance CPU

    Règle : Tout ordinateur avec un indice PassMark CPU < 800 est considéré comme inadapté à une utilisation moderne (navigation web fluide), même sous Linux.
    Action : Ces machines sont orientées directement vers le recyclage pour éviter de perdre du temps de bénévolat sur des réparations non rentables.
    Source : cpubenchmark.net

2. Gestion des Disques Durs (Pièces Détachées)

    Inventaire propre : Les disques durs testés et sains reçoivent un numéro d'inventaire spécifique au format DSK-#### (ex: DSK-0042).
    Validation : Le format est imposé par une validation regex dans le modèle.
    Stockage : Un disque peut être dissocié d'un ordinateur pour être stocké comme pièce de rechange (ordinateur_id nullable).

3. Suivi des Poids (Convention Recyclage)

    Automatisme : Le poids_sortie_kg est automatiquement rempli avec la valeur du poids_entree_kg lors du passage en statut "Donné" ou "Recyclé".
    Exception : Il peut être modifié manuellement si des pièces ont été retirées (ex: disque dur gardé en stock, batterie HS retirée).
    Objectif : Fournir des chiffres exacts pour les bilans écologiques annuels.

4. Compétences Bénévoles

    Chaque bénévole possède un profil avec des spécialités multiples (Hardware Tour, Portable, Linux, Shell, etc.).
    Cela permet d'affecter les tâches aux bonnes personnes (ex: assigner un PC portable à un bénévole cochant "Hardware PC Portable").

📂 Structure du Projet

plain text
mon_projet/
├── manage.py
├── README.md                # Ce fichier
├── docs/                    # Documentation complémentaire (procédures, etc.)
├── inventaire/              # Application principale
│   ├── models.py            # Définition des données (Règles métier incluses)
│   ├── views.py             # Logique d'affichage et tableaux de bord
│   ├── admin.py             # Interface d'administration (configurée)
│   ├── forms.py             # Formulaires de saisie
│   ├── templates/           # Templates HTML
│   │   ├── parts/           # Composants réutilisables (menu, footer, bootstrap)
│   │   ├── home.html        # Tableau de bord
│   │   └── inventaire/      # Vues listes et détails
│   └── migrations/          # Historique des changements de BDD
└── mon_projet/              # Configuration du projet Django
    ├── settings.py
    └── urls.py

🚀 Démarrage Rapide (Pour les bénévoles)
1. Prérequis

    Python 3.8+
    Git

2. Installation

bash
# Cloner le projet
git clone https://github.com/votre-org/inv_recond.git
cd inv_recond

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement
# Sur Linux/Mac:
source venv/bin/activate
# Sur Windows:
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Initialiser la base de données
python manage.py migrate

# Créer un compte administrateur
python manage.py createsuperuser

# Lancer le serveur
python manage.py runserver

3. Accès

    Site local : http://127.0.0.1:8000/
    Interface Admin : http://127.0.0.1:8000/admin/

📝 Procédures Opérationnelles

Pour les guides pas-à-pas destinés aux utilisateurs (ex: "Comment enregistrer une entrée ?", "Comment tester un disque dur ?"), veuillez consulter le dossier docs/.

    docs/ENTREE_MATERIEL.md : Procédure de pesée et d'enregistrement.
    docs/DIAGNOSTIC_CPU.md : Comment trouver et saisir le score CPU.
    docs/CONFIGURATION_LINUX.md : Checklist des logiciels à installer (OnlyOffice, GIMP, etc.).

🤝 Contribuer

    Créer une branche pour votre fonctionnalité (git checkout -b feature/nouvelle-fonction).
    Committer vos changements avec des messages clairs.
    Pusher la branche et ouvrir une Pull Request.
    Important : Mettre à jour ce README si vous ajoutez une nouvelle règle métier ou un nouveau champ critique.

Développé avec ❤️ pour l'association LBAO - Favoriser le réemploi numérique.