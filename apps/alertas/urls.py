from django.urls import path

from . import views

app_name = "alertas"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("generar/", views.generar, name="generar"),
    path("<int:pk>/atender/", views.atender, name="atender"),
]
