from django.urls import path

from . import views

app_name = "conteos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("<int:pk>/", views.detalle, name="detalle"),
    path("<int:pk>/cerrar/", views.cerrar, name="cerrar"),
    path("diferencia/<int:pk>/revisar/", views.revisar, name="revisar"),
]
