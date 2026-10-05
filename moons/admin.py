from solo.admin import SingletonModelAdmin

from django.contrib import admin
from django.utils import timezone

# Register your models here.
from .models import (
    InvoiceRecord, MiningTax, MoonAvailability, MoonFrack, MoonRental,
    OreTaxRates, RentalRepricing,
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
class RentalRepricingAdmin(SingletonModelAdmin):
    readonly_fields = ('last_run',)


@admin.register(MoonAvailability)
class MoonAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('moon', 'available', 'changed_by', 'changed_at', 'note')
    list_filter = ('available', 'moon__solar_system__constellation__region')
    list_select_related = ('moon', 'changed_by')
    search_fields = ('moon__name', 'note')
    raw_id_fields = ('moon',)
    readonly_fields = ('changed_by', 'changed_at')

    def save_model(self, request, obj, form, change):
        obj.changed_by = request.user
        obj.changed_at = timezone.now()
        super().save_model(request, obj, form, change)
