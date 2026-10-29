from datetime import datetime

from django.core.paginator import Paginator
from django.shortcuts import render

from apps.usuarios.models import Usuario
from apps.usuarios.permisos import ADMIN, ENCARGADO, rol_requerido

from .models import Bitacora


@rol_requerido(ADMIN, ENCARGADO)
def lista(request):
    registros = Bitacora.objects.select_related("usuario")
    f = {k: request.GET.get(k, "").strip() for k in ("desde", "hasta", "usuario", "accion")}
    if f["desde"]:
        registros = registros.filter(fecha_hora__date__gte=datetime.strptime(f["desde"], "%Y-%m-%d").date())
    if f["hasta"]:
        registros = registros.filter(fecha_hora__date__lte=datetime.strptime(f["hasta"], "%Y-%m-%d").date())
    if f["usuario"]:
        registros = registros.filter(usuario_id=f["usuario"])
    if f["accion"]:
        registros = registros.filter(accion=f["accion"])
    pagina = Paginator(registros, 50).get_page(request.GET.get("page"))
    acciones = Bitacora.objects.order_by("accion").values_list("accion", flat=True).distinct()
    return render(request, "bitacora/lista.html", {
        "pagina": pagina, "filtros": f, "usuarios": Usuario.objects.all(), "acciones": acciones,
    })
