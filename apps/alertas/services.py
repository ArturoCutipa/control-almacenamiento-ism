"""Generación diaria de alertas de vencimiento (RF-14, RN-11) y bloqueo de lotes vencidos (RN-12)."""
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.bitacora.services import registrar
from apps.inventario.models import Lote

from .models import Alerta


@transaction.atomic
def generar_alertas(hoy=None, plazo=None):
    hoy = hoy or timezone.localdate()
    plazo = settings.ALERTA_DIAS_VENCIMIENTO if plazo is None else plazo
    lotes = (Lote.objects.filter(estado=Lote.DISPONIBLE, fecha_vencimiento__lte=hoy + timedelta(days=plazo))
             .annotate(cajas=Sum("stocks__cantidad_cajas")).filter(cajas__gt=0).select_related("producto"))
    creadas = vencidos = 0
    for lote in lotes:
        dias = lote.dias_para_vencer(hoy)
        if dias < 0:
            lote.estado = Lote.VENCIDO  # bloqueado para despacho y registrado como merma
            lote.save(update_fields=["estado"])
            Alerta.objects.filter(lote=lote, tipo=Alerta.POR_VENCER, atendida=False).update(
                atendida=True, comentario="Lote vencido")
            tipo = Alerta.VENCIDO
            vencidos += 1
        else:
            tipo = Alerta.POR_VENCER
        alerta, nueva = Alerta.objects.get_or_create(
            lote=lote, tipo=tipo, atendida=False, defaults={"dias_restantes": dias, "cajas": lote.cajas})
        if not nueva:
            alerta.dias_restantes, alerta.cajas = dias, lote.cajas
            alerta.save(update_fields=["dias_restantes", "cajas"])
        creadas += int(nueva)
    registrar(None, "GENERAR_ALERTAS", f"{creadas} alertas nuevas, {vencidos} lotes vencidos bloqueados")
    return {"nuevas": creadas, "vencidos": vencidos, "revisados": len(lotes)}


def atender(alerta, usuario, comentario=""):
    alerta.atendida, alerta.atendida_por, alerta.comentario = True, usuario, comentario.strip()
    alerta.save(update_fields=["atendida", "atendida_por", "comentario"])
    registrar(usuario, "ALERTA_ATENDIDA", f"{alerta}: {alerta.comentario}")
    return alerta
