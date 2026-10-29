from django import forms

from apps.core_forms import estilizar

from .models import Ubicacion


class UbicacionForm(forms.ModelForm):
    class Meta:
        model = Ubicacion
        fields = ["zona", "nivel", "posicion", "capacidad_pallets", "activa"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)

    def clean_zona(self):
        return self.cleaned_data["zona"].strip().upper()

    def clean(self):
        datos = super().clean()
        zona, nivel, posicion = datos.get("zona"), datos.get("nivel"), datos.get("posicion")
        if zona and nivel and posicion:
            existe = Ubicacion.objects.filter(zona=zona, nivel=nivel, posicion=posicion).exclude(pk=self.instance.pk)
            if existe.exists():
                raise forms.ValidationError("Ya existe una ubicación con esa zona, nivel y posición.")
        cap = datos.get("capacidad_pallets")
        if self.instance.pk and cap and cap < self.instance.pallets_ocupados():
            self.add_error("capacidad_pallets", "La capacidad no puede ser menor que los pallets ocupados actualmente.")
        return datos
