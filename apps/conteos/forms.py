from django import forms

from apps.core_forms import estilizar


class AbrirConteoForm(forms.Form):
    descripcion = forms.CharField(label="Descripción (zona o familia de productos)", max_length=120, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)


class RegistroConteoForm(forms.Form):
    qr_ubicacion = forms.CharField(label="QR de la ubicación", max_length=30,
                                   widget=forms.TextInput(attrs={"data-escaner": "qr"}))
    numero_lote = forms.CharField(label="Número de lote", max_length=30)
    codigo_barras = forms.CharField(label="Código de barras del producto", max_length=20,
                                    widget=forms.TextInput(attrs={"inputmode": "numeric", "data-escaner": "barras"}))
    cant_fisica = forms.IntegerField(label="Cajas contadas", min_value=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)


class RevisionForm(forms.Form):
    motivo = forms.CharField(label="Motivo", widget=forms.Textarea(attrs={"rows": 2}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)
