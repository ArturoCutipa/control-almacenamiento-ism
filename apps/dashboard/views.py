from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from apps.alertas.models import Alerta
from apps.conteos.models import DetalleConteo
from apps.inventario.models import Stock
from apps.movimientos.models import Movimiento
from apps.recepcion.models import Recepcion
from apps.ubicaciones.models import Ubicacion
from apps.usuarios.permisos import TODOS, rol_requerido


@rol_requerido(*TODOS)
def panel(request):
    """Panel con las funciones e indicadores del rol (RF-20)."""
    hoy = timezone.localdate()
    ubicaciones = list(Ubicacion.objects.filter(activa=True).prefetch_related("stocks__lote__producto"))
    capacidad = sum(u.capacidad_pallets for u in ubicaciones)
    ocupados = sum(u.pallets_ocupados() for u in ubicaciones)
    indicadores = {
        "alertas": Alerta.objects.filter(atendida=False).count(),
        "vencidos": Alerta.objects.filter(atendida=False, tipo=Alerta.VENCIDO).count(),
        "recepciones_hoy": Recepcion.objects.filter(fecha_hora_inicio__date=hoy).count(),
        "recepciones_abiertas": Recepcion.objects.filter(fecha_hora_fin__isnull=True).count(),
        "pendientes_ajuste": DetalleConteo.objects.filter(estado=DetalleConteo.PENDIENTE).count(),
        "cajas": Stock.objects.aggregate(t=Sum("cantidad_cajas"))["t"] or 0,
        "ocupacion": round(ocupados * 100 / capacidad) if capacidad else 0,
        "pallets": f"{ocupados} / {capacidad}",
        "movimientos_hoy": Movimiento.objects.filter(fecha_hora__date=hoy).count(),
    }
    ultimos = Movimiento.objects.select_related("lote__producto", "usuario")[:8]
    proximas = Alerta.objects.filter(atendida=False).select_related("lote__producto")[:5]
    return render(request, "dashboard/panel.html", {"ind": indicadores, "ultimos": ultimos, "proximas": proximas})
