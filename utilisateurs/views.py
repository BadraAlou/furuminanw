from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import Http404
from django.utils import timezone
from django.db import transaction
from .forms import (
    UtilisateurInscriptionForm, UtilisateurUpdateForm, ProfilUpdateForm,
    SuppressionCompteForm, AvisClientForm, PhotoAvisFormSet
)
from .models import Profil, AvisClient
from commandes.models import Commande
import jwt
from django.conf import settings


def inscription(request):
    if request.method == 'POST':
        form = UtilisateurInscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            prenom = form.cleaned_data.get('first_name')
            messages.success(request, f'Compte créé pour {prenom}! Vous pouvez maintenant vous connecter.')
            return redirect('utilisateurs:connexion')
    else:
        form = UtilisateurInscriptionForm()

    context = {
        'form': form,
        'titre': 'Inscription'
    }
    return render(request, 'utilisateurs/inscription.html', context)


def deconnexion(request):
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return render(request, 'utilisateurs/deconnexion.html', {'titre': 'Déconnexion'})


@login_required
def profil(request):
    if request.method == 'POST':
        u_form = UtilisateurUpdateForm(request.POST, instance=request.user)
        p_form = ProfilUpdateForm(request.POST, request.FILES, instance=request.user.profil)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès!')
            return redirect('utilisateurs:profil')
    else:
        u_form = UtilisateurUpdateForm(instance=request.user)
        p_form = ProfilUpdateForm(instance=request.user.profil)

    # Récupérer les avis récents de l'utilisateur
    avis_recents = AvisClient.objects.filter(client=request.user).order_by('-date_creation')[:3]

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'avis_recents': avis_recents,
        'titre': 'Mon Profil Client'
    }

    return render(request, 'utilisateurs/profil.html', context)


@login_required
def historique_commandes(request):
    commandes = Commande.objects.filter(client=request.user).order_by('-date_commande')

    context = {
        'commandes': commandes,
        'titre': 'Historique des commandes'
    }

    return render(request, 'utilisateurs/historique_commandes.html', context)


@login_required
def detail_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id, client=request.user)

    context = {
        'commande': commande,
        'titre': f'Commande #{commande.id}'
    }

    return render(request, 'utilisateurs/detail_commande.html', context)


@login_required
def mes_avis(request):
    """Vue pour afficher tous les avis de l'utilisateur"""
    avis = AvisClient.objects.filter(client=request.user).order_by('-date_creation')

    context = {
        'avis': avis,
        'titre': 'Mes Avis'
    }

    return render(request, 'utilisateurs/mes_avis.html', context)


@login_required
def ajouter_avis(request):
    """Vue pour ajouter un nouvel avis"""
    # Vérifier si l'utilisateur peut laisser un avis
    if not request.user.profil.peut_laisser_avis():
        messages.error(
            request,
            'Vous devez avoir une photo de profil et une date de mariage pour pouvoir laisser un avis. '
            'Veuillez compléter votre profil.'
        )
        return redirect('utilisateurs:profil')

    if request.method == 'POST':
        form = AvisClientForm(request.POST, user=request.user)
        formset = PhotoAvisFormSet(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                avis = form.save(commit=False)
                avis.client = request.user
                avis.save()

                # Sauvegarder les photos
                formset.instance = avis
                photos = formset.save(commit=False)
                for i, photo in enumerate(photos):
                    photo.ordre = i
                    photo.save()

                messages.success(
                    request,
                    'Votre avis a été soumis avec succès ! Il sera publié après modération.'
                )
                return redirect('utilisateurs:mes_avis')
    else:
        form = AvisClientForm(user=request.user)
        formset = PhotoAvisFormSet()

    context = {
        'form': form,
        'formset': formset,
        'titre': 'Partagez votre Expérience'
    }

    return render(request, 'utilisateurs/ajouter_avis.html', context)


@login_required
def modifier_avis(request, avis_id):
    """Vue pour modifier un avis existant"""
    avis = get_object_or_404(AvisClient, id=avis_id, client=request.user)

    # Seuls les avis en attente ou rejetés peuvent être modifiés
    if avis.statut == 'approuve':
        messages.error(request, 'Vous ne pouvez pas modifier un avis déjà approuvé.')
        return redirect('utilisateurs:mes_avis')

    if request.method == 'POST':
        form = AvisClientForm(request.POST, instance=avis, user=request.user)
        formset = PhotoAvisFormSet(request.POST, request.FILES, instance=avis)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                avis = form.save(commit=False)
                avis.statut = 'en_attente'  # Remettre en attente après modification
                avis.save()

                # Sauvegarder les photos
                photos = formset.save(commit=False)
                for i, photo in enumerate(photos):
                    photo.ordre = i
                    photo.save()

                # Supprimer les photos marquées pour suppression
                for photo in formset.deleted_objects:
                    photo.delete()

                messages.success(request, 'Votre avis a été modifié et sera re-soumis pour modération.')
                return redirect('utilisateurs:mes_avis')
    else:
        form = AvisClientForm(instance=avis, user=request.user)
        formset = PhotoAvisFormSet(instance=avis)

    context = {
        'form': form,
        'formset': formset,
        'avis': avis,
        'titre': 'Modifier mon Avis'
    }

    return render(request, 'utilisateurs/modifier_avis.html', context)


@login_required
def supprimer_avis(request, avis_id):
    """Vue pour supprimer un avis"""
    avis = get_object_or_404(AvisClient, id=avis_id, client=request.user)

    if request.method == 'POST':
        avis.delete()
        messages.success(request, 'Votre avis a été supprimé avec succès.')
        return redirect('utilisateurs:mes_avis')

    context = {
        'avis': avis,
        'titre': 'Supprimer mon Avis'
    }

    return render(request, 'utilisateurs/supprimer_avis.html', context)


@login_required
def demander_suppression_compte(request):
    """Vue pour demander la suppression du compte"""
    profil = request.user.profil

    # Vérifier si une demande est déjà en cours
    if profil.suppression_demandee:
        jours_restants = profil.jours_restants_suppression()
        context = {
            'titre': 'Suppression de compte en cours',
            'jours_restants': jours_restants,
            'date_suppression': profil.date_demande_suppression + timezone.timedelta(days=30),
            'token_suppression': profil.token_suppression
        }
        return render(request, 'utilisateurs/suppression_en_cours.html', context)

    if request.method == 'POST':
        form = SuppressionCompteForm(request.user, request.POST)
        if form.is_valid():
            # Initier la demande de suppression
            profil.demander_suppression_compte()

            messages.success(
                request,
                'Votre demande de suppression a été enregistrée. Vous avez 30 jours pour annuler cette demande.'
            )
            return redirect('utilisateurs:suppression_en_cours')
    else:
        form = SuppressionCompteForm(request.user)

    context = {
        'form': form,
        'titre': 'Supprimer mon compte'
    }
    return render(request, 'utilisateurs/demander_suppression.html', context)


@login_required
def suppression_en_cours(request):
    """Vue pour afficher l'état de la suppression en cours"""
    profil = request.user.profil

    if not profil.suppression_demandee:
        return redirect('utilisateurs:profil')

    jours_restants = profil.jours_restants_suppression()

    context = {
        'titre': 'Suppression de compte en cours',
        'jours_restants': jours_restants,
        'date_suppression': profil.date_demande_suppression + timezone.timedelta(days=30),
        'token_suppression': profil.token_suppression
    }
    return render(request, 'utilisateurs/suppression_en_cours.html', context)


def annuler_suppression_compte(request, token):
    """Vue pour annuler la suppression du compte via token"""
    try:
        # Décoder le token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('user_id')
        action = payload.get('action')

        if action != 'delete_account':
            raise jwt.InvalidTokenError()

        # Récupérer le profil
        profil = get_object_or_404(Profil, utilisateur_id=user_id, token_suppression=token)

        if not profil.suppression_demandee:
            messages.info(request, 'Aucune demande de suppression en cours pour ce compte.')
            return redirect('pages:accueil')

        # Annuler la suppression
        profil.annuler_suppression_compte()

        messages.success(
            request,
            'Votre demande de suppression de compte a été annulée avec succès. Votre compte reste actif.'
        )

        # Si l'utilisateur est connecté, le rediriger vers son profil
        if request.user.is_authenticated and request.user.id == user_id:
            return redirect('utilisateurs:profil')
        else:
            return redirect('utilisateurs:connexion')

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        messages.error(request, 'Le lien d\'annulation est invalide ou a expiré.')
        return redirect('pages:accueil')


@login_required
def annuler_suppression_compte_connecte(request):
    """Vue pour annuler la suppression quand l'utilisateur est connecté"""
    profil = request.user.profil

    if not profil.suppression_demandee:
        messages.info(request, 'Aucune demande de suppression en cours.')
        return redirect('utilisateurs:profil')

    if request.method == 'POST':
        profil.annuler_suppression_compte()
        messages.success(request, 'Votre demande de suppression a été annulée avec succès.')
        return redirect('utilisateurs:profil')

    context = {
        'titre': 'Annuler la suppression de compte'
    }
    return render(request, 'utilisateurs/annuler_suppression.html', context)


# Vue legacy pour compatibilité (à supprimer plus tard)
@login_required
def supprimer_compte(request):
    """Redirection vers la nouvelle vue de demande de suppression"""
    return redirect('utilisateurs:demander_suppression')