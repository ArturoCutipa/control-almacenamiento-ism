from django.test import TestCase

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
