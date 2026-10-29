from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.bitacora.services import registrar

from .forms import LoginForm, UsuarioForm
from .models import Usuario
from .permisos import ADMIN, rol_requerido


class LoginView(auth_views.LoginView):
    template_name = "usuarios/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        registrar(self.request.user, "INICIO_SESION", "Inicio de sesión")
        return respuesta


class LogoutView(auth_views.LogoutView):
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            registrar(request.user, "CIERRE_SESION", "Cierre de sesión")
        return super().post(request, *args, **kwargs)


@rol_requerido(ADMIN)
def lista(request):
    q = request.GET.get("q", "").strip()
    usuarios = Usuario.objects.select_related("rol")
    if q:
        usuarios = usuarios.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
    return render(request, "usuarios/lista.html", {"usuarios": usuarios, "q": q})


@rol_requerido(ADMIN)
def editar(request, pk=None):
    usuario = get_object_or_404(Usuario, pk=pk) if pk else None
    form = UsuarioForm(request.POST or None, instance=usuario)
    if request.method == "POST" and form.is_valid():
        nuevo = usuario is None
        usuario = form.save()
        registrar(request.user, "USUARIO_CREADO" if nuevo else "USUARIO_EDITADO",
                  f"{usuario.username} - rol {usuario.rol}")
        messages.success(request, f"Usuario {usuario.username} guardado.")
        return redirect("usuarios:lista")
    return render(request, "usuarios/form.html", {"form": form, "usuario": usuario})


@require_POST
@rol_requerido(ADMIN)
def cambiar_estado(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if usuario == request.user:
        messages.error(request, "No puede desactivar su propia cuenta.")
        return redirect("usuarios:lista")
    usuario.is_active = not usuario.is_active
    usuario.save(update_fields=["is_active"])
    estado = "activado" if usuario.is_active else "desactivado"
    registrar(request.user, "USUARIO_ESTADO", f"{usuario.username} {estado}")
    messages.success(request, f"Usuario {usuario.username} {estado}.")
    return redirect("usuarios:lista")
