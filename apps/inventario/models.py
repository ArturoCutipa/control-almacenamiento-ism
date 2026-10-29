from django.db import models
from django.utils import timezone

from apps.catalogo.models import Producto
from apps.ubicaciones.models import Ubicacion


class Lote(models.Model):
    DISPONIBLE = "DISPONIBLE"
    BLOQUEADO = "BLOQUEADO"
    VENCIDO = "VENCIDO"
    ESTADOS = [(DISPONIBLE, "Disponible"), (BLOQUEADO, "Bloqueado"), (VENCIDO, "Vencido")]

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="lotes")
    numero_lote = models.CharField("número de lote", max_length=30)
    fecha_vencimiento = models.DateField("fecha de vencimiento", db_index=True)
    estado = models.CharField(max_length=12, choices=ESTADOS, default=DISPONIBLE, db_index=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "lote"
        verbose_name_plural = "lotes"
        ordering = ["fecha_vencimiento", "creado"]
        constraints = [
            models.UniqueConstraint(fields=["producto", "numero_lote"], name="lote_unico_por_producto"),
        ]

    def __str__(self):
        return f"{self.numero_lote} ({self.producto})"

    def dias_para_vencer(self, hoy=None):
        hoy = hoy or timezone.localdate()
        return (self.fecha_vencimiento - hoy).days

    def esta_vencido(self, hoy=None):
        return self.dias_para_vencer(hoy) < 0

    @property
    def total_cajas(self):
        return sum(s.cantidad_cajas for s in self.stocks.all())


class Stock(models.Model):
    """Cajas de un lote en una ubicación. Único por lote y ubicación; nunca negativo (RNF-05, RN-10)."""

    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name="stocks")
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT, related_name="stocks")
    cantidad_cajas = models.PositiveIntegerField(default=0)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "stock"
        verbose_name_plural = "stock"
        ordering = ["lote__fecha_vencimiento", "ubicacion__codigo_qr"]
        constraints = [
            models.UniqueConstraint(fields=["lote", "ubicacion"], name="stock_unico_lote_ubicacion"),
            models.CheckConstraint(condition=models.Q(cantidad_cajas__gte=0), name="stock_no_negativo"),
        ]

    def __str__(self):
        return f"{self.lote.numero_lote} en {self.ubicacion}: {self.cantidad_cajas} cajas"
