from decimal import Decimal
from django.views.generic import CreateView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from ..forms import NouveauMaterielForm, DiagnosticRepaForm, DisqueFormSet
from ..mixins import AuthBenevoleMixin
from ..decorators import benevole_actif_required
from ..models import Ordinateur, Ecran, Peripherique, Materiel, Marque, Benevole, Intervention



"""====== NouveauMateriel =====================================================
    Formulaire de saisie rapide d'un nouveau matériel.
    Contient également une vue Ajax pour ajouter une marque à la volée.
============================================================================"""

class NouveauMaterielView(AuthBenevoleMixin, CreateView): 

    model = Materiel # On utilise le parent pour le formulaire, mais on sauvera dans l'enfant
    form_class = NouveauMaterielForm
    template_name = 'inventaire/nouveau_materiel.html'
    success_url = '/inventaire' # Redirige vers la liste après succès

    # permissions nécessaires pour afficher la vue
    permission_required = 'inventaire.add_materiel'

    def form_valid(self, form):
        type_materiel = form.cleaned_data['type_materiel']
        categorie_pc = form.cleaned_data.get('categorie_pc')
        categorie_periph = form.cleaned_data.get('categorie_periph')
        
        # 1. Création de l'instance en mémoire (pas encore en base)
        instance = form.save(commit=False)
        instance.date_entree = timezone.now().date()
        
        # 2. Génération du numéro
        instance.numero_inventaire = instance.generer_numero_inventaire()
        
        # 3. Sauvegarde initiale (Crée la ligne avec un ID)
        # On essaie de sauver normalement d'abord
        instance.save()
        
        # 4. Création de l'enfant (Nécessite que le parent ait un ID)
        if type_materiel == 'PC':
            if not categorie_pc:
                return self.form_invalid(form)
            Ordinateur.objects.create(materiel_ptr=instance, categorie=categorie_pc)
        elif type_materiel == 'ECRAN':
            Ecran.objects.create(materiel_ptr=instance)
        elif type_materiel == 'PERIPH':
            if not categorie_periph:
                return self.form_invalid(form)
            Peripherique.objects.create(materiel_ptr=instance, type_periph=categorie_periph)
            
        # 5. CORRECTION GLOBALE (Le "Silver Bullet")
        # On force l'écriture de TOUS les champs critiques en une seule requête SQL
        # Cela contourne tous les problèmes de commit=False, editable, etc.
        Materiel.objects.filter(pk=instance.pk).update(
            numero_inventaire=instance.numero_inventaire,
            poids_entree_kg=instance.poids_entree_kg,
            provenance=instance.provenance,
            marque_id=instance.marque_id, # Attention : utiliser l'ID pour une ForeignKey
            modele=instance.modele,
            type_materiel=instance.type_materiel,
            date_entree=instance.date_entree,
            statut=instance.statut,
            benevole_en_charge_id=instance.benevole_en_charge_id,
        )

        return redirect(self.success_url)



# --- Vue AJAX pour permettre l'ajout de marque à la volée ---

def ajax_create_marque(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Non authentifié'})
    
    try:
        if not request.user.profile_benevole.actif and not request.user.is_superuser:
            return JsonResponse({'success': False, 'error': 'Compte inactif'})
    except Benevole.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil introuvable'})
    
    if request.method == 'POST':
        nom = request.POST.get('nom')
        if nom:
            marque, created = Marque.objects.get_or_create(nom=nom)
            return JsonResponse({'success': True, 'id': marque.id, 'nom': marque.nom})
    return JsonResponse({'success': False, 'error': 'Nom requis'})



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

    if request.method == 'POST':
        action = request.POST.get('action')
        form = DiagnosticRepaForm(request.POST, instance=ordinateur, action=action)
        formset = DisqueFormSet(request.POST, instance=ordinateur)
        
        if form.is_valid() and formset.is_valid():
            action = request.POST.get('action')
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

            if action == 'start_diag':
                # Transition : ENTREE -> DIAGNOSTIC
                if materiel.statut == 'ENTREE':
                    instance.statut = 'DIAGNOSTIC'
                    instance.benevole_en_charge = benevole
                    instance.date_prise_en_charge = timezone.now()
                    type_action = 'DIAG'
                    commentaire_intervention = "Début du diagnostic. Prise en charge du dossier."
                    messages.success(request, "🔍 Diagnostic commencé. Vous êtes maintenant assigné à ce dossier.")
                else:
                    messages.warning(request, "Le statut ne permet pas de démarrer le diagnostic.")

            elif action == 'save_exit':
                # Sauvegarde brouillon : Reste en DIAGNOSTIC (ou passe de ENTREE à DIAGNOSTIC si premier sauvegarde)
                if materiel.statut == 'ENTREE':
                    instance.statut = 'DIAGNOSTIC'
                    instance.benevole_en_charge = benevole
                    instance.date_prise_en_charge = timezone.now()
                    type_action = 'DIAG'
                    commentaire_intervention = "Début du diagnostic (sauvegarde intermédiaire)."
                else:
                    type_action = 'NOTE'
                    commentaire_intervention = "Sauvegarde intermédiaire du diagnostic."
                
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
                # redirect_to_inventory = False (Reste sur page, ou True si vous préférez)

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

    else:
        # GET
        form = DiagnosticRepaForm(instance=ordinateur)
        formset = DisqueFormSet(instance=ordinateur)

    context = {
        'materiel': materiel,
        'ordinateur': ordinateur,
        'form': form,
        'formset': formset,
    }
    return render(request, 'inventaire/modifier_materiel.html', context)

