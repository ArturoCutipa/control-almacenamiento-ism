from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.inventario.excepciones import ReglaNegocioError
from apps.inventario.models import Lote
from apps.ubicaciones.models import Ubicacion
from apps.usuarios.permisos import ADMIN, ENCARGADO, OPERARIO, rol_requerido

from . import services
from .forms import AbrirConteoForm, RegistroConteoForm, RevisionForm
from .models import Conteo, DetalleConteo


@rol_requerido(OPERARIO, ENCARGADO, ADMIN)
def lista(request):
    form = AbrirConteoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        conteo = services.abrir_conteo(request.user, form.cleaned_data["descripcion"])
        return redirect("conteos:detalle", pk=conteo.pk)
    conteos = Conteo.objects.select_related("usuario")[:30]
    pendientes = DetalleConteo.objects.filter(estado=DetalleConteo.PENDIENTE).count()
    return render(request, "conteos/lista.html", {"form": form, "conteos": conteos, "pendientes": pendientes})


@rol_requerido(OPERARIO, ENCARGADO, ADMIN)
def detalle(request, pk):
    conteo = get_object_or_404(Conteo, pk=pk)
    form = RegistroConteoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        ubicacion = Ubicacion.objects.filter(codigo_qr=d["qr_ubicacion"].strip().upper()).first()
        lote = Lote.objects.filter(numero_lote=d["numero_lote"].strip().upper(),
                                   producto__codigo_barras=d["codigo_barras"].strip()).first()
        if not ubicacion:
            messages.error(request, "QR de ubicación no válido.")
        elif not lote:
            messages.error(request, "El lote no está registrado para ese producto.")
        else:
            try:
                det = services.registrar_conteo(conteo=conteo, ubicacion=ubicacion, lote=lote,
                                                cant_fisica=d["cant_fisica"], usuario=request.user)
                if det.diferencia:
                    messages.warning(request, f"Diferencia de {det.diferencia:+d} cajas registrada; "
                                              "queda pendiente de aprobación del Encargado.")
                else:
                    messages.success(request, "Conteo conciliado: coincide con el sistema.")
                return redirect("conteos:detalle", pk=pk)
            except ReglaNegocioError as e:
                messages.error(request, str(e))
    detalles = conteo.detalles.select_related("lote__producto", "ubicacion", "revisado_por")
    return render(request, "conteos/detalle.html", {"conteo": conteo, "form": form, "detalles": detalles,
                                                    "revision": RevisionForm()})


@require_POST
@rol_requerido(ENCARGADO, ADMIN)
def revisar(request, pk):
    det = get_object_or_404(DetalleConteo, pk=pk)
    form = RevisionForm(request.POST)
    form.is_valid()
    motivo = form.cleaned_data.get("motivo", "")
    try:
        if request.POST.get("accion") == "aprobar":
            services.aprobar_ajuste(detalle=det, motivo=motivo, encargado=request.user)
            messages.success(request, f"Ajuste aprobado: {det.diferencia:+d} cajas del lote {det.lote.numero_lote}.")
        else:
            services.rechazar_ajuste(detalle=det, motivo=motivo, encargado=request.user)
            messages.info(request, "Ajuste rechazado; se solicita reconteo.")
    except ReglaNegocioError as e:
        messages.error(request, str(e))
    return redirect("conteos:detalle", pk=det.conteo_id)


@require_POST
@rol_requerido(ENCARGADO, ADMIN)
def cerrar(request, pk):
    conteo = get_object_or_404(Conteo, pk=pk)
    try:
        services.cerrar_conteo(conteo, request.user)
        messages.success(request, f"{conteo} cerrado.")
    except ReglaNegocioError as e:
        messages.error(request, str(e))
    return redirect("conteos:detalle", pk=pk)
