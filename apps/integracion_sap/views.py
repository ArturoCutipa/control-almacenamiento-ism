from datetime import datetime

from django.contrib import messages
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.usuarios.permisos import ADMIN, ENCARGADO, rol_requerido

from . import services
from .models import ExportacionSAP


@rol_requerido(ENCARGADO, ADMIN)
def exportar(request):
    hoy = timezone.localdate()
    if request.method == "POST":
        try:
            fecha = datetime.strptime(request.POST.get("fecha_corte", ""), "%Y-%m-%d").date()
        except ValueError:
            fecha = None
        if not fecha or fecha > hoy:
            messages.error(request, "Ingrese una fecha de corte válida (no futura).")
        elif services.conteos_pendientes() and not request.POST.get("confirmar"):
            messages.warning(request, f"Hay {services.conteos_pendientes()} diferencias de conteo pendientes de "
                                      "aprobación. Marque la confirmación para exportar de todas formas.")
        else:
            exp = services.generar_archivo(fecha, request.user)
            messages.success(request, f"Archivo generado: {exp.total_registros} lotes, {exp.total_cajas} cajas.")
            return redirect("integracion_sap:exportar")
    contexto = {
        "hoy": hoy, "pendientes": services.conteos_pendientes(),
        "vista_previa": services.inventario_consolidado(hoy)[:15],
        "exportaciones": ExportacionSAP.objects.select_related("usuario")[:20],
    }
    return render(request, "integracion_sap/exportar.html", contexto)


@rol_requerido(ENCARGADO, ADMIN)
def descargar(request, pk):
    exp = get_object_or_404(ExportacionSAP, pk=pk)
    if not exp.archivo:
        raise Http404
    return FileResponse(exp.archivo.open("rb"), as_attachment=True, filename=exp.archivo.name.split("/")[-1])
