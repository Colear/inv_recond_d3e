from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from ..forms import DiagnosticRepaForm, DisqueFormSet
from ..decorators import benevole_actif_required
from ..models import Materiel, Marque, Intervention



"""====== modifier_materiel ===================================================
    Vue commune au diagnostic et à la réparation / configuration d'ordis.
============================================================================"""

@login_required
@benevole_actif_required
@permission_required('inventaire.change_materiel', raise_exception=True)
def modifier_materiel(request, pk):

    materiel = get_object_or_404(Materiel, pk=pk)
    
    # Sécurité : Vérifier que c'est un ordinateur
    if not hasattr(materiel, 'ordinateur') or materiel.ordinateur is None:
        messages.error(request, "Ce matériel n'est pas un ordinateur.")
        return redirect('inventaire')
        
    ordinateur = materiel.ordinateur
    benevole = request.user
    redirect_to_inventory = False

    # === Traitement du POST ==========
    # Soumission du formulaire rempli
    if request.method == 'POST':

        action = request.POST.get('action')

        # 1. TRAITEMENT SPÉCIAL : DÉMARRAGE DU DIAGNOSTIC
        if action == 'start_diag':
            # On ne valide PAS le formulaire ici. On change juste le statut.
            materiel.statut = 'DIAGNOSTIC'
            materiel.benevole_en_charge = request.user
            materiel.date_prise_en_charge = timezone.now()
            materiel.save()
            
            Intervention.objects.create(
                materiel=materiel, benevole=request.user, type_action='DIAG',
                commentaire="Début du diagnostic."
            )
            messages.success(request, "Diagnostic commencé. Vous pouvez maintenant saisir les informations.")
            return redirect('modifier_materiel', pk=materiel.pk) # Redirection pour recharger la page en mode DIAGNOSTIC


        # 2. CAS NORMAL (TOUS LES AUTRES ETATS)
        form = DiagnosticRepaForm(request.POST, instance=ordinateur, action=action)
        formset = DisqueFormSet(request.POST, instance=ordinateur)
        
        if form.is_valid() and formset.is_valid():
            instance = form.save(commit=False)
            
            # 1. Gestion Marque/Modèle (Champs manuels du template)
            nom_marque = request.POST.get('input_marque', '').strip()
            nom_modele = request.POST.get('input_modele', '').strip()
            if nom_marque:
                marque_obj, _ = Marque.objects.get_or_create(nom=nom_marque)
                instance.materiel_ptr.marque = marque_obj
            if nom_modele:
                instance.materiel_ptr.modele = nom_modele
            instance.materiel_ptr.save()

            # 2. Logique des Actions
            commentaire_intervention = ""
            type_action = "NOTE"

            # --- SAVE_EXIT : sauvegarde intermédiaire du travail, on ne change pas le statut
            if action == 'save_exit':
                commentaire_intervention = "Sauvegarde intermédiaire du travail."
                messages.info(request, "💾 Travail enregistré. Vous pouvez revenir plus tard.")
                redirect_to_inventory = True # RETOUR LISTE

            elif action == 'validate_diag_release':
                # Validation + Libération : DIAGNOSTIC -> REPARATION (Sans bénévole)
                instance.statut = 'REPARATION'
                instance.benevole_en_charge = None # On libère
                type_action = 'TRANSFERT'
                commentaire_intervention = "Diagnostic validé. Dossier relâché pour la suite (spécialiste)."
                messages.success(request, "👋 Diagnostic validé et dossier relâché. Retour à l'inventaire.")
                redirect_to_inventory = True # RETOUR LISTE

            elif action == 'validate_diag_repa':
                # Validation + Continuité : DIAGNOSTIC -> REPARATION (Avec bénévole)
                if not instance.benevole_en_charge:
                    instance.benevole_en_charge = benevole
                    instance.date_prise_en_charge = timezone.now()
                instance.statut = 'REPARATION'
                type_action = 'DIAG'
                commentaire_intervention = "Diagnostic validé. Passage en phase de réparation/configuration."
                messages.success(request, "✅ Diagnostic validé. Vous pouvez maintenant configurer le logiciel.")
                # redirect_to_inventory = False (Reste sur page)

            elif action == 'recycle_now':
                # Recyclage immédiat : -> RECYCLAGE
                instance.statut = 'RECYCLAGE'
                if not instance.benevole_en_charge:
                    instance.benevole_en_charge = benevole
                type_action = 'SORTIE'
                raison = instance.rapport_diagnostic[:100] or "Non réparable (Décision diagnostic)"
                commentaire_intervention = f"Décision de recyclage : {raison}"
                messages.warning(request, "♻️ Matériel envoyé au recyclage.")
                redirect_to_inventory = True # RETOUR LISTE

            elif action == 'wait_parts':
                # Transition : -> ATTENTE_PIECES
                instance.statut = 'ATTENTE_PIECES'
                
                # LIBÉRATION DU BÉNÉVOLE
                # On note qui a fait la mise en attente dans l'historique, mais on vide le champ "en charge"
                ancien_benevole = instance.benevole_en_charge
                instance.benevole_en_charge = None 
                # On ne touche pas à date_prise_en_charge pour garder la trace de la première prise en charge
                
                raison = instance.rapport_diagnostic[:100] or "En attente de composants"
                Intervention.objects.create(
                    materiel=materiel,
                    benevole=benevole, # Celui qui clique maintenant
                    type_action='NOTE',
                    commentaire=f"Mise en attente de pièces par {benevole.get_full_name()}. (Dossier libéré). Raison : {raison}"
                )
                messages.info(request, "⏳ Matériel placé en attente de pièces. Le dossier a été libéré pour un futur spécialiste.")
                redirect_to_inventory = True

            elif action == 'reactivate_keep':
                # Option 1 : Réactiver et Garder (Je fais tout : Hardware + Software)
                if materiel.statut == 'ATTENTE_PIECES':
                    instance.statut = 'REPARATION'
                    instance.benevole_en_charge = benevole # Je me l'attribue
                    instance.date_prise_en_charge = timezone.now()
                    
                    Intervention.objects.create(
                        materiel=materiel,
                        benevole=benevole,
                        type_action='TRANSFERT',
                        commentaire="Réactivation et prise en charge complète (Hardware + Software)."
                    )
                    messages.success(request, "✅ Matériel réactivé. Vous restez en charge du dossier pour la configuration.")
                    # redirect_to_inventory = False (Reste sur la page)

            elif action == 'reactivate_release':
                # Option 2 : Réactiver et Relâcher (Je fais le Hardware, je laisse le Software à un autre)
                if materiel.statut == 'ATTENTE_PIECES':
                    instance.statut = 'REPARATION'
                    instance.benevole_en_charge = None # Je libère le dossier pour la suite
                    
                    Intervention.objects.create(
                        materiel=materiel,
                        benevole=benevole,
                        type_action='TRANSFERT',
                        commentaire=f"Réactivation Hardware par {benevole.get_full_name()}. Pièces installées. Dossier relâché pour configuration Linux."
                    )
                    messages.success(request, "🔧 Matériel réactivé (Hardware fait). Le dossier est retourné à l'inventaire pour un spécialiste Linux.")
                    redirect_to_inventory = True # Retour liste

            elif action == 'reactivate_repa':
                # Transition : ATTENTE_PIECES -> REPARATION
                if materiel.statut == 'ATTENTE_PIECES':
                    instance.statut = 'REPARATION'
                    
                    # On attribue le dossier au bénévole actuel s'il n'y en a pas, 
                    # ou on le laisse tel quel si c'est le même qui reprend son travail.
                    if not instance.benevole_en_charge:
                        instance.benevole_en_charge = benevole
                        instance.date_prise_en_charge = timezone.now()
                    
                    Intervention.objects.create(
                        materiel=materiel,
                        benevole=benevole,
                        type_action='TRANSFERT', # ou 'REPA'
                        commentaire="Réactivation du dossier : pièces manquantes installées. Passage en réparation."
                    )
                    messages.success(request, "✅ Matériel réactivé. Vous pouvez maintenant procéder à la configuration.")
                    # redirect_to_inventory = False (On reste sur la page pour travailler)
                else:
                    messages.warning(request, "Ce statut ne permet pas la réactivation.")

            elif action == 'validate_repa':
                # Fin de réparation : REPARATION -> PRET_A_DON
                instance.statut = 'PRET_A_DON'
                type_action = 'REPA'
                commentaire_intervention = "Réparation et configuration validées. Prêt à donner."
                messages.success(request, "🎉 Matériel prêt à être donné !")
                redirect_to_inventory = True

            # 3. Sauvegarde Finale
            if instance.cout_reparation is None or instance.cout_reparation == '':
                instance.cout_reparation = Decimal('0.00')
            
            instance.save()
            formset.save()

            # 4. Création de l'historique (Intervention)
            if commentaire_intervention:
                Intervention.objects.create(
                    materiel=materiel,
                    benevole=benevole,
                    type_action=type_action,
                    commentaire=commentaire_intervention
                )

            # 5. Redirection
            if redirect_to_inventory:
                return redirect('inventaire')
            else:
                return redirect('modifier_materiel', pk=pk)

        else:
            # Debug erreurs
            if not form.is_valid():
                print(f"Erreurs Form : {form.errors}")
            if not formset.is_valid():
                print(f"Erreurs Formset : {formset.errors}")
            messages.error(request, "Une erreur est survenue dans le formulaire. Vérifiez les champs.")

    # === Traitement du GET ==========
    # Affichage du formulaire vide
    else:
        form = DiagnosticRepaForm(instance=ordinateur)
        formset = DisqueFormSet(instance=ordinateur)


    # --- Gestion des boutons ----------
    # Les boutons d'action sont différents selon l'étape de workflow
    # Pour que le template n'ait pas à gérer de logique métier (si tel étape alors tel bouton...) 
    # on créé ici un liste avec l'état affiché ou non de chaque bouton
    statut = materiel.statut
    display_flags = {
        'show_start_button': statut == 'ENTREE',
        'show_diag_actions': statut == 'DIAGNOSTIC',
        'show_wait_actions': statut == 'ATTENTE_PIECES',
        'show_repair_section': statut in ['REPARATION', 'PRET_A_DON'],
        'is_locked': statut in ['DONNE', 'RECYCLAGE', 'PERDU'],
        'show_recycle_button': statut in ['DIAGNOSTIC', 'REPARATION'], 
    }
    display_flags = {
        'show_start_button': statut == 'ENTREE',
        'show_diag_actions': statut == 'DIAGNOSTIC',
        'show_wait_actions': statut == 'ATTENTE_PIECES',
        'show_repair_section': statut in ['REPARATION', 'PRET_A_DON'],
        'show_validate_final_button': statut == 'REPARATION',
        'is_locked': statut in ['DONNE', 'RECYCLAGE', 'PERDU'],
        'show_recycle_button': statut in ['DIAGNOSTIC', 'REPARATION'],
        
        # La section Hardware est toujours visible (sauf si verrouillé), mais repliée en mode Réparation
        'hardware_collapsed': statut in ['REPARATION', 'PRET_A_DON'], 
        
        # La section Software est invisible en mode Diagnostic/Entrée/Attente, visible sinon
        'software_visible': statut in ['REPARATION', 'PRET_A_DON'],
    }


    # On peut aussi préparer les textes dynamiques si besoin
    status_message = ""
    if statut == 'ENTREE':
        status_message = "En attente de prise en charge."
    elif statut == 'DIAGNOSTIC':
        status_message = f"En cours de diagnostic par {materiel.benevole_en_charge}." if materiel.benevole_en_charge else "En cours de diagnostic."

    
    # --- Passage du contexte et affichage de la view
    context = {
        'materiel': materiel,
        'ordinateur': ordinateur,
        'form': form,
        'formset': formset,
        'display': display_flags,
        'status_message': status_message,
    }
    return render(request, 'inventaire/modifier_materiel.html', context)

