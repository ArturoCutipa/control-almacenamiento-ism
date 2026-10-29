from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


class Producto(models.Model):
    """Producto identificado por el código de barras que trae de fábrica (RN-03)."""

    codigo_barras = models.CharField(
        "código de barras", max_length=20, unique=True,
        validators=[RegexValidator(r"^\d{8,14}$", "El código de barras debe tener entre 8 y 14 dígitos.")])
    descripcion = models.CharField("descripción", max_length=150)
    marca = models.CharField(max_length=60)
    sabor = models.CharField(max_length=60)
    formato = models.CharField(max_length=60, help_text="Ej.: 625 ml x 15")
    cajas_por_pallet = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "producto"
        verbose_name_plural = "productos"
        ordering = ["marca", "sabor", "formato"]

    def __str__(self):
        return f"{self.marca} {self.sabor} {self.formato}"
