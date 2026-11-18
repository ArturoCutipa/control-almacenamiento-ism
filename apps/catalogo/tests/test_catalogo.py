from django.test import TestCase
from django.urls import reverse

from apps import pruebas
from apps.catalogo.forms import ProductoForm
from apps.catalogo.models import Producto
from apps.usuarios.models import Rol

DATOS = {"codigo_barras": "7750182000011", "descripcion": "Agua de mesa", "marca": "Cielo", "sabor": "Sin gas",
         "formato": "625 ml x 15", "cajas_por_pallet": 80, "activo": True}


class ProductoFormTests(TestCase):
    def test_producto_valido(self):
        self.assertTrue(ProductoForm(DATOS).is_valid())

    def test_codigo_de_barras_solo_digitos_de_8_a_14(self):
        for codigo in ("12345", "ABC1234567890", "123456789012345"):
            with self.subTest(codigo=codigo):
                form = ProductoForm({**DATOS, "codigo_barras": codigo})
                self.assertFalse(form.is_valid())
                self.assertIn("codigo_barras", form.errors)

    def test_codigo_de_barras_unico(self):
        ProductoForm(DATOS).save()
        form = ProductoForm({**DATOS, "sabor": "Con gas"})
        self.assertFalse(form.is_valid())
        self.assertIn("codigo_barras", form.errors)

    def test_cajas_por_pallet_mayor_que_cero(self):
        form = ProductoForm({**DATOS, "cajas_por_pallet": 0})
        self.assertFalse(form.is_valid())


class CatalogoVistasTests(TestCase):
    def setUp(self):
        self.producto = pruebas.producto(codigo="7750182000011")

    def test_solo_el_administrador_registra_productos(self):
        for rol, esperado in ((Rol.ADMIN, 200), (Rol.ENCARGADO, 403), (Rol.OPERARIO, 403)):
            with self.subTest(rol=rol):
                self.client.force_login(pruebas.usuario(rol, username=f"u_{rol.lower()}"))
                self.assertEqual(self.client.get(reverse("catalogo:nuevo")).status_code, esperado)

    def test_registrar_producto(self):
        self.client.force_login(pruebas.usuario(Rol.ADMIN))
        r = self.client.post(reverse("catalogo:nuevo"), {**DATOS, "codigo_barras": "7750182000028"})
        self.assertRedirects(r, reverse("catalogo:lista"))
        self.assertTrue(Producto.objects.filter(codigo_barras="7750182000028").exists())

    def test_busqueda_por_codigo_de_barras_para_el_escaner(self):
        self.client.force_login(pruebas.usuario(Rol.OPERARIO))
        r = self.client.get(reverse("catalogo:buscar"), {"codigo": "7750182000011"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["id"], self.producto.id)
        r = self.client.get(reverse("catalogo:buscar"), {"codigo": "0000000000000"})
        self.assertEqual(r.status_code, 404)
        self.assertFalse(r.json()["encontrado"])

    def test_producto_inactivo_no_se_encuentra_al_escanear(self):
        Producto.objects.filter(pk=self.producto.pk).update(activo=False)
        self.client.force_login(pruebas.usuario(Rol.OPERARIO))
        r = self.client.get(reverse("catalogo:buscar"), {"codigo": "7750182000011"})
        self.assertEqual(r.status_code, 404)
