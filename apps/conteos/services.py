"""Conteo físico (RF-15) y conciliación con ajustes aprobados (RF-16, RN-13)."""
from django.db import transaction
from django.utils import timezone

from apps.bitacora.services import registrar
from apps.inventario import services as inventario
from apps.inventario.excepciones import ReglaNegocioError
from apps.inventario.models import Stock
from apps.movimientos.models import Movimiento

from .models import Conteo, DetalleConteo


def abrir_conteo(usuario, descripcion=""):
    conteo = Conteo.objects.create(usuario=usuario, descripcion=descripcion.strip())
    registrar(usuario, "CONTEO_ABIERTO", f"Conteo {conteo.id} {conteo.descripcion}")
    return conteo


def registrar_conteo(*, conteo, ubicacion, lote, cant_fisica, usuario):
    if conteo.estado != Conteo.ABIERTO:
        raise ReglaNegocioError("El conteo está cerrado.")
    if cant_fisica is None or cant_fisica < 0:
        raise ReglaNegocioError("La cantidad contada no puede ser negativa.")
    stock = Stock.objects.filter(lote=lote, ubicacion=ubicacion).first()
    sistema = stock.cantidad_cajas if stock else 0
    diferencia = cant_fisica - sistema
    detalle = DetalleConteo.objects.create(
        conteo=conteo, lote=lote, ubicacion=ubicacion, stock=stock, cant_sistema=sistema, cant_fisica=cant_fisica,
        diferencia=diferencia, contado_por=usuario,
        estado=DetalleConteo.CONCILIADO if diferencia == 0 else DetalleConteo.PENDIENTE)
    registrar(usuario, "CONTEO_REGISTRADO",
              f"Conteo {conteo.id}: lote {lote.numero_lote} en {ubicacion.codigo_qr} contado {cant_fisica}, "
              f"sistema {sistema}, diferencia {diferencia:+d}")
    return detalle


@transaction.atomic
def aprobar_ajuste(*, detalle, motivo, encargado):
    """RN-13: el ajuste requiere motivo y la aprobación del Encargado. RN-10: sin stock negativo."""
    detalle = DetalleConteo.objects.select_for_update().select_related("lote", "ubicacion").get(pk=detalle.pk)
    if detalle.estado != DetalleConteo.PENDIENTE:
        raise ReglaNegocioError("Esta diferencia ya fue revisada.")
    motivo = (motivo or "").strip()
    if not motivo:
        raise ReglaNegocioError("Indique el motivo del ajuste (RN-13).")
    stock, _ = Stock.objects.get_or_create(lote=detalle.lote, ubicacion=detalle.ubicacion)
    inventario.ajustar(stock, detalle.diferencia)
    es_ingreso = detalle.diferencia > 0
    Movimiento.objects.create(
        tipo=Movimiento.AJUSTE, lote=detalle.lote, cantidad=detalle.diferencia, motivo=motivo, usuario=encargado,
        ubicacion_destino=detalle.ubicacion if es_ingreso else None,
        ubicacion_origen=None if es_ingreso else detalle.ubicacion)
    detalle.estado, detalle.motivo = DetalleConteo.APROBADO, motivo
    detalle.revisado_por, detalle.fecha_revision = encargado, timezone.now()
    detalle.stock = stock
    detalle.save()
    registrar(encargado, "AJUSTE_APROBADO",
              f"Lote {detalle.lote.numero_lote} en {detalle.ubicacion.codigo_qr}: {detalle.diferencia:+d} cajas. "
              f"Motivo: {motivo}")
    return detalle


def rechazar_ajuste(*, detalle, motivo, encargado):
    if detalle.estado != DetalleConteo.PENDIENTE:
        raise ReglaNegocioError("Esta diferencia ya fue revisada.")
    detalle.estado, detalle.motivo = DetalleConteo.RECHAZADO, (motivo or "Se solicita reconteo").strip()
    detalle.revisado_por, detalle.fecha_revision = encargado, timezone.now()
    detalle.save()
    registrar(encargado, "AJUSTE_RECHAZADO",
              f"Lote {detalle.lote.numero_lote} en {detalle.ubicacion.codigo_qr}: reconteo. {detalle.motivo}")
    return detalle


def cerrar_conteo(conteo, usuario):
    if conteo.pendientes:
        raise ReglaNegocioError(f"Hay {conteo.pendientes} diferencia(s) pendientes de aprobación.")
    conteo.estado = Conteo.CERRADO
    conteo.save(update_fields=["estado"])
    registrar(usuario, "CONTEO_CERRADO", f"Conteo {conteo.id}")
    return conteo
