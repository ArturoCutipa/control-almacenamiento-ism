from django.db import DatabaseError, connection, transaction
from django.test import TestCase
from django.urls import reverse

from apps import pruebas
from apps.bitacora.models import Bitacora
from apps.bitacora.services import registrar
from apps.usuarios.models import Rol


class BitacoraTests(TestCase):
    def setUp(self):
        self.admin = pruebas.usuario(Rol.ADMIN)
        self.op = pruebas.usuario(Rol.OPERARIO)
        registrar(self.admin, "PRODUCTO_GUARDADO", "7750182000011 Cielo")
        registrar(self.op, "SALIDA", "10 cajas lote L1 - motivo: pedido urgente")

    def test_rn14_la_base_de_datos_impide_modificar_o_borrar(self):
        if connection.vendor != "postgresql":
            self.skipTest("El trigger de RN-14 solo existe en PostgreSQL.")
        total = Bitacora.objects.count()
        for sql in ("UPDATE bitacora_bitacora SET detalle = 'alterado'", "DELETE FROM bitacora_bitacora"):
            with self.subTest(sql=sql):
                with self.assertRaises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(sql)
        self.assertEqual(Bitacora.objects.count(), total)
        self.assertFalse(Bitacora.objects.filter(detalle="alterado").exists())

    def test_filtros_por_usuario_y_accion(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse("bitacora:lista"), {"usuario": self.op.pk, "accion": "SALIDA"})
        registros = list(r.context["pagina"])
        self.assertEqual(len(registros), 1)
        self.assertIn("pedido urgente", registros[0].detalle)  # el motivo queda registrado

    def test_tareas_del_sistema_sin_usuario(self):
        registro = registrar(None, "GENERAR_ALERTAS", "0 alertas nuevas")
        self.assertIsNone(registro.usuario)

    def test_detalle_muy_largo_se_recorta(self):
        self.assertEqual(len(registrar(self.admin, "PRUEBA", "x" * 5000).detalle), 2000)
