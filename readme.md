# 🛠️ Outil de Gestion - Atelier de Reconditionnement Numérique (LBAO)

Application web de gestion de stock et de suivi de flux pour l'association **LBAO**. Elle permet de tracer le parcours complet d'un matériel informatique, de sa récupération jusqu'à son don à un particulier ou son recyclage, en passant par le diagnostic et la réparation.

## 🎯 Objectifs du Projet

*   **Traçabilité totale** : Savoir où est chaque machine, qui s'en occupe, et quelles interventions ont été réalisées.
*   **Optimisation du flux** : Identifier rapidement les goulots d'étranglement (ex: machines en attente de diagnostic).
*   **Conformité & Écologie** : Suivre les poids entrants/sortants pour les conventions de recyclage et garantir la qualité du matériel donné (critères de performance).
*   **Travail collaboratif** : Permettre à plusieurs bénévoles de travailler simultanément sur le parc avec un suivi des compétences.

---

## 🏗️ Architecture Technique

*   **Backend** : Python 3.x + Django 5.x
*   **Base de données** : SQLite (Développement) / PostgreSQL (Production)
*   **Frontend** : Templates Django + Bootstrap 5 (via `django-bootstrap5`)
*   **Authentification** : Système d'utilisateurs Django étendu avec profils bénévoles.

### Modèle de Données

Le cœur du système repose sur une gestion hiérarchique du matériel (`Materiel` parent, `Ordinateur`/`Écran`/`Périphérique` enfants) et une traçabilité fine via un journal d'interventions.

Vous pouvez voir dans *Mermaid* le [schéma de donnée](https://mermaid.live/edit#pako:eNqtWO9y4jYQfxWNO3dHpuAJgZCEbwR8F_cIUANpek3Ho9gCdGdLPllOkyZ5gLxFv_XyHLxYVzYQ2yhpOj0-MEbWSvvnt7_d5dbwuE-MtkFEj-K5wOEFQ_B58wbVajVUN9F0YvftcWdiTZ0xeouOlw-D5cPZsG-N1Y5s93RsOeg2e1YfyiSiPhp9fFqKpaBsjpKYCIZDsvWChJgGW6szKmLpagUCXHhzf8Gyh2NrYCn1_kUftaSUcWH9_Ud0YUwZ_ZqQKroiIk4NujC27pQkINGCs5w2n2POUBwRj-KAShLDSb-9O_nFnQynzrsqete3B9NzeDBN8_f8iZecBwQzhD1JZyUTVs7fM1fefm937Y7t5D2urFwvv87zjIdba5EgumV9LDTGS3ItEfYFiePcqo8lkTQk6YPrCYIl5UxvY8NEpx3n5ynYVnGWj7PlI6jkEdQlTAockJ0nk7N9rzZ2E1JNHGOIlPsHudTr1FQ6TZYPjm31UWWCLwOCTpffRFGZiZW-f506SUgEdym7ArMwFSSHt04iOarYg7PaOXx2dKi7iYgbgi8FJQFIjrpVZHWdzqCKRqDE6CQvo5QIsYCjN8g-U4jOvKc5PYT8D8hzKsfq0mJos7Cq-JD8G8iAEAco4tSPV2_dL3MN5Dg4AUOMt6MisUwkKGwNJo5lVVHP7nyoIscadeB5OFCP3V8hkfJWFMEWcyGp8m7mVYCez1lwU_BqUdNMoqCpcuElYeQKMhQscb0FFvOSO8sEUVQjEjTOiW4fPaPAF4CD4qH5pNZEios5ZjQOiSuId-MFeE70AN43kT0AfJ6BI-3hAFLrJ54A7QY5AOc3vIIq1_ArgyrLgjIAN977Dz5bkEQQPfYVRwLLXhh5QAyGE6uEhZSOPB6GqyzTe6dloqHTswerklYZR8tHj85UNiKLCeotaM5PT1vLXtq4JJIC_FXNLD0BBqMSQpMVEp2HVqZ5ID_nIoXre_sc8D4aOpPOcR-eOvYwL7EtGyVFZWDBjT2eMovNfAoUOsJxfIrFF7CQJDRAh7u7O9oK5HpYKD4EH4B0VySqlkF6JAIFUNAm8BDrtVE3Q8vgzvn2Grt0L7EQREJR3NJfbVChVTHtOQ1I757TTL_3SzHd1jegLLkGLgW6CDTElb32KfzkigiYn1BWRZ_A00zDHRn4QvzZ5fH2XYo8-AyylbxwIZ9DNiscLLhUV36wT0cQTPVrFmBBSreueZf4FLtRgG-IUBnSB1bvkRlOAlkSWCsDzRCZ8WvX42xG54Vs0UUV-pE0EZ6Kb77EwzrER6YQVpR73rX6faCDKjpWTHsy1mtNPIEZeBfPOfAJMB1PvLTpqTdMCGN932yBIKrEFAAkpKqdOy-Hcw0_6D2jhUpC1wfPEPJMoXLneeiXcj-iBLRRrMvmJA-7Ned7PJHAnhEWL_QkByZUnnHak_RShshaAOsanMWgFYAI5Rki2-v2ps4reJQLnzJAXCKK3JijmcogCYIXHPdcT6EwrzjsqbUYRspIRgLgJi6Ar1Bv_LH2A3yeT2cPR9hT7VE-p_NkvLnlpNerovEYvgZnp9rOIm1D_l_DsUYJgWY_xpRtv4FsgALOpOsrU9dBL8f00ETLB9Uz5XrotIf63qz-TGqg5V-osfcjquAr4iEv1PV50EbzINGmq6dsgyq48WfZviMTjVTHOjpR3yl2N3ZmTaKVLn9vc1NIRHBEtFC1o985sy0HYAHTj_0MhWzZUmADcA8QwmXwjJ2O1e9kPU1q3uadGlQlDWic5lacG0vv7mq1u7unsbANemKUMNWJzqAsVurt-iYaGwl-W-yQlJRYPgKnxkSJDLQim6lAbVfDlY8IIDRtAp-kNkrDgHea5kicDtaPDAagVWMYF2Ye3fHLx68JjUrKFMZCnZQgy785lRpl1CSGpQo8DBlv0QYCpXln5c4cX6ljF-luUnRmWSbLt1dvL8BWK7XRHSY2mwGQFRVC-sRPDa_maF1oIx7Hy2--LkjQTA83pK0C1UsJEO5wSJBWEQQyVeCvNWuX-8Y7nl6aqxPqyjVvocquaWZ3GlVjLqhvtKUA-jaAD2EQh59GmrQXhlyQEMZZJe1DY6dE7kEmwuwT5-FaTPBkvjDaMxzE8CuJVIOz-m9nswWQSUSXJ0wa7VbrID3DaN8a10a7Xq-bzUbrYO-o2ajX9_cazapxY7RrjXrT3D_abR42W_WjenO3dV81_kyvhf27zdZe6-jo4LB50NxvHt7_A3Y7fjI) complet avec toutes les relations.


## 📋 Règles Métier Importantes

Ces règles sont codées en dur dans l'application (models.py et views.py) et sont cruciales pour l'activité de l'association.

### 1. Critère de Performance CPU

    Règle : Tout ordinateur avec un indice PassMark CPU < 800 est considéré comme inadapté à une utilisation moderne (navigation web fluide), même sous Linux.
    Action : Ces machines sont orientées directement vers le recyclage pour éviter de perdre du temps de bénévolat sur des réparations non rentables.
    Source : cpubenchmark.net

### 2. Gestion des Disques Durs (Pièces Détachées)

    Inventaire propre : Les disques durs testés et sains reçoivent un numéro d'inventaire spécifique au format DSK-#### (ex: DSK-0042).
    Validation : Le format est imposé par une validation regex dans le modèle.
    Stockage : Un disque peut être dissocié d'un ordinateur pour être stocké comme pièce de rechange (ordinateur_id nullable).

### 3. Suivi des Poids (Convention Recyclage)

    Automatisme : Le poids_sortie_kg est automatiquement rempli avec la valeur du poids_entree_kg lors du passage en statut "Donné" ou "Recyclé".
    Exception : Il peut être modifié manuellement si des pièces ont été retirées (ex: disque dur gardé en stock, batterie HS retirée).
    Objectif : Fournir des chiffres exacts pour les bilans écologiques annuels.

### 4. Compétences Bénévoles

    Chaque bénévole possède un profil avec des spécialités multiples (Hardware Tour, Portable, Linux, Shell, etc.).
    Cela permet d'affecter les tâches aux bonnes personnes (ex: assigner un PC portable à un bénévole cochant "Hardware PC Portable").

## 📂 Structure du Projet

```plain text
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
```

## 🚀 Démarrage Rapide ()

Pour ceux souhaitant participer au code...

### 1. Prérequis

    Python 3.8+
    Git

### 2. Installation

```bash
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
```

### 3. Accès

    Site local : http://127.0.0.1:8000/
    Interface Admin : http://127.0.0.1:8000/admin/

## 📝 Procédures Opérationnelles

Pour les guides pas-à-pas destinés aux utilisateurs (ex: "Comment enregistrer une entrée ?", "Comment tester un disque dur ?"), veuillez consulter le dossier docs/.

    docs/ENTREE_MATERIEL.md : Procédure de pesée et d'enregistrement.
    docs/DIAGNOSTIC_CPU.md : Comment trouver et saisir le score CPU.
    docs/CONFIGURATION_LINUX.md : Checklist des logiciels à installer (OnlyOffice, GIMP, etc.).

## 🤝 Contribuer

    Créer une branche pour votre fonctionnalité (git checkout -b feature/nouvelle-fonction).
    Committer vos changements avec des messages clairs.
    Pusher la branche et ouvrir une Pull Request.
    Important : Mettre à jour ce README si vous ajoutez une nouvelle règle métier ou un nouveau champ critique.

Développé avec ❤️ pour l'association LBAO - Favoriser le réemploi numérique !
