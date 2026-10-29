from .models import Bitacora


def registrar(usuario, accion, detalle=""):
    """Agrega una operación a la bitácora. `usuario` puede ser None para tareas del sistema."""
    if usuario is not None and not getattr(usuario, "is_authenticated", False):
        usuario = None
    return Bitacora.objects.create(usuario=usuario, accion=accion, detalle=detalle[:2000])
