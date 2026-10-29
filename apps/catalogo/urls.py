from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.editar, name="nuevo"),
    path("<int:pk>/", views.editar, name="editar"),
    path("buscar/", views.buscar_codigo, name="buscar"),
]
