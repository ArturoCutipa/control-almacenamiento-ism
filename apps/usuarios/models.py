from django.contrib.auth.models import AbstractUser
from django.db import models


class Rol(models.Model):
    ADMIN = "ADMIN"
    ENCARGADO = "ENCARGADO"
    OPERARIO = "OPERARIO"
    PLANIFICACION = "PLANIFICACION"
    CODIGOS = [
        (ADMIN, "Administrador"),
        (ENCARGADO, "Encargado de almacén"),
        (OPERARIO, "Operario de almacén"),
        (PLANIFICACION, "Planificación / Comercial"),
    ]

    codigo = models.CharField(max_length=20, choices=CODIGOS, unique=True)
    nombre = models.CharField(max_length=40, unique=True)

    class Meta:
        verbose_name = "rol"
        verbose_name_plural = "roles"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    """Usuario del sistema; cada usuario tiene un único rol (RN-02)."""

    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, null=True, blank=True, related_name="usuarios")

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["username"]

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def codigo_rol(self):
        if self.is_superuser and not self.rol_id:
            return Rol.ADMIN
        return self.rol.codigo if self.rol_id else None

    def tiene_rol(self, *codigos):
        return self.is_superuser or self.codigo_rol in codigos
