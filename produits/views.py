from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Case, When, Value, IntegerField
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from .models import Pack


def liste_packs(request):
    packs = Pack.objects.filter(actif=True).annotate(
        categorie_order=Case(
            When(categorie='standard', then=Value(1)),
            When(categorie='prestige', then=Value(2)),
            When(categorie='luxe', then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
    ).order_by('categorie_order', 'prix')

    context = {
        'packs': packs,
        'titre': 'Tous nos packs trousseaux'
    }
    return render(request, 'produits/liste_packs.html', context)


def liste_packs_par_categorie(request, categorie):
    packs = Pack.objects.filter(actif=True, categorie=categorie)

    categorie_display = dict(Pack.CATEGORIE_CHOICES).get(categorie, categorie.capitalize())

    context = {
        'packs': packs,
        'categorie': categorie,
        'categorie_display': categorie_display,
        'titre': f'Packs trousseaux {categorie_display}'
    }
    return render(request, 'produits/liste_packs.html', context)


def detail_pack(request, slug):
    pack = get_object_or_404(Pack, slug=slug, actif=True)
    est_favori = pack.favoris.filter(id=request.user.id).exists() if request.user.is_authenticated else False

    context = {
        'pack': pack,
        'est_favori': est_favori,
        'titre': pack.nom
    }
    return render(request, 'produits/detail_pack.html', context)


@login_required
def personnaliser_pack(request, slug):
    """Vue pour personnaliser un pack"""
    pack = get_object_or_404(Pack, slug=slug, actif=True)

    # Pour l'instant, cette vue est un placeholder
    # Elle sera implémentée complètement dans une future mise à jour
    messages.info(request, "La personnalisation des packs sera bientôt disponible.")
    return redirect('produits:detail_pack', slug=pack.slug)


@login_required
def supprimer_personnalisation(request, slug):
    """Vue pour supprimer une personnalisation"""
    pack = get_object_or_404(Pack, slug=slug, actif=True)

    # Pour l'instant, cette vue est un placeholder
    # Elle sera implémentée complètement dans une future mise à jour
    messages.info(request, "La suppression des personnalisations sera bientôt disponible.")
    return redirect('produits:detail_pack', slug=pack.slug)


@login_required
def liste_favoris(request):
    """Vue pour afficher la liste des packs favoris de l'utilisateur"""
    packs = request.user.packs_favoris.filter(actif=True)

    context = {
        'packs': packs,
        'titre': 'Mes favoris'
    }
    return render(request, 'produits/favoris.html', context)


@login_required
def ajouter_favoris(request, pack_id):
    """Vue pour ajouter un pack aux favoris"""
    pack = get_object_or_404(Pack, id=pack_id)

    if request.user not in pack.favoris.all():
        pack.favoris.add(request.user)
        messages.success(request, f"{pack.nom} a été ajouté à vos favoris.")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    return redirect('produits:detail_pack', slug=pack.slug)


@login_required
def supprimer_favoris(request, pack_id):
    """Vue pour supprimer un pack des favoris"""
    pack = get_object_or_404(Pack, id=pack_id)

    if request.user in pack.favoris.all():
        pack.favoris.remove(request.user)
        messages.success(request, f"{pack.nom} a été retiré de vos favoris.")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    return redirect('produits:liste_favoris')