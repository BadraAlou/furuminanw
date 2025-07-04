from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from produits.models import Pack
from utilisateurs.models import AvisClient
from .forms import ContactForm


def accueil(request):
    # Récupérer un pack de chaque catégorie pour mettre en avant
    packs_featured = {}
    categories = ['standard', 'prestige', 'luxe']

    for cat in categories:
        pack = Pack.objects.filter(categorie=cat, actif=True).first()
        if pack:
            packs_featured[cat] = pack

    # Récupérer seulement 3 avis clients les plus percutants pour l'accueil
    avis_clients = AvisClient.objects.filter(
        statut='approuve',
        afficher_accueil=True
    ).select_related('client__profil').prefetch_related('photos').order_by('-date_creation')[:3]

    context = {
        'packs_featured': packs_featured,
        'avis_clients': avis_clients,
        'titre': 'Accueil - Furu Minanw'
    }
    return render(request, 'pages/accueil.html', context)


def tous_les_avis(request):
    """Page dédiée pour afficher tous les avis clients approuvés"""
    avis_clients = AvisClient.objects.filter(
        statut='approuve'
    ).select_related('client__profil').prefetch_related('photos').order_by('-date_creation')

    context = {
        'avis_clients': avis_clients,
        'titre': 'Avis de nos clientes'
    }
    return render(request, 'pages/tous_les_avis.html', context)


def a_propos(request):
    context = {
        'titre': 'À propos de nous'
    }
    return render(request, 'pages/a_propos.html', context)


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Envoyer l'email de réponse automatique
            context = {
                'nom': form.cleaned_data['nom'],
                'email': form.cleaned_data['email'],
                'sujet': form.cleaned_data['sujet'],
                'message': form.cleaned_data['message']
            }

            # Email de confirmation pour le client
            html_message = render_to_string('emails/contact_reponse.html', context)

            try:
                send_mail(
                    f'Merci pour votre message - Furu Minanw',
                    'Nous avons bien reçu votre message',
                    settings.DEFAULT_FROM_EMAIL,
                    [form.cleaned_data['email']],
                    html_message=html_message,
                    fail_silently=False
                )

                # Email pour l'équipe (optionnel)
                send_mail(
                    f'Nouveau message de contact: {form.cleaned_data["sujet"]}',
                    f'Nouveau message de {form.cleaned_data["nom"]} ({form.cleaned_data["email"]}):\n\n{form.cleaned_data["message"]}',
                    settings.DEFAULT_FROM_EMAIL,
                    ['furuminanw@gmail.com'],
                    fail_silently=True
                )

                messages.success(request,
                                 'Votre message a été envoyé avec succès! Nous vous répondrons dans les plus brefs délais.')
                print(f"Email de contact envoyé à {form.cleaned_data['email']}")
            except Exception as e:
                print(f"Erreur lors de l'envoi de l'email de contact: {e}")
                messages.success(request,
                                 'Votre message a été envoyé avec succès! Nous vous répondrons dans les plus brefs délais.')

            return redirect('pages:contact')
    else:
        form = ContactForm()

    context = {
        'form': form,
        'titre': 'Contactez-nous'
    }
    return render(request, 'pages/contact.html', context)


def livraison(request):
    context = {
        'titre': 'Politique de livraison'
    }
    return render(request, 'pages/livraison.html', context)


def faq(request):
    context = {
        'titre': 'Questions fréquentes'
    }
    return render(request, 'pages/faq.html', context)