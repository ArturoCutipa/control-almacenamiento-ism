from django.test import TestCase
from django.urls import reverse

from apps import pruebas
from apps.usuarios.models import Rol

ACCIONES = {
    "recepcion:lista": {Rol.OPERARIO, Rol.ENCARGADO, Rol.ADMIN},
    "movimientos:salida": {Rol.OPERARIO, Rol.ENCARGADO, Rol.ADMIN},
    "integracion_sap:exportar": {Rol.ENCARGADO, Rol.ADMIN},
    "reportes:reportes": {Rol.PLANIFICACION, Rol.ENCARGADO, Rol.ADMIN},
    "usuarios:lista": {Rol.ADMIN},
    "inventario:consulta": {Rol.OPERARIO, Rol.ENCARGADO, Rol.PLANIFICACION, Rol.ADMIN},
}


class PanelTests(TestCase):
    def test_rf01_cada_rol_ve_solo_sus_funciones(self):
        for rol, _ in Rol.CODIGOS:
            self.client.force_login(pruebas.usuario(rol, username=f"u_{rol.lower()}"))
            html = self.client.get(reverse("dashboard:panel")).content.decode()
            for nombre, roles in ACCIONES.items():
                with self.subTest(rol=rol, accion=nombre):
                    enlace = f'href="{reverse(nombre)}"'
                    if rol in roles:
                        self.assertIn(enlace, html)
                    else:
                        self.assertNotIn(enlace, html)

    def test_indicadores_de_stock_y_ocupacion(self):
        ubic = pruebas.ubicacion(capacidad=4)
        pruebas.lote_con_stock(pruebas.producto(cajas_por_pallet=80), "L1", 120, 160, ubic)  # 2 pallets
        self.client.force_login(pruebas.usuario(Rol.ENCARGADO))
        ind = self.client.get(reverse("dashboard:panel")).context["ind"]
        self.assertEqual(ind["cajas"], 160)
        self.assertEqual(ind["pallets"], "2 / 4")
        self.assertEqual(ind["ocupacion"], 50)
