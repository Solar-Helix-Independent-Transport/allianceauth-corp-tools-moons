from django.contrib import admin

# Register your models here.
from .models import MoonFrack, MiningTax, OreTaxRates


class MoonAdmin(admin.ModelAdmin):
    list_select_related = True
    list_display = ['corporation','moon_name', 'arrival_time', 'notification']
    search_fields = ('corporation', 'moon_name')
    raw_id_fields = ('corporation', 'moon_name', 'structure', 'notification')
    

admin.site.register(MoonFrack, MoonAdmin)


class TaxAdmin(admin.ModelAdmin):
    list_display = ('rank', 'corp', 'use_variable_tax', 'tax_rate', '__str__')
    search_fields = ['region', 'constellation', 'system', 'moon', 'corp']
    ordering = ('-rank',)
    raw_id_fields = ('region', 'constellation', 'system', 'moon')


admin.site.register(MiningTax, TaxAdmin)


class OreTaxRatesAdmin(admin.ModelAdmin):
    list_display=('tag', 'refine_rate', 'exceptional_rate', 'rare_rate', 'uncommon_rate', 'common_rate', 'ubiquitous_rate', 'ore_rate')

admin.site.register(OreTaxRates, OreTaxRatesAdmin)
