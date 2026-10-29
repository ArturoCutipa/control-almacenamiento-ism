"""Control de acceso por rol (RF-02, RNF-04)."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .models import Rol

ADMIN, ENCARGADO, OPERARIO, PLANIFICACION = Rol.ADMIN, Rol.ENCARGADO, Rol.OPERARIO, Rol.PLANIFICACION
TODOS = (ADMIN, ENCARGADO, OPERARIO, PLANIFICACION)


def rol_requerido(*codigos):
    """Decorador para vistas de función: exige sesión iniciada y uno de los roles indicados."""

    def decorador(vista):
        @wraps(vista)
        @login_required
        def envoltura(request, *args, **kwargs):
            if not request.user.tiene_rol(*codigos):
                raise PermissionDenied("Su rol no tiene acceso a esta opción.")
            return vista(request, *args, **kwargs)

        return envoltura

    return decorador


class RolRequeridoMixin(LoginRequiredMixin):
    """Equivalente para vistas basadas en clases."""

    roles = TODOS

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.tiene_rol(*self.roles):
            raise PermissionDenied("Su rol no tiene acceso a esta opción.")
        return super().dispatch(request, *args, **kwargs)
