from django.urls import path

from . import views

app_name = "recepcion"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("<int:pk>/", views.detalle, name="detalle"),
    path("<int:pk>/finalizar/", views.finalizar, name="finalizar"),
    path("pallet/<int:pk>/ubicar/", views.ubicar, name="ubicar"),
]
