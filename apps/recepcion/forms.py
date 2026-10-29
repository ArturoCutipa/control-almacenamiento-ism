from django import forms

from apps.catalogo.models import Producto
from apps.core_forms import estilizar


class NuevaRecepcionForm(forms.Form):
    guia_remision = forms.CharField(label="Número de guía de remisión", max_length=30)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)


class PalletForm(forms.Form):
    codigo_barras = forms.CharField(label="Código de barras", max_length=20,
                                    widget=forms.TextInput(attrs={"inputmode": "numeric", "data-escaner": "barras",
                                                                  "data-buscar-producto": "1"}))
    numero_lote = forms.CharField(label="Número de lote", max_length=30)
    fecha_vencimiento = forms.DateField(label="Fecha de vencimiento", widget=forms.DateInput(attrs={"type": "date"}))
    cantidad_cajas = forms.IntegerField(label="Cantidad de cajas", min_value=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)

    def clean_codigo_barras(self):
        codigo = self.cleaned_data["codigo_barras"].strip()
        self.producto = Producto.objects.filter(codigo_barras=codigo, activo=True).first()
        if not self.producto:
            raise forms.ValidationError("Producto no registrado. Informe al administrador.")
        return codigo


class UbicarForm(forms.Form):
    qr_ubicacion = forms.CharField(label="Escanee el QR del estante", max_length=30,
                                   widget=forms.TextInput(attrs={"data-escaner": "qr"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)
