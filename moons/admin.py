from django.contrib import admin

# Register your models here.
from .models import MoonFrack, MiningTax, OreTaxRates, InvoiceRecord


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

class InvoiceAdmin(admin.ModelAdmin):
    #generate a custom formater cause i am lazy...
    def __init__(self, *args, **kwargs):
        def generate_formatter(name, str_format):
            formatter = lambda o: str_format.format(getattr(o, name) or 0)
            formatter.short_description = name
            formatter.admin_order_field = name
            return formatter

        all_fields = []
        for f in self.list_display:
            if isinstance(f, str):
                all_fields.append(f)
            else:
                new_field_name = "_" + f[0]
                setattr(self, new_field_name, generate_formatter(f[0], f[1]))
                all_fields.append(new_field_name)
        self.list_display = all_fields

        super().__init__(*args, **kwargs)

    list_display = ['base_ref', 'start_date', 'end_date', ('total_mined', "{:,}"), ('total_taxed', "{:,}")]
    

admin.site.register(InvoiceRecord, InvoiceAdmin)
