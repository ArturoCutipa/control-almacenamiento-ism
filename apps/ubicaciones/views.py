from collections import OrderedDict

from django.contrib import messages
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.bitacora.services import registrar
from apps.usuarios.permisos import ADMIN, ENCARGADO, TODOS, rol_requerido

from .forms import UbicacionForm
from .models import Ubicacion
from .services import pdf_etiquetas


@rol_requerido(*TODOS)
def lista(request):
    zona = request.GET.get("zona", "").strip().upper()
    ubicaciones = Ubicacion.objects.all()
    if zona:
        ubicaciones = ubicaciones.filter(zona=zona)
    zonas = Ubicacion.objects.order_by("zona").values_list("zona", flat=True).distinct()
    return render(request, "ubicaciones/lista.html", {"ubicaciones": ubicaciones, "zonas": zonas, "zona": zona})


@rol_requerido(ADMIN, ENCARGADO)
def editar(request, pk=None):
    ubicacion = get_object_or_404(Ubicacion, pk=pk) if pk else None
    form = UbicacionForm(request.POST or None, instance=ubicacion)
    if request.method == "POST" and form.is_valid():
        ubicacion = form.save()
        registrar(request.user, "UBICACION_GUARDADA", f"{ubicacion.codigo_qr} capacidad {ubicacion.capacidad_pallets}")
        messages.success(request, f"Ubicación {ubicacion.codigo_qr} guardada.")
        return redirect("ubicaciones:lista")
    return render(request, "ubicaciones/form.html", {"form": form, "ubicacion": ubicacion})


@rol_requerido(ADMIN, ENCARGADO)
def etiquetas(request):
    """PDF de etiquetas QR de las ubicaciones seleccionadas o de una zona."""
    ids = request.GET.getlist("id")
    zona = request.GET.get("zona", "").strip().upper()
    ubicaciones = Ubicacion.objects.filter(activa=True)
    if ids:
        ubicaciones = ubicaciones.filter(pk__in=ids)
    elif zona:
        ubicaciones = ubicaciones.filter(zona=zona)
    ubicaciones = list(ubicaciones)
    if not ubicaciones:
        messages.error(request, "No hay ubicaciones para imprimir.")
        return redirect("ubicaciones:lista")
    registrar(request.user, "ETIQUETAS_QR", f"{len(ubicaciones)} etiquetas")
    return FileResponse(pdf_etiquetas(ubicaciones), as_attachment=False, filename="etiquetas_qr_ism.pdf",
                        content_type="application/pdf")


@rol_requerido(*TODOS)
def mapa(request):
    """Mapa de ocupación por zona, nivel y posición (RF-13)."""
    zonas = OrderedDict()
    for u in Ubicacion.objects.filter(activa=True).prefetch_related("stocks__lote__producto"):
        niveles = zonas.setdefault(u.zona, OrderedDict())
        niveles.setdefault(u.nivel, []).append(u)
    for niveles in zonas.values():
        for nivel in niveles:
            niveles[nivel].sort(key=lambda x: x.posicion)
    zonas = {z: OrderedDict(sorted(n.items(), reverse=True)) for z, n in zonas.items()}
    return render(request, "ubicaciones/mapa.html", {"zonas": zonas})


@rol_requerido(*TODOS)
def buscar_qr(request):
    """Identifica una ubicación a partir del QR escaneado (JSON)."""
    codigo = request.GET.get("codigo", "").strip().upper()
    u = Ubicacion.objects.filter(codigo_qr=codigo, activa=True).first()
    if not u:
        return JsonResponse({"encontrada": False, "mensaje": "QR de ubicación no válido."}, status=404)
    return JsonResponse({"encontrada": True, "id": u.id, "codigo_qr": u.codigo_qr,
                         "capacidad": u.capacidad_pallets, "ocupados": u.pallets_ocupados()})
