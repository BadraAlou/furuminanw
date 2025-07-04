from django.contrib import admin
from .models import Pack, Option, OptionDePack, ImagePack

class OptionDePackInline(admin.TabularInline):
    model = OptionDePack
    extra = 1

class ImagePackInline(admin.TabularInline):
    model = ImagePack
    extra = 1

@admin.register(Pack)
class PackAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prix', 'categorie', 'actif')
    list_filter = ('categorie', 'actif')
    search_fields = ('nom', 'description')
    prepopulated_fields = {'slug': ('nom',)}
    inlines = [OptionDePackInline, ImagePackInline]

@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie')
    list_filter = ('categorie',)
    search_fields = ('nom',)