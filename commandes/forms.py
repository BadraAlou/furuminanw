from django import forms
from django.forms import formset_factory
from .models import Commande, PrecisionPersonnalisation
from produits.models import Option


class CommandeForm(forms.ModelForm):
    class Meta:
        model = Commande
        fields = ['email', 'telephone', 'adresse_livraison', 'ville', 'code_postal', 'methode_paiement', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class PrecisionPersonnalisationForm(forms.ModelForm):
    """Formulaire pour saisir les précisions de personnalisation"""

    class Meta:
        model = PrecisionPersonnalisation
        fields = [
            'texte_a_graver', 'date_a_graver', 'mot_doux', 'laisser_choisir_mot_doux',
            'couleur_preference', 'taille_preference', 'instructions_speciales'
        ]
        widgets = {
            'texte_a_graver': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Quel texte souhaitez-vous faire graver ?'
            }),
            'date_a_graver': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 15/06/2024'
            }),
            'mot_doux': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': 100,
                'placeholder': 'Votre mot doux personnalisé...'
            }),
            'laisser_choisir_mot_doux': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'couleur_preference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Rouge, Bleu, Doré...'
            }),
            'taille_preference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: S, M, L, XL ou dimensions spécifiques'
            }),
            'instructions_speciales': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Toute autre précision importante...'
            })
        }

    def __init__(self, *args, **kwargs):
        self.option = kwargs.pop('option', None)
        super().__init__(*args, **kwargs)

        # Adapter les champs selon le type d'option
        if self.option:
            self.adapter_champs_selon_option()

    def adapter_champs_selon_option(self):
        """Adapter les champs visibles selon le type d'option"""
        option_nom = self.option.nom.lower()

        # Masquer tous les champs par défaut
        champs_a_masquer = [
            'texte_a_graver', 'date_a_graver', 'mot_doux', 'laisser_choisir_mot_doux',
            'couleur_preference', 'taille_preference'
        ]

        # Afficher les champs pertinents selon l'option
        if 'gravure' in option_nom or 'graver' in option_nom:
            if 'prénom' in option_nom or 'nom' in option_nom:
                champs_a_masquer.remove('texte_a_graver')
                self.fields['texte_a_graver'].label = "Quel prénom/nom graver ?"
                self.fields['texte_a_graver'].widget.attrs['placeholder'] = "Ex: Marie, Ibrahim..."

            if 'date' in option_nom:
                champs_a_masquer.remove('date_a_graver')
                self.fields['date_a_graver'].label = "Quelle date graver ?"

            if 'mot' in option_nom or 'message' in option_nom:
                champs_a_masquer.remove('mot_doux')
                champs_a_masquer.remove('laisser_choisir_mot_doux')
                self.fields['mot_doux'].label = "Votre mot doux"

        elif 'couleur' in option_nom:
            champs_a_masquer.remove('couleur_preference')
            self.fields['couleur_preference'].label = "Quelle couleur préférez-vous ?"

        elif 'taille' in option_nom:
            champs_a_masquer.remove('taille_preference')
            self.fields['taille_preference'].label = "Quelle taille souhaitez-vous ?"

        # Masquer les champs non pertinents
        for champ in champs_a_masquer:
            self.fields[champ].widget = forms.HiddenInput()
            self.fields[champ].required = False

    def clean(self):
        cleaned_data = super().clean()

        # Validation conditionnelle selon l'option
        if self.option:
            option_nom = self.option.nom.lower()

            # Validation pour les options de gravure
            if 'gravure' in option_nom or 'graver' in option_nom:
                if 'prénom' in option_nom or 'nom' in option_nom:
                    if not cleaned_data.get('texte_a_graver'):
                        raise forms.ValidationError({
                            'texte_a_graver': 'Veuillez préciser le texte à graver.'
                        })

                if 'date' in option_nom:
                    if not cleaned_data.get('date_a_graver'):
                        raise forms.ValidationError({
                            'date_a_graver': 'Veuillez préciser la date à graver.'
                        })

                if 'mot' in option_nom or 'message' in option_nom:
                    if not cleaned_data.get('mot_doux') and not cleaned_data.get('laisser_choisir_mot_doux'):
                        raise forms.ValidationError({
                            'mot_doux': 'Veuillez saisir un mot doux ou cocher "Laissez-nous choisir".'
                        })

            # Validation pour les options de couleur
            elif 'couleur' in option_nom:
                if not cleaned_data.get('couleur_preference'):
                    raise forms.ValidationError({
                        'couleur_preference': 'Veuillez préciser votre couleur préférée.'
                    })

            # Validation pour les options de taille
            elif 'taille' in option_nom:
                if not cleaned_data.get('taille_preference'):
                    raise forms.ValidationError({
                        'taille_preference': 'Veuillez préciser la taille souhaitée.'
                    })

        return cleaned_data


def creer_formset_precisions(options_selectionnees):
    """Créer un formset dynamique pour les précisions selon les options sélectionnées"""

    class PrecisionFormSetBase(forms.BaseFormSet):
        def __init__(self, *args, **kwargs):
            self.options = kwargs.pop('options', [])
            super().__init__(*args, **kwargs)

        def _construct_form(self, i, **kwargs):
            if i < len(self.options):
                kwargs['option'] = self.options[i]
            return super()._construct_form(i, **kwargs)

    # Créer le formset avec le bon nombre de formulaires
    PrecisionFormSet = formset_factory(
        PrecisionPersonnalisationForm,
        formset=PrecisionFormSetBase,
        extra=len(options_selectionnees),
        max_num=len(options_selectionnees),
        can_delete=False
    )

    return PrecisionFormSet