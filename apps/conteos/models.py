from django.conf import settings
from django.db import models

from apps.inventario.models import Lote, Stock
from apps.ubicaciones.models import Ubicacion


class Conteo(models.Model):
    ABIERTO = "ABIERTO"
    CERRADO = "CERRADO"
    ESTADOS = [(ABIERTO, "Abierto"), (CERRADO, "Cerrado")]

    descripcion = models.CharField("descripción", max_length=120, blank=True)
    fecha = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=12, choices=ESTADOS, default=ABIERTO)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="conteos")

    class Meta:
        verbose_name = "conteo"
        verbose_name_plural = "conteos"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"Conteo {self.id} del {self.fecha:%d/%m/%Y}"

    @property
    def pendientes(self):
        return self.detalles.filter(estado=DetalleConteo.PENDIENTE).count()


class DetalleConteo(models.Model):
    PENDIENTE = "PENDIENTE"
    CONCILIADO = "CONCILIADO"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"
    ESTADOS = [(PENDIENTE, "Pendiente de aprobación"), (CONCILIADO, "Sin diferencia"),
               (APROBADO, "Ajuste aprobado"), (RECHAZADO, "Rechazado (reconteo)")]

    conteo = models.ForeignKey(Conteo, on_delete=models.CASCADE, related_name="detalles")
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name="detalles_conteo")
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT, related_name="detalles_conteo")
    stock = models.ForeignKey(Stock, on_delete=models.PROTECT, null=True, blank=True, related_name="detalles_conteo")
    cant_sistema = models.IntegerField("cantidad en sistema")
    cant_fisica = models.PositiveIntegerField("cantidad contada")
    diferencia = models.IntegerField()
    estado = models.CharField(max_length=12, choices=ESTADOS, default=PENDIENTE, db_index=True)
    motivo = models.TextField(blank=True)
    contado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    revisado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
                                     related_name="+")
    fecha_revision = models.DateTimeField(null=True, blank=True)
    registrado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "detalle de conteo"
        verbose_name_plural = "detalles de conteo"
        ordering = ["registrado"]

    def __str__(self):
        return f"{self.lote.numero_lote} en {self.ubicacion}: {self.diferencia:+d}"
