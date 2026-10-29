from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, render

from apps.usuarios.permisos import TODOS, rol_requerido

from .models import Lote, Stock


@rol_requerido(*TODOS)
def consulta(request):
    """Consulta de stock por producto, lote y ubicación (RF-12)."""
    q = request.GET.get("q", "").strip()
    stocks = (Stock.objects.filter(cantidad_cajas__gt=0)
              .select_related("lote__producto", "ubicacion")
              .order_by("lote__producto__marca", "lote__fecha_vencimiento", "ubicacion__codigo_qr"))
    if q:
        stocks = stocks.filter(Q(lote__producto__codigo_barras=q) | Q(lote__numero_lote__icontains=q) |
                               Q(lote__producto__marca__icontains=q) | Q(lote__producto__sabor__icontains=q) |
                               Q(ubicacion__codigo_qr__iexact=q))
    total = stocks.aggregate(t=Sum("cantidad_cajas"))["t"] or 0
    return render(request, "inventario/consulta.html", {"stocks": stocks[:300], "q": q, "total": total})


@rol_requerido(*TODOS)
def detalle_lote(request, pk):
    lote = get_object_or_404(Lote.objects.select_related("producto"), pk=pk)
    stocks = lote.stocks.filter(cantidad_cajas__gt=0).select_related("ubicacion")
    movimientos = lote.movimientos.select_related("usuario", "ubicacion_origen", "ubicacion_destino")[:50]
    return render(request, "inventario/lote.html", {"lote": lote, "stocks": stocks, "movimientos": movimientos})
