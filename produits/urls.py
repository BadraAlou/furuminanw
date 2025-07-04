from django.urls import path
from . import views

app_name = 'produits'

urlpatterns = [
    path('', views.liste_packs, name='liste_packs'),
    path('categorie/<str:categorie>/', views.liste_packs_par_categorie, name='liste_packs_par_categorie'),
    path('favoris/', views.liste_favoris, name='liste_favoris'),
    path('favoris/ajouter/<int:pack_id>/', views.ajouter_favoris, name='ajouter_favoris'),
    path('favoris/supprimer/<int:pack_id>/', views.supprimer_favoris, name='supprimer_favoris'),
    path('<slug:slug>/', views.detail_pack, name='detail_pack'),
    path('<slug:slug>/personnaliser/', views.personnaliser_pack, name='personnaliser_pack'),
    path('<slug:slug>/supprimer-personnalisation/', views.supprimer_personnalisation, name='supprimer_personnalisation'),
]