from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from .panier import Panier
from produits.models import Pack, Option
from .forms import CommandeForm, creer_formset_precisions
from .models import Commande, ElementCommande, PrecisionPersonnalisation


def voir_panier(request):
    panier = Panier(request)

    context = {
        'panier': panier,
        'titre': 'Votre panier'
    }
    return render(request, 'commandes/panier.html', context)


def ajouter_au_panier(request, pack_id):
    panier = Panier(request)
    pack = get_object_or_404(Pack, id=pack_id)

    if request.method == 'POST':
        quantite = int(request.POST.get('quantite', 1))

        # Récupérer les options sélectionnées
        options_ids = []
        for key, value in request.POST.items():
            if key.startswith('option_'):
                option_id = int(key.split('_')[1])
                options_ids.append(option_id)

        panier.ajouter(pack_id=pack.id, quantite=quantite, options=options_ids)
        messages.success(request, f"{pack.nom} a été ajouté à votre panier.")

        return redirect('commandes:panier')

    return redirect('produits:detail_pack', slug=pack.slug)


def modifier_panier(request, item_id):
    panier = Panier(request)

    if request.method == 'POST':
        quantite = int(request.POST.get('quantite', 1))
        panier.modifier_quantite(pack_id=item_id, quantite=quantite)
        messages.success(request, "Panier mis à jour.")

    return redirect('commandes:panier')


def modifier_options_panier(request, pack_id):
    """Vue pour modifier les options d'un produit dans le panier"""
    panier = Panier(request)
    pack = get_object_or_404(Pack, id=pack_id)

    # Vérifier que le produit est dans le panier
    if str(pack_id) not in panier.panier:
        messages.error(request, "Ce produit n'est pas dans votre panier.")
        return redirect('commandes:panier')

    if request.method == 'POST':
        # Récupérer les nouvelles options sélectionnées
        options_ids = []
        for key, value in request.POST.items():
            if key.startswith('option_'):
                option_id = int(key.split('_')[1])
                options_ids.append(option_id)

        # Mettre à jour les options dans le panier
        panier.panier[str(pack_id)]['options'] = options_ids
        panier.sauvegarder()

        messages.success(request, f"Les options pour {pack.nom} ont été mises à jour.")
        return redirect('commandes:panier')

    # Récupérer les options actuellement sélectionnées
    options_actuelles = panier.panier[str(pack_id)].get('options', [])

    context = {
        'pack': pack,
        'options_actuelles': options_actuelles,
        'titre': f'Modifier les options - {pack.nom}'
    }

    return render(request, 'commandes/modifier_options.html', context)


def supprimer_du_panier(request, item_id):
    panier = Panier(request)
    pack = get_object_or_404(Pack, id=item_id)

    panier.supprimer(pack_id=pack.id)
    messages.success(request, f"{pack.nom} a été supprimé de votre panier.")

    return redirect('commandes:panier')


@login_required
def recapitulatif_commande(request):
    """Vue pour afficher le récapitulatif détaillé avant la commande"""
    panier = Panier(request)

    # Vérifier si le panier est vide
    if panier.get_nombre_produits() == 0:
        messages.warning(request, "Votre panier est vide.")
        return redirect('commandes:panier')

    # Préparer les données pour les précisions de personnalisation
    produits_avec_options = []
    for item in panier.get_produits():
        if 'options_details' in item and item['options_details']:
            produits_avec_options.append({
                'pack': item['pack'],
                'options': item['options_details'],
                'quantite': item['quantite'],
                'prix_total': item['prix_total']
            })

    # Calculer les totaux
    sous_total = panier.get_total()
    frais_livraison = 0  # Livraison gratuite
    total_final = sous_total + frais_livraison

    context = {
        'panier': panier,
        'produits_avec_options': produits_avec_options,
        'sous_total': sous_total,
        'frais_livraison': frais_livraison,
        'total_final': total_final,
        'titre': 'Récapitulatif de votre commande'
    }

    return render(request, 'commandes/recapitulatif.html', context)


@login_required
def commander(request):
    panier = Panier(request)

    # Vérifier si le panier est vide
    if panier.get_nombre_produits() == 0:
        messages.warning(request, "Votre panier est vide.")
        return redirect('commandes:panier')

    # Préparer les données pour les précisions de personnalisation
    produits_avec_options = []
    for item in panier.get_produits():
        if 'options_details' in item and item['options_details']:
            produits_avec_options.append({
                'pack': item['pack'],
                'options': item['options_details'],
                'quantite': item['quantite']
            })

    if request.method == 'POST':
        form = CommandeForm(request.POST)

        # Traiter les précisions de personnalisation
        precisions_data = {}
        for key, value in request.POST.items():
            if key.startswith('precision_'):
                # Format: precision_{pack_id}_{option_id}_{champ}
                parts = key.split('_')
                if len(parts) >= 4:
                    pack_id = parts[1]
                    option_id = parts[2]
                    champ = '_'.join(parts[3:])

                    if pack_id not in precisions_data:
                        precisions_data[pack_id] = {}
                    if option_id not in precisions_data[pack_id]:
                        precisions_data[pack_id][option_id] = {}

                    precisions_data[pack_id][option_id][champ] = value

        if form.is_valid():
            with transaction.atomic():
                commande = form.save(commit=False)
                commande.client = request.user
                commande.save()

                # Ajouter les éléments du panier à la commande
                for item in panier.get_produits():
                    element = ElementCommande(
                        commande=commande,
                        pack=item['pack'],
                        quantite=item['quantite'],
                        prix=item['prix_total']
                    )
                    element.save()

                    # Ajouter les options sélectionnées si elles existent
                    if 'options_details' in item:
                        element.options_selectionnees.set(item['options_details'])

                        # Sauvegarder les précisions de personnalisation
                        pack_id_str = str(item['pack'].id)
                        if pack_id_str in precisions_data:
                            for option in item['options_details']:
                                option_id_str = str(option.id)
                                if option_id_str in precisions_data[pack_id_str]:
                                    precision_data = precisions_data[pack_id_str][option_id_str]

                                    # Créer la précision si au moins un champ est rempli
                                    if any(precision_data.values()):
                                        precision = PrecisionPersonnalisation(
                                            element_commande=element,
                                            option=option
                                        )

                                        # Assigner les valeurs des champs
                                        for champ, valeur in precision_data.items():
                                            if hasattr(precision, champ) and valeur:
                                                if champ == 'laisser_choisir_mot_doux':
                                                    setattr(precision, champ, valeur == 'on')
                                                else:
                                                    setattr(precision, champ, valeur)

                                        precision.save()

                        # Recalculer le prix avec les options
                        element.save()

                # Vider le panier
                panier.vider()

                # Envoyer l'email de confirmation après que tous les éléments soient sauvegardés
                commande.envoyer_email_confirmation()
                print(f"Commande #{commande.id} créée avec succès")

                # Message de succès professionnel
                messages.success(
                    request,
                    f'🎉 Félicitations ! Votre commande #{commande.id} a été passée avec succès. '
                    f'Un email de confirmation a été envoyé à {commande.email}. '
                    f'Notre équipe va traiter votre commande dans les plus brefs délais.'
                )

                return redirect('commandes:confirmation', commande_id=commande.id)
    else:
        # Pré-remplir le formulaire avec les informations de l'utilisateur
        initial_data = {
            'email': request.user.email,
        }
        form = CommandeForm(initial=initial_data)

    context = {
        'form': form,
        'panier': panier,
        'produits_avec_options': produits_avec_options,
        'titre': 'Finaliser votre commande'
    }

    return render(request, 'commandes/commander.html', context)


@login_required
def confirmation_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id, client=request.user)

    context = {
        'commande': commande,
        'titre': 'Confirmation de commande'
    }

    return render(request, 'commandes/confirmation.html', context)