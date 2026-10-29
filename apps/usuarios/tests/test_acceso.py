from django.test import TestCase
from django.urls import reverse

from apps import pruebas
from apps.bitacora.models import Bitacora, BitacoraInmutableError
from apps.bitacora.services import registrar
from apps.usuarios.models import Rol


class AccesoPorRolTests(TestCase):
    def setUp(self):
        self.usuarios = {c: pruebas.usuario(c) for c, _ in Rol.CODIGOS}

    def ingresar(self, codigo):
        self.client.force_login(self.usuarios[codigo])

    def test_sin_sesion_redirige_al_login(self):
        r = self.client.get(reverse("dashboard:panel"))
        self.assertRedirects(r, reverse("usuarios:login") + "?next=/")

    def test_login_registra_en_bitacora(self):
        r = self.client.post(reverse("usuarios:login"), {"username": "operario", "password": pruebas.CLAVE})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Bitacora.objects.filter(accion="INICIO_SESION").exists())

    def test_usuario_inactivo_no_ingresa(self):
        u = self.usuarios[Rol.OPERARIO]
        u.is_active = False
        u.save()
        r = self.client.post(reverse("usuarios:login"), {"username": "operario", "password": pruebas.CLAVE})
        self.assertEqual(r.status_code, 200)

    def test_permisos_por_rol(self):
        casos = [  # (rol, url, código esperado)
            (Rol.OPERARIO, "integracion_sap:exportar", 403),
            (Rol.OPERARIO, "usuarios:lista", 403),
            (Rol.OPERARIO, "recepcion:lista", 200),
            (Rol.PLANIFICACION, "movimientos:salida", 403),
            (Rol.PLANIFICACION, "reportes:reportes", 200),
            (Rol.PLANIFICACION, "alertas:lista", 200),
            (Rol.ENCARGADO, "integracion_sap:exportar", 200),
            (Rol.ENCARGADO, "usuarios:lista", 403),
            (Rol.ADMIN, "usuarios:lista", 200),
        ]
        for rol, url, esperado in casos:
            with self.subTest(rol=rol, url=url):
                self.ingresar(rol)
                self.assertEqual(self.client.get(reverse(url)).status_code, esperado)

    def test_pantallas_principales_cargan(self):
        self.ingresar(Rol.ADMIN)
        for nombre in ["dashboard:panel", "recepcion:lista", "movimientos:salida", "movimientos:transferencia",
                       "movimientos:historial", "conteos:lista", "inventario:consulta", "alertas:lista",
                       "ubicaciones:lista", "ubicaciones:mapa", "catalogo:lista", "reportes:reportes",
                       "integracion_sap:exportar", "bitacora:lista", "usuarios:lista"]:
            with self.subTest(nombre=nombre):
                self.assertEqual(self.client.get(reverse(nombre)).status_code, 200)

    def test_reportes_en_pdf_y_excel(self):
        self.ingresar(Rol.ENCARGADO)
        for formato in ("pdf", "xlsx"):
            r = self.client.get(reverse("reportes:reportes"), {"tipo": "movimientos", "formato": formato})
            self.assertEqual(r.status_code, 200)

    def test_rn14_bitacora_inalterable(self):
        b = registrar(self.usuarios[Rol.ADMIN], "PRUEBA", "detalle")
        b.detalle = "cambiado"
        with self.assertRaises(BitacoraInmutableError):
            b.save()
        with self.assertRaises(BitacoraInmutableError):
            b.delete()
