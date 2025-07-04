from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils import timezone
from .models import Profil, AvisClient, PhotoAvis


class ProfilInline(admin.StackedInline):
    model = Profil
    can_delete = False
    verbose_name_plural = 'Profil'
    fk_name = 'utilisateur'
    readonly_fields = ('photo_profil_preview',)

    def photo_profil_preview(self, obj):
        if obj.photo_profil:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.photo_profil.url
            )
        return "Aucune photo"

    photo_profil_preview.short_description = "Aperçu photo de profil"


class UtilisateurCustomAdmin(UserAdmin):
    inlines = (ProfilInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_telephone', 'get_photo_profil')

    def get_telephone(self, instance):
        return instance.profil.telephone if hasattr(instance, 'profil') else '-'

    get_telephone.short_description = 'Téléphone'

    def get_photo_profil(self, instance):
        if hasattr(instance, 'profil') and instance.profil.photo_profil:
            return format_html(
                '<img src="{}" style="width: 30px; height: 30px; border-radius: 50%;" />',
                instance.profil.photo_profil.url
            )
        return "❌"

    get_photo_profil.short_description = 'Photo'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(UtilisateurCustomAdmin, self).get_inline_instances(request, obj)


class PhotoAvisInline(admin.TabularInline):
    model = PhotoAvis
    extra = 0
    readonly_fields = ('image_preview',)
    fields = ('image', 'image_preview', 'legende', 'ordre')

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 80px; max-width: 80px;" />',
                obj.image.url
            )
        return "Aucune image"

    image_preview.short_description = "Aperçu"


@admin.register(AvisClient)
class AvisClientAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'client_nom', 'note_etoiles', 'titre', 'statut_colore',
        'afficher_accueil', 'date_creation', 'date_mariage', 'actions_disponibles'
    )
    list_filter = ('statut', 'note', 'afficher_accueil', 'date_creation', 'date_mariage')
    search_fields = ('client__username', 'client__first_name', 'client__last_name', 'titre', 'contenu')
    readonly_fields = ('date_creation', 'date_modification', 'client_info', 'photos_preview')
    list_editable = ('afficher_accueil',)
    actions = ['approuver_avis', 'rejeter_avis', 'afficher_sur_accueil', 'masquer_de_accueil']
    inlines = [PhotoAvisInline]

    fieldsets = (
        ('Informations client', {
            'fields': ('client_info', 'date_mariage')
        }),
        ('Avis', {
            'fields': ('note', 'titre', 'contenu', 'photos_preview')
        }),
        ('Modération', {
            'fields': ('statut', 'afficher_accueil', 'commentaire_moderation', 'moderateur')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification', 'date_moderation'),
            'classes': ('collapse',)
        })
    )

    def client_nom(self, obj):
        return obj.client.profil.get_nom_affichage()

    client_nom.short_description = 'Client'

    def client_info(self, obj):
        profil = obj.client.profil
        info = f"<strong>{profil.get_nom_affichage()}</strong><br>"
        info += f"Email: {obj.client.email}<br>"
        if profil.photo_profil:
            info += f'<img src="{profil.photo_profil.url}" style="width: 60px; height: 60px; border-radius: 50%; margin-top: 10px;" />'
        return mark_safe(info)

    client_info.short_description = 'Informations client'

    def note_etoiles(self, obj):
        etoiles = '⭐' * obj.note + '☆' * (5 - obj.note)
        return f"{etoiles} ({obj.note}/5)"

    note_etoiles.short_description = 'Note'

    def statut_colore(self, obj):
        colors = {
            'en_attente': '#FFC107',
            'approuve': '#28A745',
            'rejete': '#DC3545'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors[obj.statut],
            obj.get_statut_display()
        )

    statut_colore.short_description = 'Statut'

    def photos_preview(self, obj):
        if obj.photos.exists():
            html = '<div style="display: flex; gap: 10px; flex-wrap: wrap;">'
            for photo in obj.photos.all():
                html += f'<img src="{photo.image.url}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 4px;" title="{photo.legende}" />'
            html += '</div>'
            return mark_safe(html)
        return "Aucune photo"

    photos_preview.short_description = 'Photos'

    def actions_disponibles(self, obj):
        if obj.statut == 'en_attente':
            return format_html(
                '<a class="button" href="{}">Modérer</a>',
                reverse('admin:utilisateurs_avisclient_change', args=[obj.id])
            )
        elif obj.statut == 'approuve':
            return format_html(
                '<span style="color: green;">✓ Approuvé</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Rejeté</span>'
            )

    actions_disponibles.short_description = 'Actions'

    def save_model(self, request, obj, form, change):
        if change and 'statut' in form.changed_data:
            obj.moderateur = request.user
            obj.date_moderation = timezone.now()
        super().save_model(request, obj, form, change)

    def approuver_avis(self, request, queryset):
        updated = queryset.update(
            statut='approuve',
            moderateur=request.user,
            date_moderation=timezone.now()
        )
        self.message_user(request, f'{updated} avis ont été approuvés.')

    approuver_avis.short_description = "Approuver les avis sélectionnés"

    def rejeter_avis(self, request, queryset):
        updated = queryset.update(
            statut='rejete',
            moderateur=request.user,
            date_moderation=timezone.now(),
            afficher_accueil=False
        )
        self.message_user(request, f'{updated} avis ont été rejetés.')

    rejeter_avis.short_description = "Rejeter les avis sélectionnés"

    def afficher_sur_accueil(self, request, queryset):
        # Seuls les avis approuvés peuvent être affichés
        queryset_approuve = queryset.filter(statut='approuve')
        updated = queryset_approuve.update(afficher_accueil=True)
        self.message_user(request, f'{updated} avis seront affichés sur la page d\'accueil.')

    afficher_sur_accueil.short_description = "Afficher sur la page d'accueil"

    def masquer_de_accueil(self, request, queryset):
        updated = queryset.update(afficher_accueil=False)
        self.message_user(request, f'{updated} avis ont été masqués de la page d\'accueil.')

    masquer_de_accueil.short_description = "Masquer de la page d'accueil"

    class Media:
        css = {
            'all': ('css/admin_avis.css',)
        }


@admin.register(PhotoAvis)
class PhotoAvisAdmin(admin.ModelAdmin):
    list_display = ('id', 'avis', 'image_preview', 'legende', 'ordre')
    list_filter = ('avis__statut',)
    search_fields = ('avis__titre', 'legende')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return "Aucune image"

    image_preview.short_description = "Aperçu"


# Réenregistrer UserAdmin
admin.site.unregister(User)
admin.site.register(User, UtilisateurCustomAdmin)

# Personnalisation du site admin
admin.site.site_header = "Administration Furu Minanw"
admin.site.site_title = "Furu Minanw Admin"
admin.site.index_title = "Gestion du site"