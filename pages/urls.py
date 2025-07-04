from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('a-propos/', views.a_propos, name='a_propos'),
    path('contact/', views.contact, name='contact'),
    path('livraison/', views.livraison, name='livraison'),
    path('faq/', views.faq, name='faq'),
    path('avis/', views.tous_les_avis, name='tous_les_avis'),
]