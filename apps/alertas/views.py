from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.usuarios.permisos import ADMIN, ENCARGADO, PLANIFICACION, TODOS, rol_requerido

from . import services
from .models import Alerta


@rol_requerido(*TODOS)
def lista(request):
    ver = request.GET.get("ver", "abiertas")
    alertas = Alerta.objects.select_related("lote__producto", "atendida_por").prefetch_related("lote__stocks__ubicacion")
    alertas = alertas.filter(atendida=(ver == "atendidas"))
    return render(request, "alertas/lista.html", {"alertas": alertas, "ver": ver})


@require_POST
@rol_requerido(PLANIFICACION, ENCARGADO, ADMIN)
def atender(request, pk):
    alerta = get_object_or_404(Alerta, pk=pk, atendida=False)
    services.atender(alerta, request.user, request.POST.get("comentario", ""))
    messages.success(request, "Alerta marcada como atendida.")
    return redirect("alertas:lista")


@require_POST
@rol_requerido(ENCARGADO, ADMIN)
def generar(request):
    r = services.generar_alertas()
    messages.success(request, f"Revisión completada: {r['nuevas']} alertas nuevas, {r['vencidos']} lotes vencidos.")
    return redirect("alertas:lista")
