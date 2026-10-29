"""Generación de etiquetas QR en PDF (RF-06) con qrcode 8.0 y ReportLab 4.4."""
from io import BytesIO

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def imagen_qr(texto):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(texto)
    qr.make(fit=True)
    buffer = BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buffer, format="PNG")
    buffer.seek(0)
    return ImageReader(buffer)


def pdf_etiquetas(ubicaciones):
    """Hoja A4 con 3 x 5 etiquetas de 60 x 50 mm: QR y código legible."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle("Etiquetas QR de ubicación - ISM")
    ancho, alto = A4
    cols, filas = 3, 5
    w, h = 60 * mm, 50 * mm
    margen_x = (ancho - cols * w) / 2
    margen_y = (alto - filas * h) / 2
    for i, u in enumerate(ubicaciones):
        if i and i % (cols * filas) == 0:
            c.showPage()
        k = i % (cols * filas)
        x = margen_x + (k % cols) * w
        y = alto - margen_y - (k // cols + 1) * h
        c.setDash(2, 2)
        c.rect(x, y, w, h)
        c.setDash()
        c.drawImage(imagen_qr(u.codigo_qr), x + (w - 34 * mm) / 2, y + 12 * mm, 34 * mm, 34 * mm)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(x + w / 2, y + 7 * mm, u.codigo_qr)
        c.setFont("Helvetica", 8)
        c.drawCentredString(x + w / 2, y + 3 * mm, f"Zona {u.zona} - Nivel {u.nivel} - Posición {u.posicion}")
    c.save()
    buffer.seek(0)
    return buffer
