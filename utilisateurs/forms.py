from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import Profil, AvisClient, PhotoAvis


class UtilisateurInscriptionForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label='Prénom')
    last_name = forms.CharField(max_length=30, required=True, label='Nom')
    email = forms.EmailField(required=True, label='Adresse email')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


class UtilisateurUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class ProfilUpdateForm(forms.ModelForm):
    class Meta:
        model = Profil
        fields = [
            'telephone', 'adresse', 'ville', 'pays',
            'photo_profil', 'date_mariage',
            'autoriser_nom_public', 'affichage_anonyme'
        ]
        widgets = {
            'date_mariage': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'photo_profil': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'autoriser_nom_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'affichage_anonyme': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_photo_profil(self):
        photo = self.cleaned_data.get('photo_profil')
        if photo:
            # Vérifier la taille du fichier (5MB max)
            if photo.size > 5 * 1024 * 1024:
                raise ValidationError('La photo ne doit pas dépasser 5MB.')

            # Vérifier le format
            if not photo.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise ValidationError('Seuls les formats JPG et PNG sont acceptés.')

        return photo


class AvisClientForm(forms.ModelForm):
    class Meta:
        model = AvisClient
        fields = ['note', 'titre', 'contenu', 'date_mariage']
        widgets = {
            'note': forms.Select(
                choices=[(i, f'{i} étoile{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-select rating-select'}
            ),
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Donnez un titre à votre avis...',
                'maxlength': 100
            }),
            'contenu': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Partagez votre expérience avec Furu Minanw...',
                'rows': 5,
                'maxlength': 500,
                'minlength': 100
            }),
            'date_mariage': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Pré-remplir la date de mariage si disponible dans le profil
        if self.user and hasattr(self.user, 'profil') and self.user.profil.date_mariage:
            self.fields['date_mariage'].initial = self.user.profil.date_mariage

    def clean_contenu(self):
        contenu = self.cleaned_data.get('contenu')
        if contenu and len(contenu) < 100:
            raise ValidationError('Votre avis doit contenir au moins 100 caractères.')
        if contenu and len(contenu) > 500:
            raise ValidationError('Votre avis ne peut pas dépasser 500 caractères.')
        return contenu

    def clean(self):
        cleaned_data = super().clean()

        # Vérifier que l'utilisateur peut laisser un avis
        if self.user and hasattr(self.user, 'profil'):
            if not self.user.profil.peut_laisser_avis():
                raise ValidationError(
                    'Vous devez avoir une photo de profil et une date de mariage '
                    'pour pouvoir laisser un avis.'
                )

        return cleaned_data


class PhotoAvisForm(forms.ModelForm):
    class Meta:
        model = PhotoAvis
        fields = ['image', 'legende']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'legende': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Légende de la photo (optionnel)...',
                'maxlength': 200
            })
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Vérifier la taille du fichier (5MB max)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('La photo ne doit pas dépasser 5MB.')

            # Vérifier le format
            if not image.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise ValidationError('Seuls les formats JPG et PNG sont acceptés.')

        return image


# Formset pour gérer plusieurs photos
PhotoAvisFormSet = forms.inlineformset_factory(
    AvisClient,
    PhotoAvis,
    form=PhotoAvisForm,
    extra=3,
    max_num=3,
    can_delete=True,
    fields=['image', 'legende']
)


class SuppressionCompteForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Saisissez votre mot de passe'
        }),
        label='Mot de passe',
        help_text='Saisissez votre mot de passe pour confirmer la suppression'
    )

    confirmation = forms.BooleanField(
        required=True,
        label='Je comprends que cette action est irréversible',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not authenticate(username=self.user.username, password=password):
            raise forms.ValidationError('Mot de passe incorrect.')
        return password