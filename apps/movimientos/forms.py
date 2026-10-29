from django import forms

from apps.catalogo.models import Producto
from apps.core_forms import estilizar


class SolicitudSalidaForm(forms.Form):
    codigo_barras = forms.CharField(label="Código de barras del producto", max_length=20,
                                    widget=forms.TextInput(attrs={"inputmode": "numeric", "data-escaner": "barras"}))
    cantidad = forms.IntegerField(label="Cantidad de cajas", min_value=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)

    def clean_codigo_barras(self):
        codigo = self.cleaned_data["codigo_barras"].strip()
        producto = Producto.objects.filter(codigo_barras=codigo, activo=True).first()
        if not producto:
            raise forms.ValidationError("Producto no registrado en el catálogo.")
        self.producto = producto
        return codigo


class ConfirmarSalidaForm(forms.Form):
    stock = forms.IntegerField(widget=forms.HiddenInput)
    cantidad = forms.IntegerField(widget=forms.HiddenInput, min_value=1)
    qr_ubicacion = forms.CharField(label="Escanee el QR de la ubicación", max_length=30,
                                   widget=forms.TextInput(attrs={"data-escaner": "qr"}))
    motivo = forms.CharField(label="Motivo (obligatorio si no usa el lote sugerido)", required=False,
                             widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)


class TransferenciaForm(forms.Form):
    qr_origen = forms.CharField(label="QR de la ubicación de origen", max_length=30,
                                widget=forms.TextInput(attrs={"data-escaner": "qr"}))
    numero_lote = forms.CharField(label="Número de lote", max_length=30)
    cantidad = forms.IntegerField(label="Cantidad de cajas", min_value=1)
    qr_destino = forms.CharField(label="QR de la ubicación de destino", max_length=30,
                                 widget=forms.TextInput(attrs={"data-escaner": "qr"}))
    motivo = forms.CharField(label="Motivo", required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)
