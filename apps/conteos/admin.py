from django.contrib import admin

from .models import Conteo, DetalleConteo


class DetalleInline(admin.TabularInline):
    model = DetalleConteo
    extra = 0
    fk_name = "conteo"
    readonly_fields = ("lote", "ubicacion", "cant_sistema", "cant_fisica", "diferencia", "estado", "motivo")


@admin.register(Conteo)
class ConteoAdmin(admin.ModelAdmin):
    list_display = ("id", "fecha", "descripcion", "estado", "usuario")
    inlines = [DetalleInline]
