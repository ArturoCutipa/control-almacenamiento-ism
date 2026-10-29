from django.test import TestCase

from apps import pruebas
from apps.alertas.models import Alerta
from apps.alertas.services import generar_alertas
from apps.inventario.models import Lote


class AlertasTests(TestCase):
    def setUp(self):
        prod = pruebas.producto()
        u = pruebas.ubicacion(capacidad=10)
        self.proximo = pruebas.lote_con_stock(prod, "PROX", 10, 50, u)
        self.lejano = pruebas.lote_con_stock(prod, "LEJ", 120, 50, u)

    def test_rn11_alerta_a_30_dias_o_menos(self):
        r = generar_alertas()
        self.assertEqual(r["nuevas"], 1)
        self.assertTrue(Alerta.objects.filter(lote=self.proximo, tipo=Alerta.POR_VENCER).exists())
        self.assertFalse(Alerta.objects.filter(lote=self.lejano).exists())

    def test_proceso_es_idempotente(self):
        generar_alertas()
        generar_alertas()
        self.assertEqual(Alerta.objects.filter(lote=self.proximo, atendida=False).count(), 1)

    def test_rn12_bloquea_lotes_vencidos(self):
        Lote.objects.filter(pk=self.proximo.pk).update(fecha_vencimiento=self.proximo.fecha_vencimiento.replace(year=2020))
        generar_alertas()
        self.proximo.refresh_from_db()
        self.assertEqual(self.proximo.estado, Lote.VENCIDO)
        self.assertTrue(Alerta.objects.filter(lote=self.proximo, tipo=Alerta.VENCIDO).exists())
