from django.contrib import admin

from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("codigo_barras", "marca", "sabor", "formato", "cajas_por_pallet", "activo")
    search_fields = ("codigo_barras", "marca", "sabor")
    list_filter = ("marca", "activo")
