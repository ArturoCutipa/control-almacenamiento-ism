"""Auditoría de accesos (RF-17): los intentos fallidos de inicio de sesión quedan en la bitácora."""
from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver

from apps.bitacora.services import registrar


@receiver(user_login_failed)
def registrar_login_fallido(sender, credentials, request=None, **kwargs):
    usuario = (credentials or {}).get("username", "")[:150]  # nunca se guarda la contraseña
    ip = request.META.get("REMOTE_ADDR", "") if request is not None else ""
    registrar(None, "INICIO_FALLIDO", f"Usuario '{usuario}'" + (f" desde {ip}" if ip else ""))
