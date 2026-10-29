"""Carga datos de demostración para el piloto (solo desarrollo)."""
import os
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.alertas.services import generar_alertas
from apps.catalogo.models import Producto
from apps.inventario.models import Stock
from apps.recepcion import services as recepcion
from apps.ubicaciones.models import Ubicacion
from apps.usuarios.models import Rol, Usuario

USUARIOS = [
    ("admin", "Ana", "Torres", Rol.ADMIN),
    ("encargado", "Luis", "Mamani", Rol.ENCARGADO),
    ("operario", "Jorge", "Flores", Rol.OPERARIO),
    ("planificacion", "Rosa", "Quispe", Rol.PLANIFICACION),
]

PRODUCTOS = [
    ("7750182000011", "Agua de mesa sin gas", "Cielo", "Sin gas", "625 ml x 15", 80),
    ("7750182000028", "Agua de mesa con gas", "Cielo", "Con gas", "625 ml x 15", 80),
    ("7750182000035", "Bebida gasificada", "Kola Real", "Original", "3 L x 6", 60),
    ("7750182000042", "Bebida gasificada", "Kola Real", "Naranja", "500 ml x 12", 90),
    ("7750182000059", "Bebida gasificada", "Oro", "Amarilla", "3 L x 6", 60),
    ("7750182000066", "Bebida rehidratante", "Sporade", "Tropical", "500 ml x 12", 90),
]


class Command(BaseCommand):
    help = "Crea usuarios, productos, ubicaciones, lotes y stock de demostración."

    @transaction.atomic
    def handle(self, *args, **opciones):
        clave = os.environ.get("DEMO_PASSWORD", "Ism2026!demo")
        roles = {r.codigo: r for r in Rol.objects.all()}
        for username, nombre, apellido, codigo in USUARIOS:
            u, creado = Usuario.objects.get_or_create(username=username, defaults={
                "first_name": nombre, "last_name": apellido, "rol": roles[codigo],
                "is_staff": codigo == Rol.ADMIN, "is_superuser": codigo == Rol.ADMIN})
            if creado:
                u.set_password(clave)
                u.save()
        for codigo, desc, marca, sabor, formato, cxp in PRODUCTOS:
            Producto.objects.get_or_create(codigo_barras=codigo, defaults={
                "descripcion": desc, "marca": marca, "sabor": sabor, "formato": formato, "cajas_por_pallet": cxp})
        for zona in ("A", "B"):
            for nivel in (1, 2, 3):
                for pos in range(1, 7):
                    Ubicacion.objects.get_or_create(zona=zona, nivel=nivel, posicion=pos,
                                                    defaults={"capacidad_pallets": 4})
        if Stock.objects.exists():
            self.stdout.write("Ya existe stock; se omite la recepción de demostración.")
            return
        operario = Usuario.objects.get(username="operario")
        hoy = timezone.localdate()
        rec = recepcion.iniciar_recepcion("T001-000451", operario)
        carga = [  # (producto, lote, días para vencer, cajas, ubicación)
            ("7750182000011", "L260901A", 12, 160, "ISM-A-1-01"),
            ("7750182000011", "L261005B", 75, 240, "ISM-A-1-02"),
            ("7750182000028", "L260920C", 25, 80, "ISM-A-1-03"),
            ("7750182000035", "L261110D", 110, 120, "ISM-A-2-01"),
            ("7750182000042", "L261015E", 60, 180, "ISM-B-1-01"),
            ("7750182000059", "L261201F", 140, 60, "ISM-B-1-02"),
            ("7750182000066", "L260910G", 5, 90, "ISM-B-2-01"),
        ]
        for codigo, lote, dias, cajas, qr in carga:
            det = recepcion.registrar_pallet(
                recepcion=rec, producto=Producto.objects.get(codigo_barras=codigo), numero_lote=lote,
                fecha_vencimiento=hoy + timedelta(days=dias), cantidad_cajas=cajas, usuario=operario)
            recepcion.asignar_ubicacion(detalle=det, ubicacion=Ubicacion.objects.get(codigo_qr=qr), usuario=operario)
        recepcion.finalizar_recepcion(rec, operario)
        generar_alertas()
        self.stdout.write(self.style.SUCCESS(
            "Datos de demostración cargados. Usuarios: admin, encargado, operario, planificacion "
            "(contraseña: DEMO_PASSWORD del archivo .env)."))
