from django.conf import settings
from django.db import models

from apps.inventario.models import Lote
from apps.ubicaciones.models import Ubicacion


class Recepcion(models.Model):
    """Recepción de un camión identificada por su guía de remisión (RF-07)."""

    guia_remision = models.CharField("guía de remisión", max_length=30)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="recepciones")
    fecha_hora_inicio = models.DateTimeField(auto_now_add=True)
    fecha_hora_fin = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "recepción"
        verbose_name_plural = "recepciones"
        ordering = ["-fecha_hora_inicio"]

    def __str__(self):
        return f"Guía {self.guia_remision}"

    @property
    def finalizada(self):
        return self.fecha_hora_fin is not None

    def duracion_min(self):
        if not self.fecha_hora_fin:
            return None
        return round((self.fecha_hora_fin - self.fecha_hora_inicio).total_seconds() / 60, 1)


class DetalleRecepcion(models.Model):
    recepcion = models.ForeignKey(Recepcion, on_delete=models.CASCADE, related_name="detalles")
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name="detalles_recepcion")
    cantidad_cajas = models.PositiveIntegerField()
    pallets = models.PositiveSmallIntegerField()
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT, null=True, blank=True,
                                  related_name="detalles_recepcion")
    registrado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "detalle de recepción"
        verbose_name_plural = "detalles de recepción"
        ordering = ["registrado"]

    def __str__(self):
        return f"{self.lote.numero_lote}: {self.cantidad_cajas} cajas"

    @property
    def ubicado(self):
        return self.ubicacion_id is not None
