"""Archivo Excel de carga para SAP con el inventario consolidado por producto y lote (RF-18)."""
from collections import defaultdict
from datetime import datetime, time
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Sum
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from apps.bitacora.services import registrar
from apps.conteos.models import DetalleConteo
from apps.inventario.models import Lote, Stock
from apps.movimientos.models import Movimiento

from .models import ExportacionSAP

# Columnas del archivo de carga. El formato definitivo lo indica el área de TI de ISM (RNF-11):
# basta con ajustar esta lista y la función fila().
COLUMNAS = ["Material (código de barras)", "Descripción", "Lote", "Fecha de vencimiento", "Cantidad", "Unidad",
            "Centro", "Almacén", "Fecha de corte"]


def _efecto(mov):
    """Efecto de un movimiento sobre el total del lote (las transferencias no cambian el total)."""
    if mov.tipo == Movimiento.ENTRADA:
        return mov.cantidad
    if mov.tipo == Movimiento.SALIDA:
        return -mov.cantidad
    if mov.tipo == Movimiento.AJUSTE:
        return mov.cantidad
    return 0


def inventario_consolidado(fecha_corte=None):
    """Cajas por lote al cierre de la fecha de corte: stock actual menos los movimientos posteriores."""
    hoy = timezone.localdate()
    fecha_corte = fecha_corte or hoy
    totales = defaultdict(int)
    for fila in Stock.objects.values("lote").annotate(t=Sum("cantidad_cajas")):
        totales[fila["lote"]] = fila["t"] or 0
    if fecha_corte < hoy:
        limite = timezone.make_aware(datetime.combine(fecha_corte, time.max))
        for mov in Movimiento.objects.filter(fecha_hora__gt=limite).only("tipo", "cantidad", "lote_id"):
            totales[mov.lote_id] -= _efecto(mov)
    lotes = Lote.objects.filter(pk__in=[k for k, v in totales.items() if v > 0]).select_related("producto")
    return sorted(((lote, totales[lote.pk]) for lote in lotes),
                  key=lambda x: (x[0].producto.codigo_barras, x[0].fecha_vencimiento, x[0].numero_lote))


def fila(lote, cajas, fecha_corte):
    p = lote.producto
    return [p.codigo_barras, f"{p.descripcion} - {p.marca} {p.sabor} {p.formato}", lote.numero_lote,
            lote.fecha_vencimiento, cajas, "CJ", getattr(settings, "SAP_CENTRO", "TACN"),
            getattr(settings, "SAP_ALMACEN", "ALM1"), fecha_corte]


def conteos_pendientes():
    return DetalleConteo.objects.filter(estado=DetalleConteo.PENDIENTE).count()


def generar_archivo(fecha_corte, usuario):
    datos = inventario_consolidado(fecha_corte)
    wb = Workbook()
    ws = wb.active
    ws.title = "Carga SAP"
    ws.append(COLUMNAS)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F3864")
        c.alignment = Alignment(horizontal="center")
    total = 0
    for lote, cajas in datos:
        ws.append(fila(lote, cajas, fecha_corte))
        total += cajas
    for r in ws.iter_rows(min_row=2, min_col=4, max_col=4):
        r[0].number_format = "DD/MM/YYYY"
    for r in ws.iter_rows(min_row=2, min_col=9, max_col=9):
        r[0].number_format = "DD/MM/YYYY"
    for col, ancho in zip("ABCDEFGHI", (24, 46, 16, 18, 10, 8, 8, 9, 14)):
        ws.column_dimensions[col].width = ancho
    ws.freeze_panes = "A2"
    buffer = BytesIO()
    wb.save(buffer)
    exp = ExportacionSAP(fecha_corte=fecha_corte, usuario=usuario, total_registros=len(datos), total_cajas=total)
    exp.archivo.save(f"carga_sap_{fecha_corte:%Y%m%d}_{timezone.now():%H%M%S}.xlsx", ContentFile(buffer.getvalue()),
                     save=True)
    registrar(usuario, "EXPORTACION_SAP", f"Corte {fecha_corte:%d/%m/%Y}: {len(datos)} lotes, {total} cajas")
    return exp
