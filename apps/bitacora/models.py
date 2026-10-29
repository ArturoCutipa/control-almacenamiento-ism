from django.conf import settings
from django.db import models


class BitacoraInmutableError(Exception):
    pass


class Bitacora(models.Model):
    """Registro de auditoría de todas las operaciones (RF-17). No se edita ni se elimina (RN-14)."""

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
                                related_name="+")
    accion = models.CharField(max_length=40, db_index=True)
    detalle = models.TextField(blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "registro de bitácora"
        verbose_name_plural = "bitácora"
        ordering = ["-fecha_hora", "-id"]

    def __str__(self):
        return f"{self.fecha_hora:%d/%m/%Y %H:%M} {self.accion}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise BitacoraInmutableError("Los registros de la bitácora no se pueden modificar (RN-14).")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise BitacoraInmutableError("Los registros de la bitácora no se pueden eliminar (RN-14).")
