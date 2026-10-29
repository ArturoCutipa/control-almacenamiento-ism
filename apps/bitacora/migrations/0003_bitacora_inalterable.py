"""RN-14: la bitácora no se edita ni se elimina; se refuerza en PostgreSQL con un trigger."""
from django.db import migrations

CREAR = """
CREATE OR REPLACE FUNCTION bitacora_inalterable() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Los registros de la bitácora no se pueden modificar ni eliminar (RN-14)';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER bitacora_sin_cambios
BEFORE UPDATE OR DELETE ON bitacora_bitacora
FOR EACH ROW EXECUTE FUNCTION bitacora_inalterable();
"""

QUITAR = """
DROP TRIGGER IF EXISTS bitacora_sin_cambios ON bitacora_bitacora;
DROP FUNCTION IF EXISTS bitacora_inalterable();
"""


def aplicar(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(CREAR)


def revertir(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(QUITAR)


class Migration(migrations.Migration):
    dependencies = [("bitacora", "0002_initial")]

    operations = [migrations.RunPython(aplicar, revertir)]
