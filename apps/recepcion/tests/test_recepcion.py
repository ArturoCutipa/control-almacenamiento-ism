from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps import pruebas
from apps.bitacora.models import Bitacora
from apps.inventario.excepciones import ReglaNegocioError
from apps.inventario.models import Stock
from apps.movimientos.models import Movimiento
from apps.recepcion import services
from apps.usuarios.models import Rol


class RecepcionTests(TestCase):
    def setUp(self):
        self.op = pruebas.usuario(Rol.OPERARIO)
        self.prod = pruebas.producto(cajas_por_pallet=80)
        self.ubic = pruebas.ubicacion(capacidad=4)
        self.venc = timezone.localdate() + timedelta(days=60)

    def test_flujo_completo_recepcion_ubicacion_y_cierre(self):
        rec = services.iniciar_recepcion("t001-123", self.op)
        det = services.registrar_pallet(recepcion=rec, producto=self.prod, numero_lote="l55",
                                        fecha_vencimiento=self.venc, cantidad_cajas=100, usuario=self.op)
        self.assertEqual(det.pallets, 2)
        self.assertEqual(det.lote.numero_lote, "L55")
        with self.assertRaises(ReglaNegocioError):  # falta ubicar
            services.finalizar_recepcion(rec, self.op)
        services.asignar_ubicacion(detalle=det, ubicacion=self.ubic, usuario=self.op)
        self.assertEqual(Stock.objects.get(lote=det.lote, ubicacion=self.ubic).cantidad_cajas, 100)
        self.assertTrue(Movimiento.objects.filter(tipo=Movimiento.ENTRADA, cantidad=100).exists())
        services.finalizar_recepcion(rec, self.op)
        rec.refresh_from_db()
        self.assertIsNotNone(rec.duracion_min())
        self.assertTrue(Bitacora.objects.filter(accion="RECEPCION_FINALIZADA").exists())

    def test_no_se_ubica_dos_veces(self):
        rec = services.iniciar_recepcion("G1", self.op)
        det = services.registrar_pallet(recepcion=rec, producto=self.prod, numero_lote="L1",
                                        fecha_vencimiento=self.venc, cantidad_cajas=80, usuario=self.op)
        services.asignar_ubicacion(detalle=det, ubicacion=self.ubic, usuario=self.op)
        with self.assertRaises(ReglaNegocioError):
            services.asignar_ubicacion(detalle=det, ubicacion=self.ubic, usuario=self.op)

    def test_cantidad_debe_ser_positiva(self):
        rec = services.iniciar_recepcion("G2", self.op)
        with self.assertRaises(ReglaNegocioError):
            services.registrar_pallet(recepcion=rec, producto=self.prod, numero_lote="L1",
                                      fecha_vencimiento=self.venc, cantidad_cajas=0, usuario=self.op)
