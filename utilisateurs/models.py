from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from PIL import Image
import jwt
from datetime import datetime, timedelta
import os


def upload_to_profile(instance, filename):
    """Fonction pour définir le chemin d'upload des photos de profil"""
    ext = filename.split('.')[-1]
    filename = f'profile_{instance.utilisateur.id}.{ext}'
    return os.path.join('profiles/', filename)


def upload_to_avis_photos(instance, filename):
    """Fonction pour définir le chemin d'upload des photos d'avis"""
    ext = filename.split('.')[-1]
    filename = f'avis_{instance.avis.id}_{instance.id}.{ext}'
    return os.path.join('avis_photos/', filename)


class Profil(models.Model):
    utilisateur = models.OneToOneField(User, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    ville = models.CharField(max_length=100, blank=True)
    pays = models.CharField(max_length=100, default='Mali')
    email_verifie = models.BooleanField(default=False)

    # Photo de profil obligatoire pour les avis
    photo_profil = models.ImageField(
        upload_to=upload_to_profile,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        help_text="Photo de profil (JPG/PNG, max 5MB)"
    )

    # Informations pour les avis
    date_mariage = models.DateField(null=True, blank=True, verbose_name="Date de votre mariage")
    autoriser_nom_public = models.BooleanField(
        default=False,
        verbose_name="Autoriser l'affichage de mon nom complet dans les avis"
    )
    affichage_anonyme = models.BooleanField(
        default=False,
        verbose_name="Afficher mes avis de manière anonyme"
    )

    # Champs pour la suppression de compte
    suppression_demandee = models.BooleanField(default=False)
    date_demande_suppression = models.DateTimeField(null=True, blank=True)
    token_suppression = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Profil'
        verbose_name_plural = 'Profils'

    def __str__(self):
        return f"Profil de {self.utilisateur.username}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Redimensionner la photo de profil
        if self.photo_profil:
            img = Image.open(self.photo_profil.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.photo_profil.path)

    def get_nom_affichage(self):
        """Retourne le nom à afficher selon les préférences"""
        if self.affichage_anonyme:
            return "Client anonyme"
        elif self.autoriser_nom_public:
            nom_complet = f"{self.utilisateur.first_name} {self.utilisateur.last_name}".strip()
            return nom_complet if nom_complet else self.utilisateur.username
        else:
            prenom = self.utilisateur.first_name or self.utilisateur.username
            nom_initial = self.utilisateur.last_name[0] + "." if self.utilisateur.last_name else ""
            return f"{prenom} {nom_initial}".strip()

    def peut_laisser_avis(self):
        """Vérifie si l'utilisateur peut laisser un avis"""
        # Doit avoir une photo de profil et une date de mariage
        return bool(self.photo_profil and self.date_mariage)

    def generer_token_verification(self):
        """Générer un token JWT pour la vérification d'email"""
        token = jwt.encode({
            'user_id': self.utilisateur.id,
            'exp': datetime.utcnow() + timedelta(days=7)
        }, settings.SECRET_KEY, algorithm='HS256')
        return token

    def generer_token_suppression(self):
        """Générer un token JWT pour la suppression de compte"""
        token = jwt.encode({
            'user_id': self.utilisateur.id,
            'action': 'delete_account',
            'exp': datetime.utcnow() + timedelta(days=30)
        }, settings.SECRET_KEY, algorithm='HS256')
        return token

    def demander_suppression_compte(self):
        """Initier la demande de suppression de compte"""
        self.suppression_demandee = True
        self.date_demande_suppression = timezone.now()
        self.token_suppression = self.generer_token_suppression()
        self.save()

        # Envoyer l'email de confirmation
        self.envoyer_email_suppression_demandee()

    def annuler_suppression_compte(self):
        """Annuler la demande de suppression de compte"""
        self.suppression_demandee = False
        self.date_demande_suppression = None
        self.token_suppression = ''
        self.save()

        # Envoyer l'email de confirmation d'annulation
        self.envoyer_email_suppression_annulee()

    def peut_etre_supprime(self):
        """Vérifier si le compte peut être supprimé (après 30 jours)"""
        if not self.suppression_demandee or not self.date_demande_suppression:
            return False

        date_limite = self.date_demande_suppression + timedelta(days=30)
        return timezone.now() >= date_limite

    def jours_restants_suppression(self):
        """Calculer le nombre de jours restants avant suppression"""
        if not self.suppression_demandee or not self.date_demande_suppression:
            return None

        date_limite = self.date_demande_suppression + timedelta(days=30)
        jours_restants = (date_limite - timezone.now()).days
        return max(0, jours_restants)

    def envoyer_email_bienvenue(self):
        """Envoyer l'email de bienvenue"""
        context = {
            'user': self.utilisateur,
        }

        html_message = render_to_string('utilisateurs/emails/bienvenue.html', context)

        try:
            send_mail(
                'Bienvenue chez Furu Minanw - Votre compte a été créé',
                'Bienvenue sur Furu Minanw',
                settings.DEFAULT_FROM_EMAIL,
                [self.utilisateur.email],
                html_message=html_message,
                fail_silently=False
            )
            print(f"Email de bienvenue envoyé à {self.utilisateur.email}")
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email de bienvenue: {e}")

    def envoyer_email_suppression_demandee(self):
        """Envoyer l'email de confirmation de demande de suppression"""
        context = {
            'user': self.utilisateur,
            'date_suppression': self.date_demande_suppression + timedelta(days=30),
            'jours_restants': 30,
            'annulation_url': f"https://www.furuminanw.com/compte/annuler-suppression/{self.token_suppression}/",
            'nom_prenom': f"{self.utilisateur.first_name} {self.utilisateur.last_name}".strip() or self.utilisateur.username
        }

        html_message = render_to_string('utilisateurs/emails/suppression_demandee.html', context)

        try:
            send_mail(
                'Demande de suppression de compte - Furu Minanw',
                'Votre demande de suppression de compte a été enregistrée',
                settings.DEFAULT_FROM_EMAIL,
                [self.utilisateur.email],
                html_message=html_message,
                fail_silently=False
            )
            print(f"Email de suppression demandée envoyé à {self.utilisateur.email}")
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email de suppression: {e}")

    def envoyer_email_suppression_annulee(self):
        """Envoyer l'email de confirmation d'annulation de suppression"""
        context = {
            'user': self.utilisateur,
            'nom_prenom': f"{self.utilisateur.first_name} {self.utilisateur.last_name}".strip() or self.utilisateur.username
        }

        html_message = render_to_string('utilisateurs/emails/suppression_annulee.html', context)

        try:
            send_mail(
                'Suppression de compte annulée - Furu Minanw',
                'Votre demande de suppression de compte a été annulée',
                settings.DEFAULT_FROM_EMAIL,
                [self.utilisateur.email],
                html_message=html_message,
                fail_silently=False
            )
            print(f"Email de suppression annulée envoyé à {self.utilisateur.email}")
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email d'annulation: {e}")

    def envoyer_rappel_suppression(self, jours_restants):
        """Envoyer un rappel avant suppression définitive"""
        context = {
            'user': self.utilisateur,
            'jours_restants': jours_restants,
            'date_suppression': self.date_demande_suppression + timedelta(days=30),
            'annulation_url': f"https://www.furuminanw.com/compte/annuler-suppression/{self.token_suppression}/",
            'nom_prenom': f"{self.utilisateur.first_name} {self.utilisateur.last_name}".strip() or self.utilisateur.username
        }

        html_message = render_to_string('utilisateurs/emails/rappel_suppression.html', context)

        try:
            send_mail(
                f'Rappel: Suppression de compte dans {jours_restants} jours - Furu Minanw',
                f'Votre compte sera supprimé dans {jours_restants} jours',
                settings.DEFAULT_FROM_EMAIL,
                [self.utilisateur.email],
                html_message=html_message,
                fail_silently=False
            )
            print(f"Rappel de suppression envoyé à {self.utilisateur.email}")
        except Exception as e:
            print(f"Erreur lors de l'envoi du rappel de suppression: {e}")


class AvisClient(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente de modération'),
        ('approuve', 'Approuvé'),
        ('rejete', 'Rejeté'),
    ]

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avis_donnes')
    note = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Note (sur 5)"
    )
    titre = models.CharField(max_length=100, verbose_name="Titre de votre avis")
    contenu = models.TextField(
        max_length=500,
        verbose_name="Votre expérience",
        help_text="Partagez votre expérience (100-500 caractères)"
    )
    date_mariage = models.DateField(verbose_name="Date de votre mariage")

    # Modération
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    afficher_accueil = models.BooleanField(default=False, verbose_name="Afficher sur la page d'accueil")
    commentaire_moderation = models.TextField(blank=True, verbose_name="Commentaire de modération")

    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_moderation = models.DateTimeField(null=True, blank=True)
    moderateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='avis_moderes'
    )

    class Meta:
        verbose_name = 'Avis client'
        verbose_name_plural = 'Avis clients'
        ordering = ['-date_creation']

    def __str__(self):
        return f"Avis de {self.client.username} - {self.note}/5"

    def clean(self):
        from django.core.exceptions import ValidationError
        if len(self.contenu) < 100:
            raise ValidationError({'contenu': 'L\'avis doit contenir au moins 100 caractères.'})

    def save(self, *args, **kwargs):
        # Mettre à jour la date de modération si le statut change
        if self.pk:
            old_avis = AvisClient.objects.get(pk=self.pk)
            if old_avis.statut != self.statut:
                self.date_moderation = timezone.now()

        super().save(*args, **kwargs)

        # Envoyer notification à l'admin pour nouvel avis
        if not self.pk or self.statut == 'en_attente':
            self.notifier_admin_nouvel_avis()

    def notifier_admin_nouvel_avis(self):
        """Notifier l'administrateur d'un nouvel avis"""
        try:
            context = {
                'avis': self,
                'client_nom': self.client.profil.get_nom_affichage(),
                'admin_url': f"https://www.furuminanw.com/admin/utilisateurs/avisclient/{self.id}/change/"
            }

            html_message = render_to_string('utilisateurs/emails/notification_admin_avis.html', context)

            send_mail(
                f'Nouvel avis client à modérer - {self.note}/5 étoiles',
                f'Un nouvel avis de {self.client.username} attend votre modération',
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL],  # Email admin
                html_message=html_message,
                fail_silently=True
            )
            print(f"Notification admin envoyée pour l'avis #{self.id}")
        except Exception as e:
            print(f"Erreur lors de l'envoi de la notification admin: {e}")

    def get_etoiles_html(self):
        """Retourne le HTML pour afficher les étoiles"""
        etoiles_pleines = self.note
        etoiles_vides = 5 - self.note
        html = ""
        for i in range(etoiles_pleines):
            html += '<i class="fas fa-star text-warning"></i>'
        for i in range(etoiles_vides):
            html += '<i class="far fa-star text-warning"></i>'
        return html


class PhotoAvis(models.Model):
    avis = models.ForeignKey(AvisClient, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(
        upload_to=upload_to_avis_photos,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        help_text="Photo de mariage (JPG/PNG, max 5MB)"
    )
    legende = models.CharField(max_length=200, blank=True, verbose_name="Légende (optionnel)")
    ordre = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")

    class Meta:
        verbose_name = 'Photo d\'avis'
        verbose_name_plural = 'Photos d\'avis'
        ordering = ['ordre']

    def __str__(self):
        return f"Photo {self.ordre + 1} - Avis #{self.avis.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Redimensionner l'image
        if self.image:
            img = Image.open(self.image.path)
            if img.height > 800 or img.width > 800:
                output_size = (800, 800)
                img.thumbnail(output_size)
                img.save(self.image.path)


class Connexion(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    location = models.CharField(max_length=255, blank=True)

    def envoyer_notification(self):
        """Envoyer une notification de nouvelle connexion"""
        context = {
            'user': self.utilisateur,
            'connection_date': self.date.strftime('%d/%m/%Y'),
            'connection_time': self.date.strftime('%H:%M'),
            'location': self.location or "Non disponible",
            'device': self.user_agent,
            'security_url': f"https://www.furuminanw.com/compte/securite"
        }

        html_message = render_to_string('utilisateurs/emails/connexion.html', context)

        try:
            send_mail(
                'Nouvelle connexion détectée - Furu Minanw',
                'Une nouvelle connexion a été détectée',
                settings.DEFAULT_FROM_EMAIL,
                [self.utilisateur.email],
                html_message=html_message,
                fail_silently=False
            )
            print(f"Notification de connexion envoyée à {self.utilisateur.email}")
        except Exception as e:
            print(f"Erreur lors de l'envoi de la notification de connexion: {e}")


@receiver(post_save, sender=User)
def creer_profil(sender, instance, created, **kwargs):
    """Créer un profil pour un nouvel utilisateur"""
    if created:
        profil = Profil.objects.create(utilisateur=instance)
        profil.envoyer_email_bienvenue()


@receiver(post_save, sender=User)
def sauvegarder_profil(sender, instance, **kwargs):
    """Sauvegarder le profil d'un utilisateur existant"""
    if hasattr(instance, 'profil'):
        instance.profil.save()