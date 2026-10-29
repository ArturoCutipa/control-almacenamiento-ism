from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.inventario.excepciones import ReglaNegocioError
from apps.ubicaciones.models import Ubicacion
from apps.usuarios.permisos import ADMIN, ENCARGADO, OPERARIO, rol_requerido

from . import services
from .forms import NuevaRecepcionForm, PalletForm, UbicarForm
from .models import DetalleRecepcion, Recepcion

ROLES = (OPERARIO, ENCARGADO, ADMIN)


@rol_requerido(*ROLES)
def lista(request):
    form = NuevaRecepcionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            recepcion = services.iniciar_recepcion(form.cleaned_data["guia_remision"], request.user)
            return redirect("recepcion:detalle", pk=recepcion.pk)
        except ReglaNegocioError as e:
            messages.error(request, str(e))
    recepciones = Recepcion.objects.select_related("usuario").prefetch_related("detalles")[:30]
    return render(request, "recepcion/lista.html", {"form": form, "recepciones": recepciones})


@rol_requerido(*ROLES)
def detalle(request, pk):
    recepcion = get_object_or_404(Recepcion, pk=pk)
    form = PalletForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            det = services.registrar_pallet(recepcion=recepcion, producto=form.producto, numero_lote=d["numero_lote"],
                                            fecha_vencimiento=d["fecha_vencimiento"], cantidad_cajas=d["cantidad_cajas"],
                                            usuario=request.user)
            messages.success(request, f"Pallet registrado: {det.cantidad_cajas} cajas, lote {det.lote.numero_lote}. "
                                      "Ahora escanee el QR de su ubicación.")
            return redirect("recepcion:ubicar", pk=det.pk)
        except ReglaNegocioError as e:
            messages.error(request, str(e))
    detalles = recepcion.detalles.select_related("lote__producto", "ubicacion")
    return render(request, "recepcion/detalle.html", {"recepcion": recepcion, "form": form, "detalles": detalles})


@rol_requerido(*ROLES)
def ubicar(request, pk):
    det = get_object_or_404(DetalleRecepcion.objects.select_related("lote__producto", "recepcion"), pk=pk)
    if det.ubicado:
        messages.info(request, f"Este pallet ya está en {det.ubicacion.codigo_qr}.")
        return redirect("recepcion:detalle", pk=det.recepcion_id)
    form = UbicarForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        codigo = form.cleaned_data["qr_ubicacion"].strip().upper()
        ubicacion = Ubicacion.objects.filter(codigo_qr=codigo).first()
        if not ubicacion:
            messages.error(request, "QR de ubicación no válido. Escanee nuevamente.")
        else:
            try:
                services.asignar_ubicacion(detalle=det, ubicacion=ubicacion, usuario=request.user)
                messages.success(request, f"Lote {det.lote.numero_lote} ubicado en {ubicacion.codigo_qr}.")
                return redirect("recepcion:detalle", pk=det.recepcion_id)
            except ReglaNegocioError as e:
                messages.error(request, str(e))
    return render(request, "recepcion/ubicar.html", {"det": det, "form": form})


@require_POST
@rol_requerido(*ROLES)
def finalizar(request, pk):
    recepcion = get_object_or_404(Recepcion, pk=pk)
    try:
        services.finalizar_recepcion(recepcion, request.user)
        messages.success(request, f"Recepción de la guía {recepcion.guia_remision} finalizada en "
                                  f"{recepcion.duracion_min()} minutos.")
        return redirect("recepcion:lista")
    except ReglaNegocioError as e:
        messages.error(request, str(e))
        return redirect("recepcion:detalle", pk=pk)
