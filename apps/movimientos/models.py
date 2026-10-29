from django.conf import settings
from django.db import models

from apps.inventario.models import Lote
from apps.ubicaciones.models import Ubicacion


class Movimiento(models.Model):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    TRANSFERENCIA = "TRANSFERENCIA"
    AJUSTE = "AJUSTE"
    TIPOS = [(ENTRADA, "Entrada"), (SALIDA, "Salida"), (TRANSFERENCIA, "Transferencia"), (AJUSTE, "Ajuste")]

    tipo = models.CharField(max_length=13, choices=TIPOS, db_index=True)
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name="movimientos")
    ubicacion_origen = models.ForeignKey(Ubicacion, on_delete=models.PROTECT, null=True, blank=True,
                                         related_name="movimientos_salida")
    ubicacion_destino = models.ForeignKey(Ubicacion, on_delete=models.PROTECT, null=True, blank=True,
                                          related_name="movimientos_entrada")
    cantidad = models.IntegerField(help_text="Cajas; en los ajustes puede ser negativa.")
    motivo = models.TextField(blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="movimientos")
    fecha_hora = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "movimiento"
        verbose_name_plural = "movimientos"
        ordering = ["-fecha_hora", "-id"]

    def __str__(self):
        return f"{self.get_tipo_display()} {self.cantidad} cajas - {self.lote.numero_lote}"
