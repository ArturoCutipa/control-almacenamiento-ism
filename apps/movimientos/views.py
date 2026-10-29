from datetime import datetime

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from apps.inventario.excepciones import ReglaNegocioError
from apps.inventario.models import Stock
from apps.ubicaciones.models import Ubicacion
from apps.usuarios.permisos import ADMIN, ENCARGADO, OPERARIO, TODOS, rol_requerido

from . import services
from .forms import ConfirmarSalidaForm, SolicitudSalidaForm, TransferenciaForm
from .models import Movimiento


@rol_requerido(OPERARIO, ENCARGADO, ADMIN)
def salida(request):
    """Paso 1: producto y cantidad. Paso 2: el sistema sugiere el lote FEFO y el operario confirma con el QR."""
    if request.method == "POST" and "stock" in request.POST:
        confirmar = ConfirmarSalidaForm(request.POST)
        if confirmar.is_valid():
            d = confirmar.cleaned_data
            stock = Stock.objects.select_related("ubicacion", "lote").filter(pk=d["stock"]).first()
            if not stock:
                messages.error(request, "El stock seleccionado ya no existe.")
                return redirect("movimientos:salida")
            if d["qr_ubicacion"].strip().upper() != stock.ubicacion.codigo_qr:
                messages.error(request, f"El QR escaneado no corresponde a la ubicación {stock.ubicacion.codigo_qr}.")
            else:
                try:
                    services.registrar_salida(stock=stock, cantidad=d["cantidad"], usuario=request.user,
                                              motivo=d["motivo"])
                    messages.success(request, f"Salida registrada: {d['cantidad']} cajas del lote "
                                              f"{stock.lote.numero_lote} desde {stock.ubicacion.codigo_qr}.")
                    return redirect("movimientos:salida")
                except ReglaNegocioError as e:
                    messages.error(request, str(e))
            producto, cantidad = stock.lote.producto, d["cantidad"]
            sugerido, candidatos = services.sugerir(producto, cantidad)
            return render(request, "movimientos/salida_confirmar.html", {
                "producto": producto, "cantidad": cantidad, "sugerido": sugerido, "candidatos": candidatos,
                "seleccionado": stock.pk, "form": confirmar})
        messages.error(request, "Complete los datos de la salida.")
        return redirect("movimientos:salida")

    form = SolicitudSalidaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        producto, cantidad = form.producto, form.cleaned_data["cantidad"]
        sugerido, candidatos = services.sugerir(producto, cantidad)
        if not sugerido:
            messages.error(request, f"No hay stock disponible de {producto}.")
        else:
            confirmar = ConfirmarSalidaForm(initial={"stock": sugerido.pk, "cantidad": cantidad})
            return render(request, "movimientos/salida_confirmar.html", {
                "producto": producto, "cantidad": cantidad, "sugerido": sugerido, "candidatos": candidatos,
                "seleccionado": sugerido.pk, "form": confirmar})
    return render(request, "movimientos/salida.html", {"form": form})


@rol_requerido(OPERARIO, ENCARGADO, ADMIN)
def transferencia(request):
    form = TransferenciaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        origen = Ubicacion.objects.filter(codigo_qr=d["qr_origen"].strip().upper()).first()
        destino = Ubicacion.objects.filter(codigo_qr=d["qr_destino"].strip().upper(), activa=True).first()
        stock = None
        if origen:
            stock = Stock.objects.filter(ubicacion=origen, lote__numero_lote=d["numero_lote"].strip().upper()).first()
        if not origen or not destino:
            messages.error(request, "QR de ubicación no válido.")
        elif not stock:
            messages.error(request, f"El lote {d['numero_lote']} no tiene stock en {origen.codigo_qr}.")
        else:
            try:
                services.transferir(stock=stock, destino=destino, cantidad=d["cantidad"], usuario=request.user,
                                    motivo=d["motivo"])
                messages.success(request, f"Transferencia registrada: {d['cantidad']} cajas a {destino.codigo_qr}.")
                return redirect("movimientos:transferencia")
            except ReglaNegocioError as e:
                messages.error(request, str(e))
    return render(request, "movimientos/transferencia.html", {"form": form})


@rol_requerido(*TODOS)
def historial(request):
    movs = Movimiento.objects.select_related("lote__producto", "usuario", "ubicacion_origen", "ubicacion_destino")
    f = {k: request.GET.get(k, "").strip() for k in ("tipo", "desde", "hasta", "q")}
    if f["tipo"]:
        movs = movs.filter(tipo=f["tipo"])
    if f["desde"]:
        movs = movs.filter(fecha_hora__date__gte=datetime.strptime(f["desde"], "%Y-%m-%d").date())
    if f["hasta"]:
        movs = movs.filter(fecha_hora__date__lte=datetime.strptime(f["hasta"], "%Y-%m-%d").date())
    if f["q"]:
        movs = movs.filter(lote__numero_lote__icontains=f["q"]) | movs.filter(lote__producto__codigo_barras=f["q"])
    pagina = Paginator(movs, 50).get_page(request.GET.get("page"))
    return render(request, "movimientos/historial.html", {"pagina": pagina, "filtros": f, "tipos": Movimiento.TIPOS})
