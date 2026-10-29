import math

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


class Ubicacion(models.Model):
    """Posición física del almacén identificada por zona, nivel y posición, con QR único (RN-06)."""

    zona = models.CharField(max_length=10, validators=[RegexValidator(r"^[A-Z0-9]{1,10}$", "Use letras mayúsculas o números.")])
    nivel = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    posicion = models.PositiveSmallIntegerField("posición", validators=[MinValueValidator(1)])
    codigo_qr = models.CharField("código QR", max_length=30, unique=True, editable=False)
    capacidad_pallets = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "ubicación"
        verbose_name_plural = "ubicaciones"
        ordering = ["zona", "nivel", "posicion"]
        constraints = [
            models.UniqueConstraint(fields=["zona", "nivel", "posicion"], name="ubicacion_unica_zona_nivel_posicion"),
        ]

    def __str__(self):
        return self.codigo_qr or f"{self.zona}-{self.nivel}-{self.posicion:02d}"

    @staticmethod
    def armar_codigo(zona, nivel, posicion):
        return f"ISM-{zona}-{nivel}-{posicion:02d}"

    def save(self, *args, **kwargs):
        self.zona = self.zona.upper()
        self.codigo_qr = self.armar_codigo(self.zona, self.nivel, self.posicion)
        super().save(*args, **kwargs)

    def pallets_ocupados(self, excluir_stock=None):
        """Pallets ocupados: cada lote ocupa ceil(cajas / cajas_por_pallet) pallets."""
        total = 0
        stocks = self.stocks.filter(cantidad_cajas__gt=0).select_related("lote__producto")
        if excluir_stock is not None:
            stocks = stocks.exclude(pk=excluir_stock)
        for s in stocks:
            total += math.ceil(s.cantidad_cajas / s.lote.producto.cajas_por_pallet)
        return total

    @property
    def porcentaje_ocupacion(self):
        return min(100, round(self.pallets_ocupados() * 100 / self.capacidad_pallets))
