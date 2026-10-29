from django.contrib import admin

from .models import Movimiento


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ("fecha_hora", "tipo", "lote", "cantidad", "ubicacion_origen", "ubicacion_destino", "usuario")
    list_filter = ("tipo",)
    search_fields = ("lote__numero_lote",)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
