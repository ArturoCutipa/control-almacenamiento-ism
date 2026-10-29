"""Operaciones de stock. Deben llamarse dentro de transaction.atomic()."""
import math

from django.db import transaction
from django.utils import timezone

from apps.ubicaciones.models import Ubicacion

from .excepciones import CapacidadExcedidaError, LoteNoDisponibleError, ReglaNegocioError, StockInsuficienteError
from .models import Lote, Stock


def obtener_o_crear_lote(producto, numero_lote, fecha_vencimiento, hoy=None):
    """RF-08 / RN-04 / RN-05: crea el lote si no existe; valida la fecha de vencimiento."""
    hoy = hoy or timezone.localdate()
    numero_lote = numero_lote.strip().upper()
    if not numero_lote:
        raise ReglaNegocioError("El número de lote es obligatorio.")
    if fecha_vencimiento <= hoy:
        raise ReglaNegocioError("La fecha de vencimiento debe ser posterior a la fecha de recepción.")
    lote, creado = Lote.objects.get_or_create(
        producto=producto, numero_lote=numero_lote, defaults={"fecha_vencimiento": fecha_vencimiento})
    if not creado and lote.fecha_vencimiento != fecha_vencimiento:
        raise ReglaNegocioError(
            f"El lote {numero_lote} ya está registrado con vencimiento {lote.fecha_vencimiento:%d/%m/%Y}.")
    if lote.estado != Lote.DISPONIBLE:
        raise LoteNoDisponibleError(f"El lote {numero_lote} está {lote.get_estado_display().lower()}.")
    return lote


def _pallets(cajas, producto):
    return math.ceil(cajas / producto.cajas_por_pallet) if cajas > 0 else 0


def incrementar(lote, ubicacion, cajas):
    """Suma cajas al stock del lote en la ubicación validando la capacidad (RN-07)."""
    assert transaction.get_connection().in_atomic_block, "incrementar() requiere una transacción"
    if cajas <= 0:
        raise ReglaNegocioError("La cantidad debe ser mayor que cero.")
    ubicacion = Ubicacion.objects.select_for_update().get(pk=ubicacion.pk)
    stock, _ = Stock.objects.select_for_update().get_or_create(lote=lote, ubicacion=ubicacion)
    ocupados_otros = ubicacion.pallets_ocupados(excluir_stock=stock.pk)
    necesarios = _pallets(stock.cantidad_cajas + cajas, lote.producto)
    if ocupados_otros + necesarios > ubicacion.capacidad_pallets:
        libres = max(0, ubicacion.capacidad_pallets - ocupados_otros - _pallets(stock.cantidad_cajas, lote.producto))
        raise CapacidadExcedidaError(
            f"La ubicación {ubicacion.codigo_qr} no tiene capacidad: quedan {libres} pallet(s) libres.")
    stock.cantidad_cajas += cajas
    stock.save()
    return stock


def descontar(lote, ubicacion, cajas):
    """Resta cajas del stock; nunca deja stock negativo (RN-10)."""
    assert transaction.get_connection().in_atomic_block, "descontar() requiere una transacción"
    if cajas <= 0:
        raise ReglaNegocioError("La cantidad debe ser mayor que cero.")
    stock = Stock.objects.select_for_update().filter(lote=lote, ubicacion=ubicacion).first()
    disponible = stock.cantidad_cajas if stock else 0
    if cajas > disponible:
        raise StockInsuficienteError(
            f"Stock insuficiente: el lote {lote.numero_lote} tiene {disponible} cajas en {ubicacion.codigo_qr}.")
    stock.cantidad_cajas -= cajas
    stock.save()
    return stock


def ajustar(stock, diferencia):
    """Aplica una diferencia (positiva o negativa) a un stock existente (ajuste de conteo)."""
    assert transaction.get_connection().in_atomic_block, "ajustar() requiere una transacción"
    stock = Stock.objects.select_for_update().get(pk=stock.pk)
    nuevo = stock.cantidad_cajas + diferencia
    if nuevo < 0:
        raise StockInsuficienteError("El ajuste dejaría el stock en negativo (RN-10).")
    stock.cantidad_cajas = nuevo
    stock.save()
    return stock
