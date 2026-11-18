import re

from django.test import TestCase
from django.urls import reverse

from apps import pruebas
from apps.ubicaciones.forms import UbicacionForm


class UbicacionFormTests(TestCase):
    def setUp(self):
        self.ubic = pruebas.ubicacion(zona="A", nivel=1, posicion=1, capacidad=4)
        self.datos = {"zona": "A", "nivel": 1, "posicion": 1, "capacidad_pallets": 4, "activa": True}

    def test_ubicacion_vacia_se_puede_desactivar_y_mover(self):
        form = UbicacionForm({**self.datos, "posicion": 2, "activa": False}, instance=self.ubic)
        self.assertTrue(form.is_valid(), form.errors)

    def test_ubicacion_con_stock_no_se_desactiva(self):
        pruebas.lote_con_stock(pruebas.producto(), "L1", 30, 100, self.ubic)
        form = UbicacionForm({**self.datos, "activa": False}, instance=self.ubic)
        self.assertFalse(form.is_valid())
        self.assertIn("activa", form.errors)

    def test_ubicacion_con_stock_no_cambia_su_codigo_qr(self):
        pruebas.lote_con_stock(pruebas.producto(), "L1", 30, 100, self.ubic)
        form = UbicacionForm({**self.datos, "nivel": 2}, instance=self.ubic)
        self.assertFalse(form.is_valid())

    def test_capacidad_no_menor_que_lo_ocupado(self):
        pruebas.lote_con_stock(pruebas.producto(), "L1", 30, 200, self.ubic)  # 3 pallets
        form = UbicacionForm({**self.datos, "capacidad_pallets": 2}, instance=self.ubic)
        self.assertFalse(form.is_valid())
        self.assertIn("capacidad_pallets", form.errors)


class EtiquetasQRTests(TestCase):
    def setUp(self):
        for pos in range(1, 18):  # 17 ubicaciones -> 2 hojas de 15 etiquetas
            pruebas.ubicacion(zona="B", nivel=1, posicion=pos)
        self.client.force_login(pruebas.usuario("ENCARGADO"))

    def test_pdf_de_etiquetas_de_una_zona(self):
        r = self.client.get(reverse("ubicaciones:etiquetas"), {"zona": "b"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/pdf")
        contenido = b"".join(r.streaming_content)
        self.assertTrue(contenido.startswith(b"%PDF"))
        paginas = len(re.findall(rb"/Type /Page[^s]", contenido))
        self.assertEqual(paginas, 2)  # 15 etiquetas por hoja A4

    def test_zona_sin_ubicaciones_redirige_con_mensaje(self):
        r = self.client.get(reverse("ubicaciones:etiquetas"), {"zona": "Z"})
        self.assertRedirects(r, reverse("ubicaciones:lista"))

    def test_operario_no_imprime_etiquetas(self):
        self.client.force_login(pruebas.usuario("OPERARIO"))
        self.assertEqual(self.client.get(reverse("ubicaciones:etiquetas"), {"zona": "B"}).status_code, 403)
