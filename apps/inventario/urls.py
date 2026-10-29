from django.urls import path

from . import views

app_name = "inventario"

urlpatterns = [
    path("", views.consulta, name="consulta"),
    path("lote/<int:pk>/", views.detalle_lote, name="lote"),
]
