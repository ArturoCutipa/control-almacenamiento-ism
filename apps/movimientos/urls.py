from django.urls import path

from . import views

app_name = "movimientos"

urlpatterns = [
    path("", views.historial, name="historial"),
    path("salida/", views.salida, name="salida"),
    path("transferencia/", views.transferencia, name="transferencia"),
]
