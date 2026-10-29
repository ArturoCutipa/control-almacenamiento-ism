from django import forms

from apps.core_forms import estilizar

from .models import Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["codigo_barras", "descripcion", "marca", "sabor", "formato", "cajas_por_pallet", "activo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)
        self.fields["codigo_barras"].widget.attrs.update({"inputmode": "numeric", "data-escaner": "barras"})
