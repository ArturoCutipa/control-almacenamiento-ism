from django.contrib import admin

from .models import Ubicacion


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ("codigo_qr", "zona", "nivel", "posicion", "capacidad_pallets", "activa")
    list_filter = ("zona", "activa")
    readonly_fields = ("codigo_qr",)
