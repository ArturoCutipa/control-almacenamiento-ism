from django.db import migrations

ROLES = [
    ("ADMIN", "Administrador"),
    ("ENCARGADO", "Encargado de almacén"),
    ("OPERARIO", "Operario de almacén"),
    ("PLANIFICACION", "Planificación / Comercial"),
]


def crear_roles(apps, schema_editor):
    Rol = apps.get_model("usuarios", "Rol")
    for codigo, nombre in ROLES:
        Rol.objects.get_or_create(codigo=codigo, defaults={"nombre": nombre})


class Migration(migrations.Migration):
    dependencies = [("usuarios", "0001_initial")]

    operations = [migrations.RunPython(crear_roles, migrations.RunPython.noop)]
