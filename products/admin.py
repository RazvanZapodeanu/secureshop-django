from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Produs, Producator, Specificatie, Categorie, Tag, Review, Discount, Utilizator, Vizualizare, Promotie, Comanda, ProdusComanda, Nota

admin.site.site_header = "SECURED SYSTEMS - Panou Administrare"
admin.site.site_title = "Lambda Security"
admin.site.index_title = "Dashboard Management"


class ProducatorAdmin(admin.ModelAdmin):
    list_display = ('nume', 'tara_origine', 'website', 'activ')
    search_fields = ('nume', 'descriere')
    ordering = ['nume']
    list_filter = ('activ', 'tara_origine')
    empty_value_display = 'necompletat'


class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nume', 'slug', 'activa')
    search_fields = ('nume', 'descriere')
    list_filter = ('activa',)
    empty_value_display = 'necompletat'


class TagAdmin(admin.ModelAdmin):
    list_display = ('nume', 'slug', 'culoare')
    search_fields = ('nume', 'slug')
    list_filter = ('culoare',)
    empty_value_display = 'necompletat'


class SpecificatieInline(admin.TabularInline):
    model = Specificatie
    extra = 1
    fields = ('nume', 'valoare', 'ordine', 'activa')


class ProdusAdmin(admin.ModelAdmin):
    list_display = ('cod_produs', 'nume', 'producator', 'pret', 'stoc', 'disponibil')
    search_fields = ('nume', 'descriere_lunga')
    ordering = ['-pret']
    list_per_page = 5
    list_filter = ('disponibil', 'producator', 'categorii')
    fieldsets = (
        ('Informatii Generale', {
            'fields': ('nume', 'slug', 'cod_produs', 'producator')
        }),
        ('Descriere', {
            'fields': ('descriere_scurta', 'descriere_lunga'),
            'classes': ('collapse',),
        }),
        ('Pret si Stoc', {
            'fields': ('pret', 'pret_vechi', 'stoc', 'disponibil')
        }),
        ('Media', {
            'fields': ('imagine',),
            'classes': ('collapse',),
        }),
        ('Clasificare', {
            'fields': ('categorii', 'tag_uri'),
            'classes': ('collapse',),
        }),
    )
    inlines = [SpecificatieInline]
    empty_value_display = 'necompletat'


class SpecificatieAdmin(admin.ModelAdmin):
    list_display = ('nume', 'produs', 'valoare', 'ordine', 'activa')
    search_fields = ('nume', 'valoare')
    list_filter = ('activa', 'produs')
    ordering = ['ordine']
    list_per_page = 10
    empty_value_display = 'necompletat'


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('titlu', 'produs', 'rating', 'nume_client', 'verificat', 'data_review')
    search_fields = ('titlu', 'comentariu')
    list_filter = ('rating', 'verificat', 'data_review')
    list_per_page = 5
    ordering = ['-data_review']
    fieldsets = (
        ('Review', {
            'fields': ('produs', 'rating', 'titlu', 'comentariu')
        }),
        ('Informatii Client', {
            'fields': ('nume_client', 'verificat'),
        }),
    )
    empty_value_display = 'necompletat'


class DiscountAdmin(admin.ModelAdmin):
    list_display = ('produs', 'procent', 'data_inceput', 'data_sfarsit', 'activ')
    search_fields = ('produs__nume',)
    list_filter = ('activ', 'data_inceput', 'data_sfarsit')
    ordering = ['-data_inceput']
    fieldsets = (
        ('Informatii Discount', {
            'fields': ('produs', 'procent', 'activ')
        }),
        ('Perioada de Valabilitate', {
            'fields': ('data_inceput', 'data_sfarsit'),
        }),
    )
    empty_value_display = 'necompletat'


class UtilizatorAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'email_confirmat', 'blocat', 'is_staff')
    list_filter = ('email_confirmat', 'blocat', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ['username']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informatii Suplimentare', {
            'fields': ('telefon', 'adresa', 'oras', 'judet', 'cod_postal', 'data_nasterii', 'avatar')
        }),
        ('Status Cont', {
            'fields': ('cod', 'email_confirmat', 'blocat', 'notificare_campuri_lipsa', 'ultima_notificare_campuri')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informatii Suplimentare', {
            'fields': ('email', 'telefon', 'adresa', 'oras', 'judet', 'cod_postal')
        }),
    )


class VizualizareAdmin(admin.ModelAdmin):
    list_display = ('utilizator', 'produs', 'data_vizualizare')
    list_filter = ('data_vizualizare',)
    search_fields = ('utilizator__username', 'produs__nume')
    ordering = ['-data_vizualizare']


class PromotieAdmin(admin.ModelAdmin):
    list_display = ('nume', 'data_creare', 'data_expirare', 'procent_reducere', 'activa')
    list_filter = ('activa', 'data_expirare')
    search_fields = ('nume', 'descriere')
    filter_horizontal = ('categorii',)


class ProdusComandaInline(admin.TabularInline):
    model = ProdusComanda
    extra = 0
    readonly_fields = ('produs', 'cantitate', 'pret_unitar')


class ComandaAdmin(admin.ModelAdmin):
    list_display = ('id', 'utilizator', 'data_comanda', 'stare', 'total')
    list_filter = ('stare', 'data_comanda')
    search_fields = ('utilizator__username', 'adresa_livrare')
    ordering = ['-data_comanda']
    inlines = [ProdusComandaInline]
    readonly_fields = ('data_comanda',)


class NotaAdmin(admin.ModelAdmin):
    list_display = ('utilizator', 'produs', 'nota', 'data_notare')
    list_filter = ('nota', 'data_notare')
    search_fields = ('utilizator__username', 'produs__nume')


admin.site.register(Producator, ProducatorAdmin)
admin.site.register(Categorie, CategorieAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Produs, ProdusAdmin)
admin.site.register(Specificatie, SpecificatieAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Discount, DiscountAdmin)
admin.site.register(Utilizator, UtilizatorAdmin)
admin.site.register(Vizualizare, VizualizareAdmin)
admin.site.register(Promotie, PromotieAdmin)
admin.site.register(Comanda, ComandaAdmin)
admin.site.register(Nota, NotaAdmin)
