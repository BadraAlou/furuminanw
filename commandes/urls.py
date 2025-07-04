from django.urls import path
from . import views

app_name = 'commandes'

urlpatterns = [
    path('panier/', views.voir_panier, name='panier'),
    path('ajouter/<int:pack_id>/', views.ajouter_au_panier, name='ajouter_au_panier'),
    path('modifier/<int:item_id>/', views.modifier_panier, name='modifier_panier'),
    path('supprimer/<int:item_id>/', views.supprimer_du_panier, name='supprimer_du_panier'),
    path('modifier-options/<int:pack_id>/', views.modifier_options_panier, name='modifier_options_panier'),
    path('recapitulatif/', views.recapitulatif_commande, name='recapitulatif'),
    path('commander/', views.commander, name='commander'),
    path('confirmation/<int:commande_id>/', views.confirmation_commande, name='confirmation'),
]