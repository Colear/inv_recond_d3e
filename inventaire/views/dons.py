from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from ..decorators import benevole_actif_required
from ..forms import BeneficiaireForm
from ..models import Materiel, Beneficiaire, Intervention



"""====== faire_un_don ========================================================
    Vue pour donner une configuration.
============================================================================"""

@login_required
@benevole_actif_required
@permission_required('inventaire.can_validate_don', raise_exception=True)
def faire_un_don(request):

    # 1. Gestion de la session Bénéficiaire
    benef_id = request.session.get('don_beneficiaire_id')
    beneficiaire = None
    
    if benef_id:
        try:
            beneficiaire = Beneficiaire.objects.get(pk=benef_id)
        except Beneficiaire.DoesNotExist:
            print("Bénéficiaire en session inexistant, nettoyage.")
            request.session['don_beneficiaire_id'] = None
            beneficiaire = None

    benef_form = BeneficiaireForm()

    # 2. Traitement POST : Recherche/Création Bénéficiaire
    if request.method == 'POST' and 'action_benef' in request.POST:
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        if nom and prenom:
            benefs = Beneficiaire.objects.filter(nom__iexact=nom, prenom__iexact=prenom)
            if not benefs.exists():
                # Essai plus large
                benefs = Beneficiaire.objects.filter(nom__icontains=nom, prenom__icontains=prenom)
            
            if benefs.exists():
                beneficiaire = benefs.first()
                request.session['don_beneficiaire_id'] = beneficiaire.id
                messages.success(request, f"Bénéficiaire trouvé : {beneficiaire}")
            else:
                beneficiaire = Beneficiaire.objects.create(nom=nom.upper(), prenom=prenom)
                request.session['don_beneficiaire_id'] = beneficiaire.id
                messages.success(request, f"Créé : {beneficiaire}")
        return redirect('faire_un_don')

    # 3. Gestion du Panier (Session)
    panier_don = request.session.get('panier_don', [])

    # Ajout au panier
    if request.method == 'POST' and 'action_ajout_materiel' in request.POST:
        inv_number = request.POST.get('numero_inventaire')
        if inv_number:
            try:
                materiel = Materiel.objects.get(numero_inventaire=inv_number)
                if materiel.statut != 'PRET_A_DON':
                    messages.error(request, f"Statut incorrect : {materiel.statut}")
                elif inv_number not in panier_don:
                    panier_don.append(inv_number)
                    request.session['panier_don'] = panier_don
                    request.session.modified = True # Force la sauvegarde de la session
                    messages.success(request, f"Ajouté : {inv_number}")
                else:
                    messages.warning(request, "Déjà dans le panier")
            except Materiel.DoesNotExist:
                messages.error(request, "Matériel introuvable")
        return redirect('faire_un_don')

    # Récupération des objets pour l'affichage
    materiels_a_donner = Materiel.objects.filter(numero_inventaire__in=panier_don) if panier_don else []

    # 4. Traitement POST : Validation Finale
    if request.method == 'POST' and 'action_valider_don' in request.POST:
        
        # Vérif Bénéficiaire
        current_benef_id = request.session.get('don_beneficiaire_id')
        
        if not current_benef_id:
            messages.error(request, "ERREUR CRITIQUE : Aucun bénéficiaire en session. Veuillez le re-sélectionner.")
            return redirect('faire_un_don')
        
        try:
            beneficiaire = Beneficiaire.objects.get(pk=current_benef_id)
        except Beneficiaire.DoesNotExist:
            messages.error(request, "ERREUR : Bénéficiaire introuvable en base.")
            request.session['don_beneficiaire_id'] = None
            return redirect('faire_un_don')

        # Vérif Panier
        if not panier_don:
            messages.error(request, "ERREUR : Le panier est vide.")
            return redirect('faire_un_don')
                   
        ids_to_pdf = []
        for inv in panier_don:
            try:
                m = Materiel.objects.get(numero_inventaire=inv)
                m.statut = 'DONNE'
                m.beneficiaire = beneficiaire
                m.date_sortie = timezone.now()
                if not m.poids_sortie_kg:
                    m.poids_sortie_kg = m.poids_entree_kg # Correction typo potentielle ici si variable mal nommée
                    m.poids_sortie_kg = m.poids_entree_kg
                m.save()
                
                Intervention.objects.create(
                    materiel=m, benevole=request.user, type_action='SORTIE',
                    commentaire=f"Donné à {beneficiaire}"
                )
                ids_to_pdf.append(str(m.id))
            except Exception as e:
                messages.error(request, f"Erreur sur {inv}: {str(e)}")

        # Nettoyage Panier
        request.session['panier_don'] = []
        request.session.modified = True
        
        # Construction URL PDF
        if ids_to_pdf:
            ids_str = ",".join(ids_to_pdf)
            return redirect('generer_fiche_don_pdf', beneficiaire_id=beneficiaire.id, materiel_ids_str=ids_str)
        else:
            messages.error(request, "Aucun matériel n'a pu être validé.")
            return redirect('faire_un_don')

    context = {
        'beneficiaire': beneficiaire,
        'benef_form': benef_form,
        'panier_don': materiels_a_donner,
        'nb_materiels': len(panier_don),
    }
    return render(request, 'inventaire/faire_un_don.html', context)



"""====== generer_fiche_don_pdf ===============================================
    Génération de la fiche de don pour impression.
============================================================================"""

@login_required
@benevole_actif_required
@permission_required('inventaire.can_validate_don', raise_exception=True)
def generer_fiche_don_pdf(request, beneficiaire_id, materiel_ids_str):

    """
    Génère la fiche de don PDF.
    materiel_ids_str : chaîne de caractères "1,2,3" contenant les IDs des matériels donnés.
    """
    try:
        beneficiaire = Beneficiaire.objects.get(pk=beneficiaire_id)
        ids = [int(x) for x in materiel_ids_str.split(',')]
        materiels = Materiel.objects.filter(id__in=ids).select_related('marque')
    except (Beneficiaire.DoesNotExist, ValueError):
        return HttpResponse("Erreur : Données invalides.", status=400)

    # Création du PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Fiche_Don_{beneficiaire.nom}_{beneficiaire.prenom}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()

    # Styles personnalisés
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=20, textColor=colors.darkblue, spaceAfter=20, alignment=TA_CENTER)
    sub_title_style = ParagraphStyle('SubTitle', parent=styles['Heading2'], fontSize=14, textColor=colors.grey, spaceAfter=10)
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.spaceAfter = 6

    # En-tête
    elements.append(Paragraph("FICHE DE DON DE MATÉRIEL INFORMATIQUE", title_style))
    elements.append(Paragraph("Atelier SICTOM / LBAO / CBE", sub_title_style))
    elements.append(Spacer(1, 0.5*cm))

    # Infos Bénéficiaire
    elements.append(Paragraph("<b>Bénéficiaire :</b>", normal_style))
    benef_info = f"""
    <b>Nom :</b> {beneficiaire.nom.upper()} {beneficiaire.prenom}<br/>
    <b>Date du don :</b> {beneficiaire.materiaux_recus.first().date_sortie.strftime('%d/%m/%Y') if beneficiaire.materiaux_recus.exists() else '...'}<br/>
    """
    # Note: Pour la date, on prend celle du premier matériel du lot, c'est approximatif mais suffit pour la démo.
    # Idéalement, on passerait la date en paramètre.
    
    elements.append(Paragraph(benef_info, normal_style))
    elements.append(Spacer(1, 0.5*cm))

    # Tableau du Matériel
    elements.append(Paragraph("<b>Matériel donné :</b>", normal_style))
    
    data = [['N° Inv.', 'Type', 'Marque', 'Modèle', 'Observations']]
    
    for m in materiels:
        # Récupération des observations (rapport diagnostic ou pièces changées)
        # Pour un PC, on peut aller chercher l'objet enfant
        obs = ""
        if hasattr(m, 'ordinateur') and m.ordinateur:
            obs = f"Linux: {m.ordinateur.linux_distro or 'Non'}"
            if m.ordinateur.ram_go:
                obs += f", RAM: {m.ordinateur.ram_go}Go"
        elif hasattr(m, 'ecran') and m.ecran:
             if m.ecran.diagonale_pouces:
                 obs = f"{m.ecran.diagonale_pouces} pouces"
        
        data.append([
            m.numero_inventaire,
            m.get_type_materiel_display(),
            m.marque.nom if m.marque else '-',
            m.modele or '-',
            obs
        ])

    t = Table(data, colWidths=[2.5*cm, 2.5*cm, 3*cm, 4*cm, 5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 1.5*cm))

    # Clause de responsabilité / Signature
    clause_text = """
    <b>Engagement du bénéficiaire :</b><br/><br/>
    Je soussigné(e), déclare recevoir le matériel listé ci-dessus en bon état de fonctionnement.
    Je m'engage à l'utiliser dans le respect de la législation en vigueur et à ne pas le revendre.
    Je comprends que ce don est fait à titre gratuit et solidaire.
    <br/><br/>
    Fait pour servir et valoir ce que de droit.
    """
    elements.append(Paragraph(clause_text, normal_style))
    elements.append(Spacer(1, 2*cm))

    # Zone de signature
    sig_data = [
        ["Signature du Responsable Association", "Signature du Bénéficiaire"],
        ["", ""],
        ["", ""],
        ["", ""],
        ["(Lu et approuvé)", "(Lu et approuvé)"]
    ]
    t_sig = Table(sig_data, colWidths=[7*cm, 7*cm])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 4), (-1, 4), 9),
        ('TOPPADDING', (0, 0), (-1, 0), 20),
        ('BOTTOMPADDING', (0, 4), (-1, 4), 10),
    ]))
    # On dessine une ligne pour signer (astuce avec GRID partiel ou dessin, ici on laisse blanc pour signer à la main)
    elements.append(t_sig)

    doc.build(elements)
    return response

