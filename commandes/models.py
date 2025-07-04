from django.db import models
from django.contrib.auth.models import User
from produits.models import Pack, Option
from decimal import Decimal
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


class Commande(models.Model):
    STATUT_CHOICES = (
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('en_preparation', 'En préparation'),
        ('expediee', 'Expédiée'),
        ('livree', 'Livrée'),
        ('annulee', 'Annulée'),
    )

    PAIEMENT_CHOICES = (
        ('especes', 'Espèces'),
        ('orange_money', 'Orange Money'),
        ('wave', 'Wave'),
    )

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='commandes')
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
    adresse_livraison = models.CharField(max_length=250)
    ville = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=20)
    pays = models.CharField(max_length=100, default='Mali')
    date_commande = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    methode_paiement = models.CharField(max_length=20, choices=PAIEMENT_CHOICES, default='especes')
    notes = models.TextField(blank=True)
    notes_admin = models.TextField(blank=True, verbose_name="Notes administrateur")
    archivee = models.BooleanField(default=False)
    numero_suivi = models.CharField(max_length=100, blank=True)
    date_livraison_estimee = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-date_commande']
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'

    def __str__(self):
        return f'Commande {self.id}'

    def total(self):
        """Calculer le total de la commande"""
        total = Decimal('0.00')
        for item in self.elements.all():
            total += item.prix
        return total

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None if is_new else Commande.objects.get(pk=self.pk).statut

        super().save(*args, **kwargs)

        if is_new:
            # Attendre que tous les éléments soient sauvegardés avant d'envoyer l'email
            pass
        elif old_status != self.statut:
            self.envoyer_email_suivi()

    def envoyer_email_confirmation(self):
        """Envoyer l'email de confirmation de commande"""
        # Récupérer tous les éléments de la commande
        elements = self.elements.all()

        # Calculer le total manuellement pour s'assurer qu'il est correct
        total_commande = Decimal('0.00')
        for element in elements:
            total_commande += element.prix

        # Debug: afficher les informations
        print(f"Commande #{self.id} - Nombre d'éléments: {elements.count()}")
        print(f"Total calculé: {total_commande}")

        context = {
            'commande': self,
            'elements': elements,
            'total': total_commande,
            'nom_prenom': f"{self.client.first_name} {self.client.last_name}".strip() or self.client.username
        }

        html_message = render_to_string('commandes/emails/confirmation_commande.html', context)

        try:
            send_mail(
                f'Confirmation de votre commande #{self.id} - Furu Minanw',
                f'Votre commande #{self.id} a été confirmée',
                settings.DEFAULT_FROM_EMAIL,
                [self.email],
                html_message=html_message,
                fail_silently=False
            )
            print(f"Email de confirmation envoyé pour la commande #{self.id}")
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email de confirmation: {e}")

    def envoyer_email_suivi(self):
        """Envoyer l'email de suivi de commande"""
        elements = self.elements.all()
        total_commande = self.total()

        context = {
            'commande': self,
            'elements': elements,
            'total': total_commande,
            'nom_prenom': f"{self.client.first_name} {self.client.last_name}".strip() or self.client.username
        }

        html_message = render_to_string('commandes/emails/notification_statut.html', context)

        try:
            send_mail(
                f'Mise à jour de votre commande #{self.id} - Furu Minanw',
                f'Le statut de votre commande #{self.id} a été mis à jour',
                settings.DEFAULT_FROM_EMAIL,
                [self.email],
                html_message=html_message,
                fail_silently=False
            )
            print(f"Email de suivi envoyé pour la commande #{self.id}")
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email de suivi: {e}")


class ElementCommande(models.Model):
    commande = models.ForeignKey(Commande, related_name='elements', on_delete=models.CASCADE)
    pack = models.ForeignKey(Pack, related_name='elements_commande', on_delete=models.CASCADE)
    options_selectionnees = models.ManyToManyField(Option, blank=True)
    quantite = models.PositiveIntegerField(default=1)
    prix = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.quantite} x {self.pack.nom}'

    def save(self, *args, **kwargs):
        if not self.prix:
            # Calculer le prix de base
            self.prix = self.pack.prix * Decimal(self.quantite)

        super().save(*args, **kwargs)

        # Après la sauvegarde, ajouter le prix des options
        if self.pk and not kwargs.get('update_fields'):
            prix_options = Decimal('0.00')
            for option_pack in self.pack.options.all():
                if self.options_selectionnees.filter(id=option_pack.option.id).exists():
                    prix_options += option_pack.prix_supplement

            if prix_options > 0:
                self.prix += prix_options * Decimal(self.quantite)
                super().save(update_fields=['prix'])

        print(f"ElementCommande sauvegardé: {self.pack.nom} - Prix: {self.prix} FCFA")


class PrecisionPersonnalisation(models.Model):
    """Précisions pour les options de personnalisation d'un élément de commande"""
    element_commande = models.ForeignKey(
        ElementCommande,
        related_name='precisions_personnalisation',
        on_delete=models.CASCADE
    )
    option = models.ForeignKey(Option, on_delete=models.CASCADE)

    # Champs pour différents types de précisions
    texte_a_graver = models.TextField(
        blank=True,
        verbose_name="Texte à graver",
        help_text="Précisez le texte exact à graver"
    )
    date_a_graver = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Date à graver",
        help_text="Format: JJ/MM/AAAA"
    )
    mot_doux = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Mot doux personnalisé",
        help_text="Maximum 100 caractères"
    )
    laisser_choisir_mot_doux = models.BooleanField(
        default=False,
        verbose_name="Laissez-nous choisir le mot doux"
    )
    couleur_preference = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Couleur préférée",
        help_text="Précisez votre couleur préférée"
    )
    taille_preference = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Taille préférée",
        help_text="Précisez la taille souhaitée"
    )
    instructions_speciales = models.TextField(
        blank=True,
        verbose_name="Instructions spéciales",
        help_text="Toute autre précision importante"
    )

    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Précision de personnalisation'
        verbose_name_plural = 'Précisions de personnalisation'
        unique_together = ('element_commande', 'option')

    def __str__(self):
        return f"Précisions pour {self.option.nom} - Commande #{self.element_commande.commande.id}"

    def get_resume_precisions(self):
        """Retourne un résumé des précisions saisies"""
        precisions = []

        if self.texte_a_graver:
            precisions.append(f"Gravure: {self.texte_a_graver}")

        if self.date_a_graver:
            precisions.append(f"Date: {self.date_a_graver}")

        if self.mot_doux:
            precisions.append(f"Mot doux: {self.mot_doux}")
        elif self.laisser_choisir_mot_doux:
            precisions.append("Mot doux: Laissez-nous choisir")

        if self.couleur_preference:
            precisions.append(f"Couleur: {self.couleur_preference}")

        if self.taille_preference:
            precisions.append(f"Taille: {self.taille_preference}")

        if self.instructions_speciales:
            precisions.append(f"Instructions: {self.instructions_speciales}")

        return " | ".join(precisions) if precisions else "Aucune précision"