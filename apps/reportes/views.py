from datetime import datetime, timedelta

from django.http import FileResponse, Http404
from django.shortcuts import render
from django.utils import timezone

from apps.bitacora.services import registrar
from apps.usuarios.permisos import ADMIN, ENCARGADO, PLANIFICACION, rol_requerido

from . import services


def _fecha(valor, defecto):
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return defecto


@rol_requerido(ENCARGADO, ADMIN, PLANIFICACION)
def reportes(request):
    hoy = timezone.localdate()
    tipo = request.GET.get("tipo", "movimientos")
    if tipo not in services.TIPOS:
        raise Http404
    desde = _fecha(request.GET.get("desde"), hoy - timedelta(days=30))
    hasta = _fecha(request.GET.get("hasta"), hoy)
    datos = services.generar(tipo, desde, hasta)
    formato = request.GET.get("formato")
    if formato in ("pdf", "xlsx"):
        registrar(request.user, "REPORTE", f"{datos['titulo']} ({formato}) {desde:%d/%m/%Y}-{hasta:%d/%m/%Y}")
        nombre = f"reporte_{tipo}_{desde:%Y%m%d}_{hasta:%Y%m%d}.{formato}"
        archivo = services.a_pdf(datos) if formato == "pdf" else services.a_excel(datos)
        return FileResponse(archivo, as_attachment=True, filename=nombre)
    return render(request, "reportes/reportes.html", {"datos": datos, "tipos": services.TIPOS})
