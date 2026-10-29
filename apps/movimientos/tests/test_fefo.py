from django.test import TestCase

from apps import pruebas
from apps.inventario.excepciones import LoteNoDisponibleError, ReglaNegocioError
from apps.inventario.models import Lote, Stock
from apps.movimientos import services
from apps.movimientos.models import Movimiento
from apps.usuarios.models import Rol


class FefoTests(TestCase):
    def setUp(self):
        self.op = pruebas.usuario(Rol.OPERARIO)
        self.prod = pruebas.producto()
        self.u1, self.u2 = pruebas.ubicacion(posicion=1), pruebas.ubicacion(posicion=2)
        self.lejano = pruebas.lote_con_stock(self.prod, "LEJANO", 90, 100, self.u1)
        self.cercano = pruebas.lote_con_stock(self.prod, "CERCANO", 20, 100, self.u2)

    def test_rn08_sugiere_el_lote_mas_proximo_a_vencer(self):
        sugerido, candidatos = services.sugerir(self.prod, 10)
        self.assertEqual(sugerido.lote, self.cercano)
        self.assertEqual([s.lote.numero_lote for s in candidatos], ["CERCANO", "LEJANO"])

    def test_salida_descuenta_y_registra_movimiento(self):
        stock = Stock.objects.get(lote=self.cercano)
        services.registrar_salida(stock=stock, cantidad=30, usuario=self.op)
        stock.refresh_from_db()
        self.assertEqual(stock.cantidad_cajas, 70)
        self.assertTrue(Movimiento.objects.filter(tipo=Movimiento.SALIDA, lote=self.cercano, cantidad=30).exists())

    def test_rn09_otro_lote_exige_motivo(self):
        stock = Stock.objects.get(lote=self.lejano)
        with self.assertRaises(ReglaNegocioError):
            services.registrar_salida(stock=stock, cantidad=10, usuario=self.op)
        services.registrar_salida(stock=stock, cantidad=10, usuario=self.op, motivo="Pedido del cliente")
        self.assertEqual(Stock.objects.get(lote=self.lejano).cantidad_cajas, 90)

    def test_rn12_lote_vencido_no_se_despacha(self):
        Lote.objects.filter(pk=self.cercano.pk).update(estado=Lote.VENCIDO)
        with self.assertRaises(LoteNoDisponibleError):
            services.registrar_salida(stock=Stock.objects.get(lote=self.cercano), cantidad=1, usuario=self.op)

    def test_transferencia_mueve_el_stock(self):
        destino = pruebas.ubicacion(posicion=3)
        services.transferir(stock=Stock.objects.get(lote=self.lejano), destino=destino, cantidad=40, usuario=self.op)
        self.assertEqual(Stock.objects.get(lote=self.lejano, ubicacion=self.u1).cantidad_cajas, 60)
        self.assertEqual(Stock.objects.get(lote=self.lejano, ubicacion=destino).cantidad_cajas, 40)
        self.assertTrue(Movimiento.objects.filter(tipo=Movimiento.TRANSFERENCIA).exists())
