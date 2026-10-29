from django.conf import settings
from django.db import models

from apps.inventario.models import Lote


class Alerta(models.Model):
    POR_VENCER = "POR_VENCER"
    VENCIDO = "VENCIDO"
    TIPOS = [(POR_VENCER, "Próximo a vencer"), (VENCIDO, "Vencido")]

    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name="alertas")
    tipo = models.CharField(max_length=12, choices=TIPOS)
    dias_restantes = models.IntegerField()
    cajas = models.PositiveIntegerField(default=0)
    fecha = models.DateField(auto_now_add=True)
    atendida = models.BooleanField(default=False, db_index=True)
    atendida_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
                                     related_name="+")
    comentario = models.TextField(blank=True)

    class Meta:
        verbose_name = "alerta"
        verbose_name_plural = "alertas"
        ordering = ["atendida", "dias_restantes"]
        constraints = [
            models.UniqueConstraint(fields=["lote", "tipo"], condition=models.Q(atendida=False),
                                    name="una_alerta_abierta_por_lote_y_tipo"),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.lote} ({self.dias_restantes} días)"
