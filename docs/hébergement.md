# Hébergement

## Les scénarios

### Scénario 1 - hébergement internet

* l'application est hebergée sur un VPS (Virtual Private Server) si possible indépendant GAFAM (OVH, ...)
* l'application est exposée sur internet
* l'application est accessible via un nom de domaine ou un sous domaine du domaine de la boite à outils

_**Les Avantages**_
* l'application est accessible partout
* le hardware est résilient (meilleure solution pour cela)
* inclut souvent un système de sauvegarde efficace

_**Les Inconvénients**_
* la publication sur Internet rend la sécurisation très importante (avec des contrôles et des mises à jour réguliers)
* couteux (hébergement + domaine)

_Remarque_ : je peux héberger temporairement l'application sur mon propre VPS (chez Infomaniak, cloud souverain Suisse sans aucune dépendance GAFAM) ce qui supprime l'inconvénient coût

### Scénario 2 - hébergement sur le NAS LBAO

* l'application est hébergée sur un serveur Web sur le NAS, à côté de l'instance Nextcloud
* l'application est exposée sur internet
* l'application est accessible via le nom de domaine dynamique lbao.zapto.org

_**Les Avantages**_
* pas de frais

_**Les Inconvénients**_
* la pire solution en terme de fiabilité hardware en l'état (positionnement du NAS en pleine poussière,...)
* la sécurisation est encore plus complexe que pour la solution 1 (car entièrement de notre ressort)
* l'IP n'est pas fixe et impose un DynDNS

### Scénario 3 - hébergement au CBE

* l'application **n'est visible que sur le réseau du CBE**, elle n'est pas publié sur Internet
* l'application est accessible de tout ordi ou téléphone connecté en filaire ou en WiFi
* pas besoin de nom de domaine, des adresse IP suffisent, et la complexité de l'accès peut être masque derrière des alias ou des accès via QRCode

_**Les Avantages**_
* pas de frais, utilisation de matériel recyclé
* si tant est qu'il existe une armoire informatique au CBE, la solution peut facilement être sécurisée en terme de hardware (éventuellement onduleur en cours de réparation par Jacques a LBAO)
* aucun risque en terme de cybersécurité
* mutualisation des uages (serveur PXE)
* sauvegardes croisées faciles à mettre en oeuvre sur le NAS LBAO

_**Les Inconvénients**_
* pas disponible en dehors du CBE (ce qui en soit est aussi un avantage...) : si jamais on en vient à étendre l'atelier ailleurs (LBAO ?) il faudra trouver une solution (réplication de base en temps réel, ...)

_Remarque_ : clairement la meilleure solution si elle est possible


## Les sauvegardes

* Dans le scénario 1 les provider VPS proposent souvent dans leur offre de base une solution de snapshot => très rapide, très sécurisé. On peut compléter ça par un backup sur le NAS LBAO. Bilan : facile à mettre en oeuvre, niveau de sécurisation très satisfaisant
* Le scénario 2 est là aussi le plus faible **à l'heure actuelle** : il faut trouver une solution pour externaliser les données ! 
* Sur le scénario 3 le NAS LBAO peut servir comme tiers externe, offrant une sécurisation très satisfaisante, d'autant que le risque de corruption suite à attaque est nul.

Seule la base est à sauvegardée, le code est automatiquement sauvegardé via le repo GitHub.
