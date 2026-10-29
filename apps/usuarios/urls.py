from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("ingresar/", views.LoginView.as_view(), name="login"),
    path("salir/", views.LogoutView.as_view(), name="logout"),
    path("usuarios/", views.lista, name="lista"),
    path("usuarios/nuevo/", views.editar, name="nuevo"),
    path("usuarios/<int:pk>/", views.editar, name="editar"),
    path("usuarios/<int:pk>/estado/", views.cambiar_estado, name="estado"),
]
