from django.test import TestCase

from apps import pruebas
from apps.conteos import services
from apps.conteos.models import DetalleConteo
from apps.inventario.excepciones import ReglaNegocioError
from apps.inventario.models import Stock
from apps.movimientos.models import Movimiento
from apps.usuarios.models import Rol


class ConteoTests(TestCase):
    def setUp(self):
        self.op = pruebas.usuario(Rol.OPERARIO)
        self.enc = pruebas.usuario(Rol.ENCARGADO)
        self.ubic = pruebas.ubicacion()
        self.lote = pruebas.lote_con_stock(pruebas.producto(), "L1", 30, 100, self.ubic)
        self.conteo = services.abrir_conteo(self.op, "Zona A")

    def test_sin_diferencia_queda_conciliado(self):
        d = services.registrar_conteo(conteo=self.conteo, ubicacion=self.ubic, lote=self.lote, cant_fisica=100,
                                      usuario=self.op)
        self.assertEqual(d.estado, DetalleConteo.CONCILIADO)

    def test_rn13_ajuste_requiere_motivo_y_aplica_el_stock(self):
        d = services.registrar_conteo(conteo=self.conteo, ubicacion=self.ubic, lote=self.lote, cant_fisica=95,
                                      usuario=self.op)
        self.assertEqual((d.diferencia, d.estado), (-5, DetalleConteo.PENDIENTE))
        with self.assertRaises(ReglaNegocioError):
            services.aprobar_ajuste(detalle=d, motivo="", encargado=self.enc)
        with self.assertRaises(ReglaNegocioError):  # no se cierra con pendientes
            services.cerrar_conteo(self.conteo, self.enc)
        services.aprobar_ajuste(detalle=d, motivo="Cajas dañadas", encargado=self.enc)
        self.assertEqual(Stock.objects.get(lote=self.lote).cantidad_cajas, 95)
        self.assertTrue(Movimiento.objects.filter(tipo=Movimiento.AJUSTE, cantidad=-5).exists())
        services.cerrar_conteo(self.conteo, self.enc)

    def test_rechazo_no_modifica_el_stock(self):
        d = services.registrar_conteo(conteo=self.conteo, ubicacion=self.ubic, lote=self.lote, cant_fisica=80,
                                      usuario=self.op)
        services.rechazar_ajuste(detalle=d, motivo="", encargado=self.enc)
        self.assertEqual(Stock.objects.get(lote=self.lote).cantidad_cajas, 100)
