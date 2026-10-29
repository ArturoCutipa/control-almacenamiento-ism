from django.conf import settings
from django.db import models


class ExportacionSAP(models.Model):
    """Archivo de carga generado para SAP (RF-18). El sistema no escribe en SAP (RN-15)."""

    fecha_corte = models.DateField("fecha de corte")
    fecha_hora = models.DateTimeField(auto_now_add=True)
    archivo = models.FileField(upload_to="exportaciones_sap/%Y/%m/")
    total_registros = models.PositiveIntegerField(default=0)
    total_cajas = models.PositiveIntegerField(default=0)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="exportaciones_sap")

    class Meta:
        verbose_name = "exportación a SAP"
        verbose_name_plural = "exportaciones a SAP"
        ordering = ["-fecha_hora"]

    def __str__(self):
        return f"Exportación SAP al {self.fecha_corte:%d/%m/%Y}"
