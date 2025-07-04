from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth.models import User


class Pack(models.Model):
    CATEGORIE_CHOICES = (
        ('standard', 'Standard'),
        ('prestige', 'Prestige'),
        ('luxe', 'Luxe'),
    )

    nom = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES)
    image_principale = models.ImageField(upload_to='packs/', blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    favoris = models.ManyToManyField(User, related_name='packs_favoris', blank=True)

    class Meta:
        ordering = [
            models.Case(
                models.When(categorie='standard', then=models.Value(1)),
                models.When(categorie='prestige', then=models.Value(2)),
                models.When(categorie='luxe', then=models.Value(3)),
                default=models.Value(4),
            ),
            'prix'
        ]
        verbose_name = 'Pack'
        verbose_name_plural = 'Packs'

    def __str__(self):
        return self.nom

    def get_absolute_url(self):
        return reverse('produits:detail_pack', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)


class ImagePack(models.Model):
    pack = models.ForeignKey(Pack, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='packs/')
    alt_text = models.CharField(max_length=200, blank=True)
    est_principale = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Image du pack'
        verbose_name_plural = 'Images des packs'

    def __str__(self):
        return f"Image de {self.pack.nom}"


class Option(models.Model):
    CATEGORIE_CHOICES = (
        ('couleur', 'Couleur'),
        ('matiere', 'Matière'),
        ('taille', 'Taille'),
        ('style', 'Style'),
        ('autre', 'Autre'),
    )

    nom = models.CharField(max_length=100)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Option'
        verbose_name_plural = 'Options'

    def __str__(self):
        return self.nom


class OptionDePack(models.Model):
    pack = models.ForeignKey(Pack, related_name='options', on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
    prix_supplement = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Option de pack'
        verbose_name_plural = 'Options de pack'
        unique_together = ('pack', 'option')

    def __str__(self):
        return f"{self.option.nom} pour {self.pack.nom}"