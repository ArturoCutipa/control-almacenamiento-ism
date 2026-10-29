from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps import pruebas
from apps.inventario import services
from apps.inventario.excepciones import CapacidadExcedidaError, ReglaNegocioError, StockInsuficienteError
from apps.inventario.models import Stock


class ReglasInventarioTests(TestCase):
    def setUp(self):
        self.prod = pruebas.producto(cajas_por_pallet=80)
        self.ubic = pruebas.ubicacion(capacidad=2)
        self.hoy = timezone.localdate()

    def test_rn05_vencimiento_debe_ser_posterior_a_la_recepcion(self):
        with self.assertRaises(ReglaNegocioError):
            services.obtener_o_crear_lote(self.prod, "L1", self.hoy)

    def test_rn04_lote_obligatorio(self):
        with self.assertRaises(ReglaNegocioError):
            services.obtener_o_crear_lote(self.prod, "  ", self.hoy + timedelta(days=30))

    def test_lote_existente_con_otro_vencimiento_se_rechaza(self):
        services.obtener_o_crear_lote(self.prod, "L1", self.hoy + timedelta(days=30))
        with self.assertRaises(ReglaNegocioError):
            services.obtener_o_crear_lote(self.prod, "l1", self.hoy + timedelta(days=40))

    def test_rn07_no_supera_la_capacidad_de_la_ubicacion(self):
        lote = pruebas.lote_con_stock(self.prod, "L1", 30, 160, self.ubic)  # 2 pallets = capacidad
        with self.assertRaises(CapacidadExcedidaError), transaction.atomic():
            services.incrementar(lote, self.ubic, 1)
        self.assertEqual(Stock.objects.get(lote=lote).cantidad_cajas, 160)

    def test_rn10_no_permite_stock_negativo(self):
        lote = pruebas.lote_con_stock(self.prod, "L1", 30, 50, self.ubic)
        with self.assertRaises(StockInsuficienteError), transaction.atomic():
            services.descontar(lote, self.ubic, 51)
        with self.assertRaises(StockInsuficienteError), transaction.atomic():
            services.ajustar(Stock.objects.get(lote=lote), -60)

    def test_restriccion_check_en_la_base_de_datos(self):
        lote = pruebas.lote_con_stock(self.prod, "L1", 30, 10, self.ubic)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Stock.objects.filter(lote=lote).update(cantidad_cajas=-1)
