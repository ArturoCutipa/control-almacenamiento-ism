from django.contrib import admin

from .models import ExportacionSAP


@admin.register(ExportacionSAP)
class ExportacionSAPAdmin(admin.ModelAdmin):
    list_display = ("fecha_corte", "fecha_hora", "total_registros", "total_cajas", "usuario")
