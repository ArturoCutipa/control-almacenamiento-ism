"""Salidas con rotación FEFO/FIFO (RF-10) y transferencias internas (RF-11)."""
from django.db import transaction
from django.utils import timezone

from apps.bitacora.services import registrar
from apps.inventario import services as inventario
from apps.inventario.excepciones import LoteNoDisponibleError, ReglaNegocioError
from apps.inventario.models import Lote, Stock

from .models import Movimiento


def candidatos_fefo(producto, hoy=None):
    """Stock disponible del producto ordenado por FEFO; a igual vencimiento, por FIFO (RN-08)."""
    hoy = hoy or timezone.localdate()
    return (Stock.objects.filter(lote__producto=producto, lote__estado=Lote.DISPONIBLE,
                                 lote__fecha_vencimiento__gte=hoy, cantidad_cajas__gt=0)
            .select_related("lote", "ubicacion")
            .order_by("lote__fecha_vencimiento", "lote__creado", "lote__id", "ubicacion__codigo_qr"))


def sugerir(producto, cantidad, hoy=None):
    """Stock sugerido: el primero en orden FEFO que cubre toda la cantidad; si ninguno la cubre, el primero."""
    candidatos = list(candidatos_fefo(producto, hoy))
    if not candidatos:
        return None, []
    sugerido = next((s for s in candidatos if s.cantidad_cajas >= cantidad), candidatos[0])
    return sugerido, candidatos


@transaction.atomic
def registrar_salida(*, stock, cantidad, usuario, motivo="", hoy=None):
    """RF-10 / RN-09: si no se despacha el lote sugerido por FEFO, el motivo es obligatorio."""
    stock = Stock.objects.select_related("lote__producto", "ubicacion").get(pk=stock.pk)
    lote = stock.lote
    if lote.estado != Lote.DISPONIBLE or lote.esta_vencido(hoy):
        raise LoteNoDisponibleError(f"El lote {lote.numero_lote} no está disponible para despacho (RN-12).")
    sugerido, _ = sugerir(lote.producto, cantidad, hoy)
    motivo = (motivo or "").strip()
    salta_fefo = sugerido and lote.fecha_vencimiento > sugerido.lote.fecha_vencimiento
    if salta_fefo and not motivo:
        raise ReglaNegocioError(
            f"Debe indicar el motivo para no despachar el lote sugerido {sugerido.lote.numero_lote} (RN-09).")
    inventario.descontar(lote, stock.ubicacion, cantidad)
    mov = Movimiento.objects.create(tipo=Movimiento.SALIDA, lote=lote, ubicacion_origen=stock.ubicacion,
                                    cantidad=cantidad, motivo=motivo, usuario=usuario)
    registrar(usuario, "SALIDA", f"{cantidad} cajas lote {lote.numero_lote} desde {stock.ubicacion.codigo_qr}"
              + (f" - motivo: {motivo}" if motivo else ""))
    return mov


@transaction.atomic
def transferir(*, stock, destino, cantidad, usuario, motivo=""):
    """RF-11: mueve cajas de un lote entre ubicaciones validando stock y capacidad."""
    stock = Stock.objects.select_related("lote__producto", "ubicacion").get(pk=stock.pk)
    if destino.pk == stock.ubicacion_id:
        raise ReglaNegocioError("La ubicación de destino debe ser distinta a la de origen.")
    inventario.descontar(stock.lote, stock.ubicacion, cantidad)
    inventario.incrementar(stock.lote, destino, cantidad)
    mov = Movimiento.objects.create(tipo=Movimiento.TRANSFERENCIA, lote=stock.lote, ubicacion_origen=stock.ubicacion,
                                    ubicacion_destino=destino, cantidad=cantidad, motivo=motivo, usuario=usuario)
    registrar(usuario, "TRANSFERENCIA",
              f"{cantidad} cajas lote {stock.lote.numero_lote} de {stock.ubicacion.codigo_qr} a {destino.codigo_qr}")
    return mov
