from django.contrib import admin

from .models import Alerta


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ("lote", "tipo", "dias_restantes", "cajas", "atendida", "fecha")
    list_filter = ("tipo", "atendida")
