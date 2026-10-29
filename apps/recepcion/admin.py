from django.contrib import admin

from .models import DetalleRecepcion, Recepcion


class DetalleInline(admin.TabularInline):
    model = DetalleRecepcion
    extra = 0
    readonly_fields = ("lote", "cantidad_cajas", "pallets", "ubicacion")


@admin.register(Recepcion)
class RecepcionAdmin(admin.ModelAdmin):
    list_display = ("guia_remision", "usuario", "fecha_hora_inicio", "fecha_hora_fin")
    inlines = [DetalleInline]
