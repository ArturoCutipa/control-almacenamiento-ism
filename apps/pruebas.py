"""Datos de apoyo para las pruebas automáticas."""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.catalogo.models import Producto
from apps.inventario import services as inventario
from apps.ubicaciones.models import Ubicacion
from apps.usuarios.models import Rol, Usuario

CLAVE = "Prueba2026!segura"


def usuario(codigo_rol, username=None):
    rol = Rol.objects.get(codigo=codigo_rol)
    u = Usuario.objects.create_user(username=username or codigo_rol.lower(), password=CLAVE, rol=rol)
    return u


def producto(codigo="7750000000011", cajas_por_pallet=80, **extra):
    datos = {"descripcion": "Agua", "marca": "Cielo", "sabor": "Sin gas", "formato": "625 ml x 15",
             "cajas_por_pallet": cajas_por_pallet}
    datos.update(extra)
    return Producto.objects.create(codigo_barras=codigo, **datos)


def ubicacion(zona="A", nivel=1, posicion=1, capacidad=4):
    return Ubicacion.objects.create(zona=zona, nivel=nivel, posicion=posicion, capacidad_pallets=capacidad)


def lote_con_stock(prod, numero, dias, cajas, ubic):
    hoy = timezone.localdate()
    with transaction.atomic():
        lote = inventario.obtener_o_crear_lote(prod, numero, hoy + timedelta(days=dias))
        inventario.incrementar(lote, ubic, cajas)
    return lote
