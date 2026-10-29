from django.urls import path

from . import views

app_name = "ubicaciones"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nueva/", views.editar, name="nueva"),
    path("<int:pk>/", views.editar, name="editar"),
    path("etiquetas/", views.etiquetas, name="etiquetas"),
    path("mapa/", views.mapa, name="mapa"),
    path("buscar/", views.buscar_qr, name="buscar"),
]
