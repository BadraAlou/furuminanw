from django import forms

class ContactForm(forms.Form):
    nom = forms.CharField(max_length=100)
    email = forms.EmailField()
    sujet = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea)