from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from openpyxl import load_workbook

from apps import pruebas
from apps.conteos import services as conteos
from apps.reportes import services
from apps.usuarios.models import Rol


class ReportesTests(TestCase):
    def setUp(self):
        self.enc = pruebas.usuario(Rol.ENCARGADO)
        self.ubic = pruebas.ubicacion()
        self.lote = pruebas.lote_con_stock(pruebas.producto(), "PROX", 10, 100, self.ubic)
        conteo = conteos.abrir_conteo(self.enc)
        conteos.registrar_conteo(conteo=conteo, ubicacion=self.ubic, lote=self.lote, cant_fisica=100, usuario=self.enc)
        conteos.registrar_conteo(conteo=conteo, ubicacion=self.ubic, lote=self.lote, cant_fisica=96, usuario=self.enc)
        self.hoy = timezone.localdate()

    def test_los_cinco_reportes_en_pdf_y_excel(self):
        self.client.force_login(self.enc)
        for tipo in services.TIPOS:
            for formato in ("pdf", "xlsx"):
                with self.subTest(tipo=tipo, formato=formato):
                    r = self.client.get(reverse("reportes:reportes"), {"tipo": tipo, "formato": formato})
                    self.assertEqual(r.status_code, 200)
                    self.assertIn(f"reporte_{tipo}_", r["Content-Disposition"])

    def test_exactitud_de_inventario(self):
        datos = services.generar("exactitud", self.hoy - timedelta(days=1), self.hoy)
        resumen = dict(datos["resumen"])
        self.assertEqual(resumen["Registros contados"], 2)
        self.assertEqual(resumen["Exactitud (%)"], 50.0)

    def test_vencimientos_incluye_lote_proximo(self):
        datos = services.generar("vencimientos", self.hoy, self.hoy)
        self.assertEqual([f[2] for f in datos["filas"]], ["PROX"])
        self.assertEqual(dict(datos["resumen"])["Cajas en riesgo"], 100)

    def test_excel_contiene_columnas_y_filas(self):
        datos = services.generar("diferencias", self.hoy - timedelta(days=1), self.hoy)
        hoja = load_workbook(services.a_excel(datos)).active
        valores = [c for fila in hoja.iter_rows(values_only=True) for c in fila]
        self.assertIn("Diferencia", valores)
        self.assertIn(-4, valores)

    def test_tipo_de_reporte_invalido_da_404(self):
        self.client.force_login(self.enc)
        self.assertEqual(self.client.get(reverse("reportes:reportes"), {"tipo": "otro"}).status_code, 404)

    def test_operario_no_accede_a_reportes(self):
        self.client.force_login(pruebas.usuario(Rol.OPERARIO))
        self.assertEqual(self.client.get(reverse("reportes:reportes")).status_code, 403)
