from django.urls import path

from . import views

app_name = "integracion_sap"

urlpatterns = [
    path("", views.exportar, name="exportar"),
    path("<int:pk>/descargar/", views.descargar, name="descargar"),
]
