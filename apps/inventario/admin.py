from django.contrib import admin

from .models import Lote, Stock


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ("numero_lote", "producto", "fecha_vencimiento", "estado")
    list_filter = ("estado",)
    search_fields = ("numero_lote", "producto__codigo_barras")


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("lote", "ubicacion", "cantidad_cajas", "actualizado")
    search_fields = ("lote__numero_lote", "ubicacion__codigo_qr")
