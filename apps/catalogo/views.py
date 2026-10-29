from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.bitacora.services import registrar
from apps.usuarios.permisos import ADMIN, TODOS, rol_requerido

from .forms import ProductoForm
from .models import Producto


@rol_requerido(*TODOS)
def lista(request):
    q = request.GET.get("q", "").strip()
    productos = Producto.objects.all()
    if q:
        productos = productos.filter(Q(codigo_barras__icontains=q) | Q(marca__icontains=q) |
                                     Q(sabor__icontains=q) | Q(descripcion__icontains=q))
    return render(request, "catalogo/lista.html", {"productos": productos, "q": q})


@rol_requerido(ADMIN)
def editar(request, pk=None):
    producto = get_object_or_404(Producto, pk=pk) if pk else None
    form = ProductoForm(request.POST or None, instance=producto)
    if request.method == "POST" and form.is_valid():
        producto = form.save()
        registrar(request.user, "PRODUCTO_GUARDADO", f"{producto.codigo_barras} {producto}")
        messages.success(request, f"Producto {producto} guardado.")
        return redirect("catalogo:lista")
    return render(request, "catalogo/form.html", {"form": form, "producto": producto})


@rol_requerido(*TODOS)
def buscar_codigo(request):
    """Búsqueda por código de barras para el escáner de la tablet (JSON)."""
    codigo = request.GET.get("codigo", "").strip()
    producto = Producto.objects.filter(codigo_barras=codigo, activo=True).first()
    if not producto:
        return JsonResponse({"encontrado": False, "mensaje": "Producto no registrado en el catálogo."}, status=404)
    return JsonResponse({"encontrado": True, "id": producto.id, "codigo_barras": producto.codigo_barras,
                         "nombre": str(producto), "cajas_por_pallet": producto.cajas_por_pallet})
