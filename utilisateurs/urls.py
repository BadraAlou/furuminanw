from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'utilisateurs'

urlpatterns = [
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', auth_views.LoginView.as_view(template_name='utilisateurs/connexion.html'), name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('profil/', views.profil, name='profil'),
    path('commandes/', views.historique_commandes, name='historique_commandes'),
    path('commande/<int:commande_id>/', views.detail_commande, name='detail_commande'),

    # URLs pour les avis
    path('avis/', views.mes_avis, name='mes_avis'),
    path('avis/ajouter/', views.ajouter_avis, name='ajouter_avis'),
    path('avis/<int:avis_id>/modifier/', views.modifier_avis, name='modifier_avis'),
    path('avis/<int:avis_id>/supprimer/', views.supprimer_avis, name='supprimer_avis'),

    # URLs pour la suppression de compte
    path('demander-suppression/', views.demander_suppression_compte, name='demander_suppression'),
    path('suppression-en-cours/', views.suppression_en_cours, name='suppression_en_cours'),
    path('annuler-suppression/<str:token>/', views.annuler_suppression_compte, name='annuler_suppression'),
    path('annuler-suppression/', views.annuler_suppression_compte_connecte, name='annuler_suppression_connecte'),

    # URL legacy pour compatibilité
    path('supprimer-compte/', views.supprimer_compte, name='supprimer_compte'),
]