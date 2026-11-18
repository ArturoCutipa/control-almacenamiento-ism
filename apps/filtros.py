"""Lectura segura de los parámetros de filtro que llegan por GET."""
from datetime import datetime


def fecha_iso(valor, defecto=None):
    """Convierte 'AAAA-MM-DD' en fecha; si el valor falta o no es válido, devuelve `defecto`."""
    try:
        return datetime.strptime((valor or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return defecto


def entero(valor, defecto=None):
    """Convierte el valor en entero positivo; si no es válido, devuelve `defecto`."""
    try:
        numero = int((valor or "").strip())
    except ValueError:
        return defecto
    return numero if numero > 0 else defecto
