from django.contrib import admin

# Register your models here.
from .models import (
    InvoiceRecord, MiningTax, MoonFrack, MoonRental, OreTaxRates,
    RentalRepricing,
)
from .tasks import invoice_single_moon


@admin.register(MoonFrack)
class MoonAdmin(admin.ModelAdmin):
    list_select_related = True
    list_display = ['corporation', 'moon_name', 'arrival_time', 'notification']
    search_fields = ('corporation', 'moon_name')
    raw_id_fields = ('corporation', 'moon_name', 'structure', 'notification')




@admin.register(MiningTax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ('rank', 'corp', 'use_variable_tax', 'tax_rate', '__str__')
    search_fields = ['region', 'constellation', 'system', 'moon', 'corp']
    ordering = ('-rank',)
    raw_id_fields = ('region', 'constellation', 'system', 'moon')




@admin.register(OreTaxRates)
class OreTaxRatesAdmin(admin.ModelAdmin):
    list_display = ('tag', 'refine_rate', 'exceptional_rate', 'rare_rate',
                    'uncommon_rate', 'common_rate', 'ubiquitous_rate', 'ore_rate',
                    'show_in_moon_values', 'drill_m3_per_hour')




@admin.register(InvoiceRecord)
class InvoiceAdmin(admin.ModelAdmin):
    list_select_related = True

    # generate a custom formater cause i am lazy...
    def __init__(self, *args, **kwargs):
        def generate_formatter(name, str_format):
            def formatter(o): return str_format.format(getattr(o, name) or 0)
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

    list_display = ['base_ref', 'start_date', 'end_date',
                    ('total_mined', "{:,}"), ('total_taxed', "{:,}")]


@admin.action(description='Send Partial Invoice for Selected')
def invoice_send_action(RentalAdmin, request, queryset):
    for i in queryset:
        invoice_single_moon.delay(i.id)


@admin.register(MoonRental)
class RentalAdmin(admin.ModelAdmin):
    list_select_related = (
        'corporation', 'contact', 'moon',
        'moon__solar_system__constellation__region', 'reprice_method',
    )
    raw_id_fields = ('corporation', 'contact', 'moon')
    list_filter = ('reprice_method',)
    search_fields = (
        'corporation__corporation_name', 'contact__character_name', 'moon__name',
        'moon__solar_system__constellation__name',
        'moon__solar_system__constellation__region__name',
    )

    actions = [invoice_send_action]

    @admin.display(
        description='Constellation',
        ordering='moon__solar_system__constellation__name',
    )
    def constellation(self, obj):
        return obj.moon.solar_system.constellation.name

    @admin.display(
        description='Region',
        ordering='moon__solar_system__constellation__region__name',
    )
    def region(self, obj):
        return obj.moon.solar_system.constellation.region.name

    # generate a custom formater cause i am lazy...
    def __init__(self, *args, **kwargs):
        def generate_formatter(name, str_format):
            def formatter(o): return str_format.format(getattr(o, name) or 0)
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

    list_display = ['moon', 'constellation', 'region', 'contact', 'corporation',
                    'start_date', 'end_date', ('price', "{:,}"), 'reprice_method']


@admin.register(RentalRepricing)
class RentalRepricingAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'dry_run', 'notify_renters', 'channel_id', 'last_run')
    readonly_fields = ('last_run',)

    def has_add_permission(self, request):
        # one settings row
        return not RentalRepricing.objects.exists() and super().has_add_permission(request)
