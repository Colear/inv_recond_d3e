# 🔄 Workflow de gestion du matériel

Ce document décrit le cycle de vie complet d'un ordinateur au sein de l'association, depuis sa récupération jusqu'à son don ou son recyclage. Ce processus est tracé numériquement dans notre application de gestion de stock.

<br/>

## 1. Vue d'ensemble

Le workflow est conçu pour maximiser le taux de réemploi tout en assurant une qualité de service optimale pour les bénéficiaires. Il intègre une gestion flexible des pièces détachées (cannibalisation).

Ce workflow est [visible dans Mermaid](https://mermaid.live/edit#pako:eNp1VD9v00AU_yqnG1AipSFO6rj1gFRSUBEgoqYTSYbL-cU5Yd-553NoSTIwMDBAB1gQSHRBalhZkBj9TfIF4CPwzm6ghDay4rvT7897zz97RrkKgPp0HKnnfMK0IUf7A0nw1zO4q1T2tBbTfAmk26lWydbWHXJPGg3Q__X53RdcE2YMSAMkwEuwUKrUCD4sNUqoZc3v5kuZL6cqApJokAEBSaxhCHOyjzzUe__G6nGV6fRatfLfggvFHsumEDKN0JFWmYgiJUutDeBBj9wmR1olZCogOyFzcgj8lEcshP7qw4-f38_-Hgz_MxGSxEykREiu4iQCMyd7Zcv91dm3jQkkIr_gkF6rcot01gKHkDBs-OO59UYFnS8TppkRSmKpHSXHIvyn6UvHQqxbelgSz5J8iXdIS80NcB3R94VkEcR4QA56Vzq_qm6phfQDmRoWRWUhj4TEYT15OCddDaa_-vQKF_lXQ_JzEigpQQ836PlrPgG-0U1ZLs5QHmfMlsW1MOI4gxuKsWaFGrahxSgrZEZFesaCCya0TYz1xwm-fVks8-Vwg9zVahTlFzE-FRyTwqRgtDHRgZgWw7jBvNC9THlQqeDwSJARC4Rqdd3tJW8NW_NpjYZaBNQ3OoMajUFjbnBLZxYxoGaCzgPq4zJg-tmADuQCOQmTT5WK1zRMcjih_phFKe6yJGAGbI40i_-c2vcHdEdl0lDfaXpOoUL9GT2x-1Z9Z9dzWs0dr-W2XKddo6fU33K2G_W26267bXe7udve8dxFjb4onJ2647XwZNdrIqnhNVAQAmGUflx-HXiRSLr4DSjJdBk)

<br/>

## 2. Détail des Étapes

| Étape | Statut dans l'outil | Description & Actions Clés | Issues Possibles |
| :--- | :--- | :--- | :--- |
| **1. Réception** | `ENTREE`<br>*(En attente de diagnostic)* | **Logistique :** Pesée, étiquetage (QR Code), saisie de la provenance (Déchetterie, Don, Partenariat).<br>**Objectif :** Tracer l'entrée du matériel dans le stock. | ➡️ Prise en charge par un bénévole. |
| **2. Analyse** | `DIAGNOSTIC`<br>*(En cours de diagnostic)* | **Hardware :** Test CPU (Score PassMark), vérification RAM, Disques, Alimentation, WiFi.<br>**Sécurité :** Identification des disques contenant des données à effacer.<br>**Assignation :** Le bénévole qui commence le diagnostic devient "responsable" du dossier. | ✅ **Sain & Complet** → Vers *Réparation*.<br>⏳ **Sain mais Incomplet** → Vers *Attente Pièces*.<br>❌ **HS / Trop vieux** (CPU < 800) → Vers *Recyclage*. |
| **3. Optimisation** | `ATTENTE_PIECES`<br>*(En attente de pièces)* | **Stockage :** Le PC est physiquement rangé dans une zone dédiée.<br>**Stratégie :** On attend de récupérer des composants (RAM, Disques, Alimentations) sur d'autres PC envoyés au recyclage ou en stock dormant. | 🔧 **Pièces reçues** → Vers *Réparation*.<br>❌ **Pièces introuvables / Trop vieux** → Vers *Recyclage*. |
| **4. Réparation** | `REPARATION`<br>*(En réparation / Config)* | **Technique :** Remplacement des pièces défectueuses.<br>**Logiciel :** Installation de la distribution Linux, drivers, suite bureautique (OnlyOffice), navigateur (Firefox), codecs multimédia.<br>**Contrôle :** Vérification du bon fonctionnement global. | ✅ **Conforme** → Vers *Prêt à donner*.<br>❌ **Échec technique** → Vers *Recyclage*. |
| **5. Validation** | `PRET_A_DON`<br>*(Prêt à donner)* | **Qualité :** Le PC est fonctionnel, propre et prêt à être remis.<br>**Stock Sortie :** Il est placé dans la zone de stockage "Sortie". | 🎁 **Attribution** → Vers *Donné*.<br>⚠️ **Problème découvert** → Retour en *Réparation* ou *Recyclage*. |
| **6. Sortie (Don)** | `DONNE`<br>*(Donné)* | **Social :** Remise au bénéficiaire, souvent accompagnée d'une formation de prise en main.<br>**Administratif :** Signature de la fiche de don, liaison avec le bénéficiaire dans l'outil. | **Fin du cycle** (Impact Social). |
| **Sortie (Recyclage)** | `RECYCLAGE`<br>*(Envoyé au recyclage)* | **Écologie :** Envoi en filière spécialisée DEEE (Déchets d'Équipements Électriques et Électroniques).<br>**Poids :** Le poids de sortie est enregistré pour les statistiques de détournement de déchets. | **Fin du cycle** (Impact Écologique). | 

<br/>

## 3. Règles de Gestion Importantes

*   **Traçabilité :** Chaque changement de statut majeur est enregistré dans l'historique des interventions (`Intervention`), avec la date, le bénévole responsable et un commentaire.
*   **Assignation :** Un PC en cours de diagnostic ou de réparation est "verrouillé" par un bénévole pour éviter les doublons de travail.
*   **Flexibilité :** Un PC peut être "relâché" après le diagnostic pour qu'un spécialiste (ex: expert Linux) prenne le relais sans avoir refait le diagnostic hardware.
*   **Critère de performance :** Tout ordinateur avec un score CPU PassMark < 800 est systématiquement orienté vers le recyclage, sauf besoin spécifique.
*   **Sécurité des données :** Tout disque dur présent lors du diagnostic est marqué "Contient données" ou "Sain/Effacé". Aucun disque avec des données n'est réutilisé sans effacement sécurisé préalable.

<br/>

## 4. Modèle de Données Associé

Ce workflow repose sur les modèles Django suivants (simplifié) :
*   `Materiel` : Classe parente (Statut, Inventaire, Provenance, Poids).
*   `Ordinateur` : Détails techniques (CPU, RAM, Linux, etc.).
*   `DisqueDur` : Gestion indépendante des stockages (Numéro d'inventaire disque, État).
*   `Intervention` : Journal d'audit des actions.
*   `Beneficiaire` : Informations sur les receveurs de dons.

<br/>

---
*Document mis à jour le : 29/03/2026*
*Version de l'application : 0.1*
