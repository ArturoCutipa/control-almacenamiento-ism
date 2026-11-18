# Sistema de Control de Almacenamiento e Inventario – ISM Tacna

Aplicación web (Django 5.2 + PostgreSQL 17) para registrar la recepción, ubicación, salida FEFO,
transferencias, conteos físicos y alertas de vencimiento del almacén de ISM – Tacna, y generar el
archivo de carga para SAP. Pensada para usarse desde tablets con lector de códigos (cámara o lector
inalámbrico).

## Requisitos

- Python 3.10 o superior
- Docker (para PostgreSQL) o un PostgreSQL 16/17 propio

## Instalación (desarrollo)

```bash
git clone https://github.com/ArturoCutipa/control-almacenamiento-ism.git
cd control-almacenamiento-ism

python -m venv .venv
# Windows: .venv\Scripts\activate    ·    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # Windows: copy .env.example .env
docker compose up -d          # PostgreSQL en el puerto 5434

python manage.py migrate
python manage.py cargar_datos_demo   # opcional: usuarios, productos, ubicaciones y stock de prueba
python manage.py runserver
```

Abrir <http://127.0.0.1:8000>. Los usuarios de demostración son `admin`, `encargado`, `operario` y
`planificacion`, con la contraseña `DEMO_PASSWORD` del archivo `.env`.

## Pruebas

```bash
python manage.py test
```

## Tareas programadas

La revisión de vencimientos (RF-12) se ejecuta sola la primera vez que se abre el panel o la lista
de alertas en el día. En el servidor también puede programarse con cron:

```cron
0 6 * * * cd /ruta/al/proyecto && .venv/bin/python manage.py generar_alertas
```

## Producción

Con `DJANGO_DEBUG=False` es obligatorio definir `DJANGO_SECRET_KEY` con una clave propia; además se
activan las cookies seguras, HSTS y la redirección a HTTPS (detrás de Nginx). Ejecutar
`python manage.py collectstatic` y servir con `gunicorn config.wsgi`.

## Requerimientos funcionales y dónde se implementan

| RF | Caso de uso | Ruta | Módulo | Roles con acceso |
|----|-------------|------|--------|------------------|
| RF-01 | CU-01 Iniciar sesión y panel por rol | `/cuenta/ingresar/`, `/` | `usuarios`, `dashboard` | Todos |
| RF-02 | CU-02 Gestionar usuarios y roles | `/cuenta/usuarios/` | `usuarios` | Administrador |
| RF-03 | CU-03 Gestionar productos | `/catalogo/` | `catalogo` | Administrador (consulta: todos) |
| RF-04 | CU-04 Gestionar ubicaciones | `/ubicaciones/` | `ubicaciones` | Encargado, Administrador |
| RF-05 | CU-05 Imprimir etiquetas QR (PDF) | `/ubicaciones/etiquetas/` | `ubicaciones` | Encargado, Administrador |
| RF-06 | CU-06 Registrar recepción | `/recepcion/` | `recepcion` | Operario, Encargado, Administrador |
| RF-07 | CU-07 Asignar ubicación (valida capacidad) | `/recepcion/pallet/<id>/ubicar/` | `recepcion` | Operario, Encargado, Administrador |
| RF-08 | CU-08 Registrar salida FEFO | `/movimientos/salida/` | `movimientos` | Operario, Encargado, Administrador |
| RF-09 | CU-09 Registrar transferencia | `/movimientos/transferencia/` | `movimientos` | Operario, Encargado, Administrador |
| RF-10 | CU-10 Consultar stock y ubicación | `/inventario/` | `inventario` | Todos |
| RF-11 | CU-11 Mapa del almacén | `/ubicaciones/mapa/` | `ubicaciones` | Todos |
| RF-12 | CU-12 Alertas de vencimiento | `/alertas/` | `alertas` | Todos (atender: Planificación, Encargado, Administrador) |
| RF-13 | CU-13 Registrar conteo físico | `/conteos/` | `conteos` | Operario, Encargado, Administrador |
| RF-14 | CU-14 Aprobar/rechazar ajuste con motivo | `/conteos/<id>/` | `conteos` | Encargado, Administrador |
| RF-15 | CU-15 Exportar a SAP (Excel) | `/sap/` | `integracion_sap` | Encargado, Administrador |
| RF-16 | CU-16 Reportes PDF y Excel | `/reportes/` | `reportes` | Planificación, Encargado, Administrador |
| RF-17 | CU-17 Consultar bitácora | `/bitacora/` | `bitacora` | Administrador |
