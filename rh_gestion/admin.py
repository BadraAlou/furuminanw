from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils import timezone
from .models import Poste, Employe, Conge, ArretTravail, FicheDePaie


class CongeInline(admin.TabularInline):
    model = Conge
    extra = 0
    readonly_fields = ('date_demande', 'duree_jours')
    fields = ('type_conge', 'date_debut', 'date_fin', 'duree_jours', 'statut', 'motif')

    def duree_jours(self, obj):
        if obj.date_debut and obj.date_fin:
            return obj.duree_jours()
        return '-'

    duree_jours.short_description = 'Durée (jours)'


class ArretTravailInline(admin.TabularInline):
    model = ArretTravail
    extra = 0
    readonly_fields = ('date_declaration', 'duree_jours')
    fields = ('date_debut', 'date_fin', 'duree_jours', 'statut', 'motif')

    def duree_jours(self, obj):
        if obj.date_debut and obj.date_fin:
            return obj.duree_jours()
        return '-'

    duree_jours.short_description = 'Durée (jours)'


class FicheDePaieInline(admin.TabularInline):
    model = FicheDePaie
    extra = 0
    readonly_fields = ('date_emission', 'salaire_net')
    fields = ('mois', 'annee', 'salaire_base', 'primes', 'retenues', 'salaire_net')


@admin.register(Poste)
class PosteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'departement_colore', 'nombre_employes', 'actif', 'date_creation')
    list_filter = ('departement', 'actif', 'date_creation')
    search_fields = ('nom', 'description')
    readonly_fields = ('date_creation', 'nombre_employes')
    list_editable = ('actif',)

    fieldsets = (
        ('Informations du poste', {
            'fields': ('nom', 'departement', 'description', 'actif')
        }),
        ('Statistiques', {
            'fields': ('nombre_employes', 'date_creation'),
            'classes': ('collapse',)
        })
    )

    def departement_colore(self, obj):
        colors = {
            'direction': '#8B0000',
            'administration': '#4169E1',
            'comptabilite': '#228B22',
            'it': '#FF4500',
            'commercial': '#9932CC',
            'marketing': '#FF1493',
            'communication': '#00CED1',
            'service_client': '#FFD700',
            'logistique': '#8B4513',
            'services_generaux': '#708090',
            'securite': '#DC143C'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.departement, '#000000'),
            obj.get_departement_display()
        )

    departement_colore.short_description = 'Département'
    departement_colore.admin_order_field = 'departement'


@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display = (
        'photo_miniature', 'nom_complet', 'poste', 'statut',
        'age', 'anciennete', 'salaire', 'est_en_conge', 'est_en_arret'
    )
    list_filter = ('statut', 'poste__departement', 'poste', 'date_embauche', 'ville')
    search_fields = ('nom', 'prenom', 'email', 'telephone')
    readonly_fields = ('date_creation', 'date_modification', 'age', 'anciennete', 'photo_preview')
    list_editable = ('statut',)
    inlines = [CongeInline, ArretTravailInline, FicheDePaieInline]

    fieldsets = (
        ('Informations personnelles', {
            'fields': ('nom', 'prenom', 'email', 'telephone', 'date_naissance', 'age')
        }),
        ('Photo', {
            'fields': ('photo', 'photo_preview'),
            'classes': ('collapse',)
        }),
        ('Informations professionnelles', {
            'fields': ('date_embauche', 'anciennete', 'poste', 'salaire', 'statut')
        }),
        ('Adresse', {
            'fields': ('adresse', 'ville', 'pays'),
            'classes': ('collapse',)
        }),
        ('Notes et observations', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        })
    )

    def photo_miniature(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />',
                obj.photo.url
            )
        return format_html(
            '<div style="width: 40px; height: 40px; border-radius: 50%; background-color: #ddd; display: flex; align-items: center; justify-content: center; font-size: 12px;">👤</div>')

    photo_miniature.short_description = 'Photo'

    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 8px;" />',
                obj.photo.url
            )
        return "Aucune photo"

    photo_preview.short_description = 'Aperçu photo'

    def statut_colore(self, obj):
        colors = {
            'actif': '#28A745',
            'conge': '#FFC107',
            'arret': '#FF6B6B',
            'suspendu': '#FF8C00',
            'demission': '#6C757D',
            'licencie': '#DC3545',
            'retraite': '#17A2B8'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.statut, '#000000'),
            obj.get_statut_display()
        )

    statut_colore.short_description = 'Statut'
    statut_colore.admin_order_field = 'statut'

    actions = ['marquer_actif', 'marquer_conge', 'marquer_arret']

    def marquer_actif(self, request, queryset):
        updated = queryset.update(statut='actif')
        self.message_user(request, f'{updated} employé(s) marqué(s) comme actif(s).')

    marquer_actif.short_description = "Marquer comme actif"

    def marquer_conge(self, request, queryset):
        updated = queryset.update(statut='conge')
        self.message_user(request, f'{updated} employé(s) marqué(s) en congé.')

    marquer_conge.short_description = "Marquer en congé"

    def marquer_arret(self, request, queryset):
        updated = queryset.update(statut='arret')
        self.message_user(request, f'{updated} employé(s) marqué(s) en arrêt.')

    marquer_arret.short_description = "Marquer en arrêt"


@admin.register(Conge)
class CongeAdmin(admin.ModelAdmin):
    list_display = (
        'employe', 'type_conge', 'date_debut', 'date_fin', 'duree_jours',
        'statut_colore', 'date_demande', 'validateur'
    )
    list_filter = ('type_conge', 'statut', 'date_demande', 'employe__poste__departement')
    search_fields = ('employe__nom', 'employe__prenom', 'motif')
    readonly_fields = ('date_demande', 'duree_jours')
    date_hierarchy = 'date_debut'

    fieldsets = (
        ('Informations du congé', {
            'fields': ('employe', 'type_conge', 'date_debut', 'date_fin', 'duree_jours', 'motif')
        }),
        ('Validation', {
            'fields': ('statut', 'validateur', 'date_validation', 'commentaire_validation')
        }),
        ('Métadonnées', {
            'fields': ('date_demande',),
            'classes': ('collapse',)
        })
    )

    def statut_colore(self, obj):
        colors = {
            'en_attente': '#FFC107',
            'valide': '#28A745',
            'rejete': '#DC3545',
            'annule': '#6C757D'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.statut, '#000000'),
            obj.get_statut_display()
        )

    statut_colore.short_description = 'Statut'
    statut_colore.admin_order_field = 'statut'

    def save_model(self, request, obj, form, change):
        if change and 'statut' in form.changed_data and obj.statut in ['valide', 'rejete']:
            obj.validateur = request.user
            obj.date_validation = timezone.now()
        super().save_model(request, obj, form, change)

    actions = ['valider_conges', 'rejeter_conges']

    def valider_conges(self, request, queryset):
        updated = queryset.filter(statut='en_attente').update(
            statut='valide',
            validateur=request.user,
            date_validation=timezone.now()
        )
        self.message_user(request, f'{updated} congé(s) validé(s).')

    valider_conges.short_description = "Valider les congés sélectionnés"

    def rejeter_conges(self, request, queryset):
        updated = queryset.filter(statut='en_attente').update(
            statut='rejete',
            validateur=request.user,
            date_validation=timezone.now()
        )
        self.message_user(request, f'{updated} congé(s) rejeté(s).')

    rejeter_conges.short_description = "Rejeter les congés sélectionnés"


@admin.register(ArretTravail)
class ArretTravailAdmin(admin.ModelAdmin):
    list_display = (
        'employe', 'date_debut', 'date_fin', 'duree_jours',
        'statut_colore', 'date_declaration', 'validateur'
    )
    list_filter = ('statut', 'date_declaration', 'employe__poste__departement')
    search_fields = ('employe__nom', 'employe__prenom', 'motif')
    readonly_fields = ('date_declaration', 'duree_jours', 'justificatif_preview')
    date_hierarchy = 'date_debut'

    fieldsets = (
        ('Informations de l\'arrêt', {
            'fields': ('employe', 'date_debut', 'date_fin', 'duree_jours', 'motif')
        }),
        ('Justificatif', {
            'fields': ('justificatif', 'justificatif_preview')
        }),
        ('Validation', {
            'fields': ('statut', 'validateur', 'date_validation')
        }),
        ('Métadonnées', {
            'fields': ('date_declaration',),
            'classes': ('collapse',)
        })
    )

    def justificatif_preview(self, obj):
        if obj.justificatif:
            if obj.justificatif.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                return format_html(
                    '<img src="{}" style="max-width: 300px; max-height: 200px;" />',
                    obj.justificatif.url
                )
            else:
                return format_html(
                    '<a href="{}" target="_blank">📄 Voir le justificatif PDF</a>',
                    obj.justificatif.url
                )
        return "Aucun justificatif"

    justificatif_preview.short_description = 'Aperçu justificatif'

    def statut_colore(self, obj):
        colors = {
            'en_attente': '#FFC107',
            'valide': '#28A745',
            'rejete': '#DC3545'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.statut, '#000000'),
            obj.get_statut_display()
        )

    statut_colore.short_description = 'Statut'
    statut_colore.admin_order_field = 'statut'

    def save_model(self, request, obj, form, change):
        if change and 'statut' in form.changed_data and obj.statut in ['valide', 'rejete']:
            obj.validateur = request.user
            obj.date_validation = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(FicheDePaie)
class FicheDePaieAdmin(admin.ModelAdmin):
    list_display = (
        'employe', 'periode', 'salaire_base', 'primes', 'retenues',
        'salaire_net', 'date_emission', 'pdf_disponible'
    )
    list_filter = ('annee', 'mois', 'employe__poste__departement')
    search_fields = ('employe__nom', 'employe__prenom')
    readonly_fields = ('date_emission', 'salaire_net_calcule')
    date_hierarchy = 'date_emission'

    fieldsets = (
        ('Informations générales', {
            'fields': ('employe', 'mois', 'annee')
        }),
        ('Détail de la paie', {
            'fields': ('salaire_base', 'primes', 'retenues', 'salaire_net_calcule')
        }),
        ('Document PDF', {
            'fields': ('pdf',)
        }),
        ('Métadonnées', {
            'fields': ('date_emission',),
            'classes': ('collapse',)
        })
    )

    def salaire_net_calcule(self, obj):
        if obj.salaire_base is not None:
            net = obj.salaire_base + (obj.primes or 0) - (obj.retenues or 0)
            return format_html(
                '<strong style="color: #28A745; font-size: 1.1em;">{:,.0f} FCFA</strong>',
                net
            )
        return '-'

    salaire_net_calcule.short_description = 'Salaire net calculé'

    def pdf_disponible(self, obj):
        if obj.pdf:
            return format_html(
                '<a href="{}" target="_blank" style="color: #28A745;">📄 Télécharger</a>',
                obj.pdf.url
            )
        return format_html('<span style="color: #DC3545;">❌ Non disponible</span>')

    pdf_disponible.short_description = 'PDF'

    def save_model(self, request, obj, form, change):
        # Calcul automatique du salaire net
        obj.salaire_net = obj.salaire_base + (obj.primes or 0) - (obj.retenues or 0)
        super().save_model(request, obj, form, change)


# Personnalisation du site admin
admin.site.site_header = "Administration RH - Furu Minanw"
admin.site.site_title = "RH Admin"
admin.site.index_title = "Gestion des Ressources Humaines"