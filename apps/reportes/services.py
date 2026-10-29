"""Reportes e indicadores (RF-19). Cada reporte devuelve título, columnas, filas y resumen."""
from datetime import timedelta
from io import BytesIO

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.conteos.models import DetalleConteo
from apps.inventario.models import Lote
from apps.movimientos.models import Movimiento
from apps.recepcion.models import Recepcion

TIPOS = {
    "recepcion": "Tiempos de recepción",
    "exactitud": "Exactitud de inventario",
    "vencimientos": "Lotes próximos a vencer",
    "diferencias": "Diferencias de conteo",
    "movimientos": "Movimientos del almacén",
}


def _rango(qs, campo, desde, hasta):
    return qs.filter(**{f"{campo}__date__gte": desde, f"{campo}__date__lte": hasta})


def reporte_recepcion(desde, hasta):
    recs = _rango(Recepcion.objects.filter(fecha_hora_fin__isnull=False), "fecha_hora_inicio", desde, hasta)
    recs = recs.select_related("usuario").prefetch_related("detalles")
    filas, minutos, pallets = [], [], 0
    for r in recs:
        p = sum(d.pallets for d in r.detalles.all())
        pallets += p
        minutos.append(r.duracion_min())
        filas.append([r.guia_remision, f"{timezone.localtime(r.fecha_hora_inicio):%d/%m/%Y %H:%M}", str(r.usuario),
                      p, sum(d.cantidad_cajas for d in r.detalles.all()), r.duracion_min()])
    prom = round(sum(minutos) / len(minutos), 1) if minutos else 0
    por_pallet = round(sum(minutos) / pallets, 2) if pallets else 0
    return {"columnas": ["Guía", "Inicio", "Operario", "Pallets", "Cajas", "Minutos"], "filas": filas,
            "resumen": [("Recepciones", len(filas)), ("Tiempo promedio (min)", prom),
                        ("Minutos por pallet", por_pallet)]}


def reporte_exactitud(desde, hasta):
    dets = _rango(DetalleConteo.objects.select_related("lote__producto", "ubicacion"), "registrado", desde, hasta)
    filas, exactos = [], 0
    for d in dets:
        exacto = d.diferencia == 0
        exactos += exacto
        filas.append([f"{timezone.localtime(d.registrado):%d/%m/%Y}", d.ubicacion.codigo_qr, d.lote.numero_lote,
                      d.cant_sistema, d.cant_fisica, d.diferencia, "Sí" if exacto else "No"])
    total = len(filas)
    pct = round(exactos * 100 / total, 1) if total else 0
    return {"columnas": ["Fecha", "Ubicación", "Lote", "Sistema", "Contado", "Diferencia", "Exacto"], "filas": filas,
            "resumen": [("Registros contados", total), ("Registros exactos", exactos), ("Exactitud (%)", pct)]}


def reporte_vencimientos(desde, hasta):
    hoy = timezone.localdate()
    limite = hoy + timedelta(days=settings.ALERTA_DIAS_VENCIMIENTO)
    lotes = (Lote.objects.filter(fecha_vencimiento__lte=limite).annotate(cajas=Sum("stocks__cantidad_cajas"))
             .filter(cajas__gt=0).select_related("producto").order_by("fecha_vencimiento"))
    filas = [[l.producto.codigo_barras, str(l.producto), l.numero_lote, l.fecha_vencimiento.strftime("%d/%m/%Y"),
              l.dias_para_vencer(hoy), l.cajas, l.get_estado_display()] for l in lotes]
    return {"columnas": ["Código", "Producto", "Lote", "Vence", "Días", "Cajas", "Estado"], "filas": filas,
            "resumen": [("Lotes", len(filas)), ("Cajas en riesgo", sum(f[5] for f in filas)),
                        ("Plazo de alerta (días)", settings.ALERTA_DIAS_VENCIMIENTO)]}


def reporte_diferencias(desde, hasta):
    dets = _rango(DetalleConteo.objects.exclude(diferencia=0).select_related("lote__producto", "ubicacion",
                                                                             "revisado_por"), "registrado", desde, hasta)
    filas = [[f"{timezone.localtime(d.registrado):%d/%m/%Y}", d.ubicacion.codigo_qr, d.lote.numero_lote,
              str(d.lote.producto), d.diferencia, d.get_estado_display(), d.motivo,
              str(d.revisado_por or "")] for d in dets]
    return {"columnas": ["Fecha", "Ubicación", "Lote", "Producto", "Diferencia", "Estado", "Motivo", "Revisó"],
            "filas": filas,
            "resumen": [("Diferencias", len(filas)), ("Suma de diferencias (cajas)", sum(f[4] for f in filas))]}


def reporte_movimientos(desde, hasta):
    movs = _rango(Movimiento.objects.select_related("lote__producto", "ubicacion_origen", "ubicacion_destino",
                                                    "usuario"), "fecha_hora", desde, hasta)
    filas = [[f"{timezone.localtime(m.fecha_hora):%d/%m/%Y %H:%M}", m.get_tipo_display(), m.lote.numero_lote,
              str(m.lote.producto), m.cantidad, str(m.ubicacion_origen or ""), str(m.ubicacion_destino or ""),
              str(m.usuario)] for m in movs]
    resumen = [("Movimientos", len(filas))]
    for codigo, nombre in Movimiento.TIPOS:
        resumen.append((nombre, sum(1 for f in filas if f[1] == nombre)))
    return {"columnas": ["Fecha", "Tipo", "Lote", "Producto", "Cajas", "Origen", "Destino", "Usuario"],
            "filas": filas, "resumen": resumen}


def generar(tipo, desde, hasta):
    datos = globals()[f"reporte_{tipo}"](desde, hasta)
    datos.update({"titulo": TIPOS[tipo], "desde": desde, "hasta": hasta, "tipo": tipo})
    return datos


def a_excel(datos):
    wb = Workbook()
    ws = wb.active
    ws.title = datos["titulo"][:30]
    ws.append([datos["titulo"]])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([f"Del {datos['desde']:%d/%m/%Y} al {datos['hasta']:%d/%m/%Y}"])
    for k, v in datos["resumen"]:
        ws.append([k, v])
    ws.append([])
    ws.append(datos["columnas"])
    for c in ws[ws.max_row]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F3864")
    for f in datos["filas"]:
        ws.append(f)
    for i in range(1, len(datos["columnas"]) + 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = 18
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def a_pdf(datos):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=12 * mm, rightMargin=12 * mm,
                            topMargin=12 * mm, bottomMargin=12 * mm, title=datos["titulo"])
    est = getSampleStyleSheet()
    celda = est["BodyText"].clone("celda", fontSize=8, leading=10)
    partes = [Paragraph(f"ISM - Tacna · {datos['titulo']}", est["Title"]),
              Paragraph(f"Del {datos['desde']:%d/%m/%Y} al {datos['hasta']:%d/%m/%Y} · generado el "
                        f"{timezone.localtime():%d/%m/%Y %H:%M}", est["Normal"]), Spacer(1, 4 * mm)]
    resumen = Table([[k, str(v)] for k, v in datos["resumen"]], hAlign="LEFT")
    resumen.setStyle(TableStyle([("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                                 ("GRID", (0, 0), (-1, -1), 0.3, colors.grey)]))
    partes += [resumen, Spacer(1, 5 * mm)]
    filas = [[Paragraph(f"<b>{c}</b>", celda) for c in datos["columnas"]]]
    filas += [[Paragraph(str(v), celda) for v in f] for f in datos["filas"]] or [["Sin datos en el rango"]]
    tabla = Table(filas, repeatRows=1)
    tabla.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
                               ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    partes.append(tabla)
    doc.build(partes)
    buffer.seek(0)
    return buffer
