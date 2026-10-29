"""Utilidades compartidas para formularios con Bootstrap 5.3."""
from django import forms


def estilizar(form):
    """Agrega las clases de Bootstrap a todos los campos del formulario."""
    for campo in form.fields.values():
        w = campo.widget
        if isinstance(w, forms.CheckboxInput):
            css = "form-check-input"
        elif isinstance(w, (forms.Select, forms.SelectMultiple)):
            css = "form-select form-select-lg"
        else:
            css = "form-control form-control-lg"
        w.attrs["class"] = (w.attrs.get("class", "") + " " + css).strip()
    return form
