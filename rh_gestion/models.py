from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.utils import timezone
from decimal import Decimal
import os


def upload_to_employee_photos(instance, filename):
    """Fonction pour définir le chemin d'upload des photos d'employés"""
    ext = filename.split('.')[-1]
    filename = f'employee_{instance.id}_{instance.nom}_{instance.prenom}.{ext}'
    return os.path.join('employees/photos/', filename)


def upload_to_justificatifs(instance, filename):
    """Fonction pour définir le chemin d'upload des justificatifs d'arrêt de travail"""
    ext = filename.split('.')[-1]
    filename = f'arret_{instance.employe.id}_{instance.id}.{ext}'
    return os.path.join('employees/justificatifs/', filename)


def upload_to_fiches_paie(instance, filename):
    """Fonction pour définir le chemin d'upload des fiches de paie PDF"""
    ext = filename.split('.')[-1]
    filename = f'fiche_paie_{instance.employe.id}_{instance.mois}_{instance.annee}.{ext}'
    return os.path.join('employees/fiches_paie/', filename)


class Poste(models.Model):
    """Modèle représentant un poste dans l'entreprise"""

    DEPARTEMENTS_CHOICES = [
        ('direction', 'Direction Générale'),
        ('administration', 'Administration Générale'),
        ('comptabilite', 'Comptabilité et Finances'),
        ('it', 'IT / Développement Web'),
        ('commercial', 'Ventes / Commercial'),
        ('marketing', 'Marketing'),
        ('communication', 'Communication'),
        ('service_client', 'Service Client'),
        ('logistique', 'Logistique / Transport'),
        ('services_generaux', 'Services Généraux'),
        ('securite', 'Sécurité'),
    ]

    nom = models.CharField(max_length=100, verbose_name="Nom du poste")
    departement = models.CharField(
        max_length=50,
        choices=DEPARTEMENTS_CHOICES,
        verbose_name="Département"
    )
    description = models.TextField(blank=True, verbose_name="Description du poste")
    date_creation = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True, verbose_name="Poste actif")

    class Meta:
        verbose_name = 'Poste'
        verbose_name_plural = 'Postes'
        ordering = ['departement', 'nom']
        unique_together = ['nom', 'departement']

    def __str__(self):
        return f"{self.nom} - {self.get_departement_display()}"

    def nombre_employes(self):
        """Retourne le nombre d'employés occupant ce poste"""
        return self.employes.filter(statut__in=['actif', 'conge']).count()

    nombre_employes.short_description = 'Nb employés'


class Employe(models.Model):
    """Modèle représentant un employé de l'entreprise"""

    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('conge', 'En congé'),
        ('arret', 'Arrêt de travail'),
        ('suspendu', 'Suspendu'),
        ('demission', 'Démission'),
        ('licencie', 'Licencié'),
        ('retraite', 'Retraité'),
    ]

    # Informations personnelles
    nom = models.CharField(max_length=100, verbose_name="Nom de famille")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    email = models.EmailField(unique=True, verbose_name="Adresse email")
    telephone = models.CharField(max_length=20, verbose_name="Numéro de téléphone")
    date_naissance = models.DateField(verbose_name="Date de naissance")

    # Informations professionnelles
    date_embauche = models.DateField(verbose_name="Date d'embauche")
    poste = models.ForeignKey(
        Poste,
        on_delete=models.PROTECT,
        related_name='employes',
        verbose_name="Poste occupé"
    )
    salaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Salaire mensuel (FCFA)"
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='actif',
        verbose_name="Statut de l'employé"
    )

    # Informations complémentaires
    photo = models.ImageField(
        upload_to=upload_to_employee_photos,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        verbose_name="Photo de l'employé"
    )
    adresse = models.CharField(max_length=255, verbose_name="Adresse")
    ville = models.CharField(max_length=100, default='Bamako', verbose_name="Ville")
    pays = models.CharField(max_length=100, default='Mali', verbose_name="Pays")
    notes = models.TextField(blank=True, verbose_name="Notes et observations")

    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Employé'
        verbose_name_plural = 'Employés'
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.poste.nom}"

    def nom_complet(self):
        """Retourne le nom complet de l'employé"""
        return f"{self.prenom} {self.nom}"

    nom_complet.short_description = 'Nom complet'

    def age(self):
        """Calcule l'âge de l'employé"""
        today = timezone.now().date()
        return today.year - self.date_naissance.year - (
                (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
        )

    age.short_description = 'Âge'

    def anciennete(self):
        """Calcule l'ancienneté en années"""
        today = timezone.now().date()
        return today.year - self.date_embauche.year - (
                (today.month, today.day) < (self.date_embauche.month, self.date_embauche.day)
        )

    anciennete.short_description = 'Ancienneté (années)'

    def conges_en_cours(self):
        """Retourne les congés en cours"""
        return self.conges.filter(
            statut='valide',
            date_debut__lte=timezone.now().date(),
            date_fin__gte=timezone.now().date()
        )

    def est_en_conge(self):
        """Vérifie si l'employé est actuellement en congé"""
        return self.conges_en_cours().exists()

    est_en_conge.boolean = True
    est_en_conge.short_description = 'En congé'

    def arrets_en_cours(self):
        """Retourne les arrêts de travail en cours"""
        return self.arrets_travail.filter(
            statut='valide',
            date_debut__lte=timezone.now().date(),
            date_fin__gte=timezone.now().date()
        )

    def est_en_arret(self):
        """Vérifie si l'employé est actuellement en arrêt de travail"""
        return self.arrets_en_cours().exists()

    est_en_arret.boolean = True
    est_en_arret.short_description = 'En arrêt'


class Conge(models.Model):
    """Modèle représentant une demande de congé"""

    TYPE_CONGE_CHOICES = [
        ('annuel', 'Congé annuel'),
        ('maladie', 'Congé maladie'),
        ('maternite', 'Congé maternité'),
        ('paternite', 'Congé paternité'),
        ('exceptionnel', 'Congé exceptionnel'),
        ('formation', 'Congé formation'),
        ('sans_solde', 'Congé sans solde'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
        ('annule', 'Annulé'),
    ]

    employe = models.ForeignKey(
        Employe,
        on_delete=models.CASCADE,
        related_name='conges',
        verbose_name="Employé"
    )
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    type_conge = models.CharField(
        max_length=20,
        choices=TYPE_CONGE_CHOICES,
        verbose_name="Type de congé"
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente',
        verbose_name="Statut de la demande"
    )
    motif = models.TextField(verbose_name="Motif de la demande")
    date_demande = models.DateTimeField(auto_now_add=True, verbose_name="Date de demande")
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de validation"
    )
    validateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Validé par"
    )
    commentaire_validation = models.TextField(
        blank=True,
        verbose_name="Commentaire de validation"
    )

    class Meta:
        verbose_name = 'Congé'
        verbose_name_plural = 'Congés'
        ordering = ['-date_demande']

    def __str__(self):
        return f"{self.employe.nom_complet()} - {self.get_type_conge_display()} ({self.date_debut} au {self.date_fin})"

    def duree_jours(self):
        """Calcule la durée du congé en jours"""
        return (self.date_fin - self.date_debut).days + 1

    duree_jours.short_description = 'Durée (jours)'

    def clean(self):
        """Validation des données"""
        from django.core.exceptions import ValidationError

        if self.date_fin < self.date_debut:
            raise ValidationError('La date de fin doit être postérieure à la date de début.')

        # Vérifier les chevauchements pour le même employé
        if self.pk:
            chevauchements = Conge.objects.filter(
                employe=self.employe,
                statut='valide'
            ).exclude(pk=self.pk).filter(
                models.Q(date_debut__lte=self.date_fin) &
                models.Q(date_fin__gte=self.date_debut)
            )
        else:
            chevauchements = Conge.objects.filter(
                employe=self.employe,
                statut='valide',
                date_debut__lte=self.date_fin,
                date_fin__gte=self.date_debut
            )

        if chevauchements.exists():
            raise ValidationError('Cette période chevauche avec un congé déjà validé.')


class ArretTravail(models.Model):
    """Modèle représentant un arrêt de travail"""

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
    ]

    employe = models.ForeignKey(
        Employe,
        on_delete=models.CASCADE,
        related_name='arrets_travail',
        verbose_name="Employé"
    )
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    motif = models.TextField(verbose_name="Motif médical")
    justificatif = models.FileField(
        upload_to=upload_to_justificatifs,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        verbose_name="Justificatif médical"
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente',
        verbose_name="Statut"
    )
    date_declaration = models.DateTimeField(auto_now_add=True, verbose_name="Date de déclaration")
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de validation"
    )
    validateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Validé par"
    )

    class Meta:
        verbose_name = 'Arrêt de travail'
        verbose_name_plural = 'Arrêts de travail'
        ordering = ['-date_declaration']

    def __str__(self):
        return f"{self.employe.nom_complet()} - Arrêt du {self.date_debut} au {self.date_fin}"

    def duree_jours(self):
        """Calcule la durée de l'arrêt en jours"""
        return (self.date_fin - self.date_debut).days + 1

    duree_jours.short_description = 'Durée (jours)'

    def clean(self):
        """Validation des données"""
        from django.core.exceptions import ValidationError

        if self.date_fin < self.date_debut:
            raise ValidationError('La date de fin doit être postérieure à la date de début.')


class FicheDePaie(models.Model):
    """Modèle représentant une fiche de paie"""

    MOIS_CHOICES = [
        (1, 'Janvier'), (2, 'Février'), (3, 'Mars'), (4, 'Avril'),
        (5, 'Mai'), (6, 'Juin'), (7, 'Juillet'), (8, 'Août'),
        (9, 'Septembre'), (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre')
    ]

    employe = models.ForeignKey(
        Employe,
        on_delete=models.CASCADE,
        related_name='fiches_paie',
        verbose_name="Employé"
    )
    mois = models.IntegerField(choices=MOIS_CHOICES, verbose_name="Mois")
    annee = models.IntegerField(verbose_name="Année")
    salaire_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Salaire de base (FCFA)"
    )
    primes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Primes et indemnités (FCFA)"
    )
    retenues = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Retenues et cotisations (FCFA)"
    )
    salaire_net = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Salaire net (FCFA)"
    )
    date_emission = models.DateTimeField(auto_now_add=True, verbose_name="Date d'émission")
    pdf = models.FileField(
        upload_to=upload_to_fiches_paie,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        verbose_name="Fiche de paie PDF"
    )

    class Meta:
        verbose_name = 'Fiche de paie'
        verbose_name_plural = 'Fiches de paie'
        ordering = ['-annee', '-mois']
        unique_together = ['employe', 'mois', 'annee']

    def __str__(self):
        return f"{self.employe.nom_complet()} - {self.get_mois_display()} {self.annee}"

    def save(self, *args, **kwargs):
        """Calcul automatique du salaire net"""
        if not self.salaire_net:
            self.salaire_net = self.salaire_base + self.primes - self.retenues
        super().save(*args, **kwargs)

    def periode(self):
        """Retourne la période sous forme de chaîne"""
        return f"{self.get_mois_display()} {self.annee}"

    periode.short_description = 'Période'