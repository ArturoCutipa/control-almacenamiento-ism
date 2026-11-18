from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from .models import Rol, Usuario


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Usuario o contraseña incorrectos.",
        "inactive": "Su cuenta está desactivada. Comuníquese con el administrador.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control form-control-lg", "autofocus": True})
        self.fields["password"].widget.attrs.update({"class": "form-control form-control-lg"})


class UsuarioForm(forms.ModelForm):
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput, required=False,
                                help_text="Obligatoria al crear. Déjela vacía para no cambiarla.")
    password2 = forms.CharField(label="Repetir contraseña", widget=forms.PasswordInput, required=False)

    class Meta:
        model = Usuario
        fields = ["username", "first_name", "last_name", "email", "rol", "is_active"]
        labels = {"username": "Usuario", "first_name": "Nombres", "last_name": "Apellidos", "is_active": "Activo"}

    def __init__(self, *args, editor=None, **kwargs):
        self.editor = editor  # usuario que está guardando el formulario
        super().__init__(*args, **kwargs)
        self.fields["rol"].required = True
        self.fields["rol"].queryset = Rol.objects.all()
        for nombre, campo in self.fields.items():
            css = "form-check-input" if isinstance(campo.widget, forms.CheckboxInput) else "form-control"
            if isinstance(campo.widget, forms.Select):
                css = "form-select"
            campo.widget.attrs.setdefault("class", css)

    def clean(self):
        datos = super().clean()
        if self.editor is not None and self.instance.pk and self.instance.pk == self.editor.pk:
            if not datos.get("is_active", True):
                self.add_error("is_active", "No puede desactivar su propia cuenta.")
            rol = datos.get("rol")
            if rol is not None and rol.codigo != Rol.ADMIN and not self.instance.is_superuser:
                self.add_error("rol", "No puede quitarse el rol de Administrador a sí mismo.")
        p1, p2 = datos.get("password1"), datos.get("password2")
        if not self.instance.pk and not p1:
            self.add_error("password1", "Ingrese una contraseña para el nuevo usuario.")
        if p1 or p2:
            if p1 != p2:
                self.add_error("password2", "Las contraseñas no coinciden.")
            else:
                validate_password(p1, self.instance)
        return datos

    def save(self, commit=True):
        usuario = super().save(commit=False)
        if self.cleaned_data.get("password1"):
            usuario.set_password(self.cleaned_data["password1"])
        if commit:
            usuario.save()
        return usuario
