from django.contrib import admin

# Register your models here.
from .models import MoonFrack


class MoonAdmin(admin.ModelAdmin):
    
    list_select_related = True
    list_display=['corporation','moon_name', 'arrival_time']
    search_fields = ('corporation', 'moon_name')
    raw_id_fields = ('corporation', 'moon_name')
    
admin.site.register(MoonFrack, MoonAdmin)
