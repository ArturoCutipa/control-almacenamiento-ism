from datetime import timedelta
from io import BytesIO

from django.test import TestCase, override_settings
from django.utils import timezone
from openpyxl import load_workbook

from apps import pruebas
from apps.inventario.models import Stock
from apps.integracion_sap import services
from apps.movimientos import services as movimientos
from apps.movimientos.models import Movimiento
from apps.usuarios.models import Rol


@override_settings(MEDIA_ROOT="media_pruebas")
class ExportacionSAPTests(TestCase):
    def setUp(self):
        self.enc = pruebas.usuario(Rol.ENCARGADO)
        self.ubic = pruebas.ubicacion()
        self.lote = pruebas.lote_con_stock(pruebas.producto(), "L1", 40, 100, self.ubic)

    def test_archivo_consolidado_por_producto_y_lote(self):
        exp = services.generar_archivo(timezone.localdate(), self.enc)
        ws = load_workbook(BytesIO(exp.archivo.read())).active
        self.assertEqual(ws.cell(2, 3).value, "L1")
        self.assertEqual(ws.cell(2, 5).value, 100)
        self.assertEqual((exp.total_registros, exp.total_cajas), (1, 100))
        exp.archivo.delete()

    def test_fecha_de_corte_pasada_descuenta_movimientos_posteriores(self):
        Movimiento.objects.create(tipo=Movimiento.ENTRADA, lote=self.lote, ubicacion_destino=self.ubic,
                                  cantidad=100, usuario=self.enc)
        movimientos.registrar_salida(stock=Stock.objects.get(lote=self.lote), cantidad=30, usuario=self.enc)
        ayer = timezone.localdate() - timedelta(days=1)
        hoy = dict((l.numero_lote, c) for l, c in services.inventario_consolidado())
        antes = dict((l.numero_lote, c) for l, c in services.inventario_consolidado(ayer))
        self.assertEqual(hoy["L1"], 70)
        self.assertNotIn("L1", antes)  # el lote entró hoy
