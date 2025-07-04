from django.contrib import admin
from django.utils.html import format_html
from .models import Commande, ElementCommande, PrecisionPersonnalisation


class PrecisionPersonnalisationInline(admin.TabularInline):
    model = PrecisionPersonnalisation
    extra = 0
    readonly_fields = ('option', 'resume_precisions')
    fields = ('option', 'resume_precisions', 'texte_a_graver', 'date_a_graver', 'mot_doux', 'laisser_choisir_mot_doux',
              'couleur_preference', 'taille_preference', 'instructions_speciales')

    def resume_precisions(self, obj):
        if obj.pk:
            return obj.get_resume_precisions()
        return "Aucune précision"

    resume_precisions.short_description = 'Résumé des précisions'


class ElementCommandeInline(admin.TabularInline):
    model = ElementCommande
    extra = 0
    readonly_fields = ('pack', 'quantite', 'prix', 'options_resume', 'precisions_resume')
    fields = ('pack', 'quantite', 'prix', 'options_resume', 'precisions_resume')

    def options_resume(self, obj):
        if obj.options_selectionnees.exists():
            options = [opt.nom for opt in obj.options_selectionnees.all()]
            return ", ".join(options)
        return "Aucune option"

    options_resume.short_description = 'Options sélectionnées'

    def precisions_resume(self, obj):
        if obj.precisions_personnalisation.exists():
            precisions = []
            for precision in obj.precisions_personnalisation.all():
                precisions.append(f"{precision.option.nom}: {precision.get_resume_precisions()}")
            return format_html("<br>".join(precisions))
        return "Aucune précision"

    precisions_resume.short_description = 'Précisions de personnalisation'


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'date_commande', 'statut_colore', 'methode_paiement', 'total', 'actions_admin')
    list_filter = ('statut', 'methode_paiement', 'date_commande', 'archivee')
    search_fields = ('client__email', 'client__first_name', 'client__last_name', 'adresse_livraison')
    readonly_fields = ('date_commande', 'total')
    inlines = [ElementCommandeInline]
    actions = ['archiver_commandes']  # Liste de chaînes de caractères

    fieldsets = (
        ('Informations client', {
            'fields': ('client', 'email', 'telephone')
        }),
        ('Informations de livraison', {
            'fields': ('adresse_livraison', 'ville', 'code_postal', 'pays')
        }),
        ('Informations de commande', {
            'fields': ('date_commande', 'statut', 'methode_paiement', 'notes', 'total', 'archivee')
        }),
        ('Notes administrateur', {
            'fields': ('notes_admin',),
            'classes': ('collapse',)
        })
    )

    def statut_colore(self, obj):
        colors = {
            'en_attente': '#FFC107',  # Jaune
            'confirmee': '#17A2B8',  # Bleu clair
            'en_preparation': '#007BFF',  # Bleu
            'expediee': '#6610F2',  # Violet
            'livree': '#28A745',  # Vert
            'annulee': '#DC3545'  # Rouge
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors[obj.statut],
            obj.get_statut_display()
        )

    statut_colore.short_description = 'Statut'

    def actions_admin(self, obj):  # Renommé pour éviter le conflit avec self.actions
        if obj.archivee:
            return format_html(
                '<span class="badge bg-secondary">Archivée</span>'
            )
        return format_html(
            '<a class="button" href="{}">Modifier</a>',
            f'/admin/commandes/commande/{obj.id}/change/'
        )

    actions_admin.short_description = 'Actions'

    def archiver_commandes(self, request, queryset):
        updated = queryset.update(archivee=True)
        self.message_user(request, f'{updated} commande(s) ont été archivée(s).')

    archiver_commandes.short_description = "Archiver les commandes sélectionnées"

    class Media:
        css = {
            'all': ('css/admin_commandes.css',)
        }
        js = ('js/admin_commandes.js',)


@admin.register(ElementCommande)
class ElementCommandeAdmin(admin.ModelAdmin):
    list_display = ('commande', 'pack', 'quantite', 'prix', 'options_count', 'precisions_count')
    list_filter = ('commande__statut', 'pack__categorie')
    search_fields = ('commande__id', 'pack__nom')
    inlines = [PrecisionPersonnalisationInline]

    def options_count(self, obj):
        return obj.options_selectionnees.count()

    options_count.short_description = 'Nb options'

    def precisions_count(self, obj):
        return obj.precisions_personnalisation.count()

    precisions_count.short_description = 'Nb précisions'


@admin.register(PrecisionPersonnalisation)
class PrecisionPersonnalisationAdmin(admin.ModelAdmin):
    list_display = ('element_commande', 'option', 'resume_precisions_court', 'date_creation')
    list_filter = ('option__categorie', 'date_creation')
    search_fields = ('element_commande__commande__id', 'option__nom', 'texte_a_graver', 'mot_doux')
    readonly_fields = ('date_creation', 'date_modification')

    fieldsets = (
        ('Informations générales', {
            'fields': ('element_commande', 'option')
        }),
        ('Précisions de gravure', {
            'fields': ('texte_a_graver', 'date_a_graver', 'mot_doux', 'laisser_choisir_mot_doux'),
            'classes': ('collapse',)
        }),
        ('Préférences', {
            'fields': ('couleur_preference', 'taille_preference'),
            'classes': ('collapse',)
        }),
        ('Instructions spéciales', {
            'fields': ('instructions_speciales',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        })
    )

    def resume_precisions_court(self, obj):
        resume = obj.get_resume_precisions()
        return resume[:50] + "..." if len(resume) > 50 else resume

    resume_precisions_court.short_description = 'Résumé'