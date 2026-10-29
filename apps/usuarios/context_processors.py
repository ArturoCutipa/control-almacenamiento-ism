from .models import Rol


def rol_usuario(request):
    """Expone el rol del usuario a las plantillas para armar el menú."""
    user = getattr(request, "user", None)
    codigo = user.codigo_rol if user is not None and user.is_authenticated else None
    return {
        "ROL": codigo,
        "ES_ADMIN": codigo == Rol.ADMIN,
        "ES_ENCARGADO": codigo in (Rol.ENCARGADO, Rol.ADMIN),
        "ES_OPERARIO": codigo in (Rol.OPERARIO, Rol.ENCARGADO, Rol.ADMIN),
        "ES_PLANIFICACION": codigo in (Rol.PLANIFICACION, Rol.ENCARGADO, Rol.ADMIN),
    }
