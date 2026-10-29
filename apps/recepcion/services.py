"""Recepción desde tablet (RF-07, RF-08) y asignación de ubicación por QR (RF-09)."""
import math

from django.db import transaction
from django.utils import timezone

from apps.bitacora.services import registrar
from apps.inventario import services as inventario
from apps.inventario.excepciones import ReglaNegocioError
from apps.movimientos.models import Movimiento

from .models import DetalleRecepcion, Recepcion


def iniciar_recepcion(guia_remision, usuario):
    guia = guia_remision.strip().upper()
    if not guia:
        raise ReglaNegocioError("Ingrese el número de la guía de remisión.")
    recepcion = Recepcion.objects.create(guia_remision=guia, usuario=usuario)
    registrar(usuario, "RECEPCION_INICIADA", f"Guía {guia}")
    return recepcion


@transaction.atomic
def registrar_pallet(*, recepcion, producto, numero_lote, fecha_vencimiento, cantidad_cajas, usuario):
    """Registra un pallet (o grupo de pallets) del mismo lote. RN-04: lote, vencimiento y cantidad obligatorios."""
    if recepcion.finalizada:
        raise ReglaNegocioError("La recepción ya fue finalizada.")
    if not cantidad_cajas or cantidad_cajas <= 0:
        raise ReglaNegocioError("La cantidad de cajas debe ser mayor que cero.")
    lote = inventario.obtener_o_crear_lote(producto, numero_lote, fecha_vencimiento)
    detalle = DetalleRecepcion.objects.create(
        recepcion=recepcion, lote=lote, cantidad_cajas=cantidad_cajas,
        pallets=math.ceil(cantidad_cajas / producto.cajas_por_pallet))
    registrar(usuario, "RECEPCION_PALLET",
              f"Guía {recepcion.guia_remision}: {cantidad_cajas} cajas de {producto} lote {lote.numero_lote}")
    return detalle


@transaction.atomic
def asignar_ubicacion(*, detalle, ubicacion, usuario):
    """Ubica el pallet recibido: valida capacidad, suma stock y registra el movimiento de ENTRADA."""
    detalle = DetalleRecepcion.objects.select_for_update().select_related("lote__producto", "recepcion").get(pk=detalle.pk)
    if detalle.ubicado:
        raise ReglaNegocioError("Este pallet ya fue ubicado.")
    if not ubicacion.activa:
        raise ReglaNegocioError("La ubicación está inactiva.")
    inventario.incrementar(detalle.lote, ubicacion, detalle.cantidad_cajas)
    detalle.ubicacion = ubicacion
    detalle.save(update_fields=["ubicacion"])
    Movimiento.objects.create(tipo=Movimiento.ENTRADA, lote=detalle.lote, ubicacion_destino=ubicacion,
                              cantidad=detalle.cantidad_cajas, usuario=usuario,
                              motivo=f"Recepción guía {detalle.recepcion.guia_remision}")
    registrar(usuario, "ENTRADA", f"{detalle.cantidad_cajas} cajas lote {detalle.lote.numero_lote} en {ubicacion.codigo_qr}")
    return detalle


def finalizar_recepcion(recepcion, usuario):
    if recepcion.finalizada:
        return recepcion
    if not recepcion.detalles.exists():
        raise ReglaNegocioError("Registre al menos un pallet antes de finalizar.")
    pendientes = recepcion.detalles.filter(ubicacion__isnull=True).count()
    if pendientes:
        raise ReglaNegocioError(f"Faltan ubicar {pendientes} pallet(s) antes de finalizar.")
    recepcion.fecha_hora_fin = timezone.now()
    recepcion.save(update_fields=["fecha_hora_fin"])
    registrar(usuario, "RECEPCION_FINALIZADA", f"Guía {recepcion.guia_remision} en {recepcion.duracion_min()} min")
    return recepcion
