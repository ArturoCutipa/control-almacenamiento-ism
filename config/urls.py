from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.dashboard.urls")),
    path("cuenta/", include("apps.usuarios.urls")),
    path("catalogo/", include("apps.catalogo.urls")),
    path("ubicaciones/", include("apps.ubicaciones.urls")),
    path("inventario/", include("apps.inventario.urls")),
    path("recepcion/", include("apps.recepcion.urls")),
    path("movimientos/", include("apps.movimientos.urls")),
    path("conteos/", include("apps.conteos.urls")),
    path("alertas/", include("apps.alertas.urls")),
    path("reportes/", include("apps.reportes.urls")),
    path("sap/", include("apps.integracion_sap.urls")),
    path("bitacora/", include("apps.bitacora.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "ISM - Control de Almacén"
admin.site.site_title = "ISM Almacén"
