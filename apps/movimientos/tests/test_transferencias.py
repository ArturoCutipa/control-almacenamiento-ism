from django.test import TestCase
from django.urls import reverse

from apps import pruebas
from apps.inventario.excepciones import CapacidadExcedidaError, ReglaNegocioError, StockInsuficienteError
from apps.inventario.models import Stock
from apps.movimientos import services
from apps.movimientos.models import Movimiento
from apps.usuarios.models import Rol


class TransferenciaTests(TestCase):
    def setUp(self):
        self.op = pruebas.usuario(Rol.OPERARIO)
        self.prod = pruebas.producto(cajas_por_pallet=80)
        self.origen = pruebas.ubicacion(posicion=1, capacidad=4)
        self.destino = pruebas.ubicacion(posicion=2, capacidad=1)  # 1 pallet = 80 cajas
        self.lote = pruebas.lote_con_stock(self.prod, "L1", 60, 200, self.origen)
        self.stock = Stock.objects.get(lote=self.lote, ubicacion=self.origen)

    def test_origen_y_destino_deben_ser_distintos(self):
        with self.assertRaises(ReglaNegocioError):
            services.transferir(stock=self.stock, destino=self.origen, cantidad=10, usuario=self.op)

    def test_no_transfiere_mas_de_lo_que_hay(self):
        with self.assertRaises(StockInsuficienteError):
            services.transferir(stock=self.stock, destino=self.destino, cantidad=500, usuario=self.op)

    def test_rn07_respeta_la_capacidad_del_destino_y_no_deja_cambios(self):
        with self.assertRaises(CapacidadExcedidaError):
            services.transferir(stock=self.stock, destino=self.destino, cantidad=100, usuario=self.op)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.cantidad_cajas, 200)  # la transacción se revierte completa
        self.assertFalse(Movimiento.objects.filter(tipo=Movimiento.TRANSFERENCIA).exists())

    def test_pantalla_acepta_qr_y_lote_en_minusculas(self):
        self.client.force_login(self.op)
        r = self.client.post(reverse("movimientos:transferencia"), {
            "qr_origen": self.origen.codigo_qr.lower(), "numero_lote": "l1", "cantidad": 50,
            "qr_destino": self.destino.codigo_qr.lower(), "motivo": "Reordenar zona A"})
        self.assertRedirects(r, reverse("movimientos:transferencia"))
        self.assertEqual(Stock.objects.get(lote=self.lote, ubicacion=self.destino).cantidad_cajas, 50)

    def test_pantalla_rechaza_destino_inactivo(self):
        self.destino.activa = False
        self.destino.save()
        self.client.force_login(self.op)
        r = self.client.post(reverse("movimientos:transferencia"), {
            "qr_origen": self.origen.codigo_qr, "numero_lote": "L1", "cantidad": 10,
            "qr_destino": self.destino.codigo_qr, "motivo": ""})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "QR de ubicación no válido")
        self.assertFalse(Stock.objects.filter(ubicacion=self.destino).exists())

    def test_planificacion_no_registra_transferencias(self):
        self.client.force_login(pruebas.usuario(Rol.PLANIFICACION))
        self.assertEqual(self.client.get(reverse("movimientos:transferencia")).status_code, 403)
