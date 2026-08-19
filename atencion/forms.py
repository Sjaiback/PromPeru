from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from .models import (
    Atencion,
    Empresa,
    PerfilAsesor,
    Region,
    Responsable,
    Sector,
    TIPOS_DOCUMENTO,
)

DETALLE_EMPRESA = [
    "sector",
    "oferta_producto_servicio",
    "region",
    "nombre",
    "tipo_personeria",
    "nombres_apellidos",
    "cargo",
    "tipo_usuario",
    "telefono",
    "email",
]


def opciones_catalogo(clave, queryset):
    """Avoid remote database round-trips for catalogues that rarely change."""
    opciones = cache.get(clave)
    if opciones is None:
        opciones = list(queryset.values_list("pk", "nombre"))
        cache.set(clave, opciones, 300)
    return opciones


class AtencionRegistroForm(forms.Form):
    tipo_documento = forms.ChoiceField(
        label="Tipo de documento",
        choices=TIPOS_DOCUMENTO,
    )
    numero_documento = forms.CharField(
        label="Número de documento",
        max_length=30,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )
    es_estudiante = forms.BooleanField(
        label="¿Eres estudiante?", required=False
    )
    actualizar_datos = forms.BooleanField(label="Actualizar mis datos", required=False)
    tipo_atencion = forms.ChoiceField(
        label="2. TIPO DE ATENCIÓN",
        choices=Atencion._meta.get_field("tipo_atencion").choices,
    )
    responsable = forms.ModelChoiceField(
        label="3. RESPONSABLE CON QUIEN DESEA ENTREVISTARSE",
        queryset=Responsable.objects.none(),
        empty_label="Seleccionar una opción",
    )
    sector = forms.ModelChoiceField(
        label="SECTOR AL QUE PERTENECE",
        queryset=Sector.objects.none(),
        required=False,
        empty_label="Seleccionar una opción",
    )
    oferta_producto_servicio = forms.CharField(
        label="OFERTA, PRODUCTO O SERVICIO QUE OFRECE",
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
    )
    region = forms.ModelChoiceField(
        label="REGIÓN",
        queryset=Region.objects.none(),
        required=False,
        empty_label="Seleccionar una opción",
    )
    nombre = forms.CharField(
        label="NOMBRE DE LA EMPRESA / INSTITUCIÓN / PERSONA NATURAL",
        max_length=255,
        required=False,
    )
    tipo_personeria = forms.ChoiceField(
        label="TIPO DE PERSONERÍA",
        choices=[("", "Seleccionar una opción")]
        + list(Empresa._meta.get_field("tipo_personeria").choices),
        required=False,
    )
    nombres_apellidos = forms.CharField(
        label="NOMBRES Y APELLIDOS", required=False, max_length=200
    )
    cargo = forms.CharField(label="CARGO", required=False, max_length=120)
    tipo_usuario = forms.ChoiceField(
        label="TIPO DE USUARIO",
        choices=[("", "Seleccionar una opción")]
        + list(Empresa._meta.get_field("tipo_usuario").choices),
        required=False,
    )
    telefono = forms.CharField(
        label="TELÉFONO / CELULAR", max_length=30, required=False
    )
    email = forms.EmailField(label="E-MAIL", required=False)
    tema_consulta = forms.CharField(
        label="TEMA DE CONSULTA",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )

    def __init__(self, *args, asesor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.asesor = asesor
        self.fields["responsable"].queryset = Responsable.objects.filter(activo=True)
        self.fields["sector"].queryset = Sector.objects.filter(activo=True)
        self.fields["region"].queryset = Region.objects.filter(activo=True)
        self.fields["responsable"].choices = [("", "Seleccionar una opción")] + opciones_catalogo(
            "catalogo:responsables", Responsable.objects.filter(activo=True)
        )
        self.fields["sector"].choices = [("", "Seleccionar una opción")] + opciones_catalogo(
            "catalogo:sectores", Sector.objects.filter(activo=True)
        )
        self.fields["region"].choices = [("", "Seleccionar una opción")] + opciones_catalogo(
            "catalogo:regiones", Region.objects.filter(activo=True)
        )
        if asesor and getattr(asesor, "responsable", None):
            self.fields["responsable"].initial = asesor.responsable
            self.fields["responsable"].disabled = True
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
            if name in DETALLE_EMPRESA:
                field.widget.attrs["data-company-detail"] = "1"

    def clean(self):
        data = super().clean()
        tipo = data.get("tipo_documento")
        doc = (data.get("numero_documento") or "").strip()
        if tipo == "RUC" and (not doc.isdigit() or len(doc) != 11):
            self.add_error(
                "numero_documento", "El RUC debe tener exactamente 11 dígitos."
            )
        if tipo == "DNI" and (not doc.isdigit() or len(doc) != 8):
            self.add_error(
                "numero_documento", "El DNI debe tener exactamente 8 dígitos."
            )
        if tipo == "Carné de Extranjería" and not doc:
            self.add_error("numero_documento", "Ingresa el número del carné.")
        if tipo == "Pasaporte" and not doc:
            self.add_error("numero_documento", "Ingresa el número de pasaporte.")
        estudiante = bool(data.get("es_estudiante") and tipo == "DNI")
        if estudiante:
            sector, _ = Sector.objects.get_or_create(
                nombre__iexact="Otros", defaults={"nombre": "Otros", "orden": 999}
            )
            data.update(
                {
                    "tipo_atencion": "Presencial",
                    "sector": sector,
                    "oferta_producto_servicio": "Otros",
                    "tipo_usuario": "Estudiante",
                    "tipo_personeria": "Persona Natural",
                    "cargo": "Estudiante",
                    "tema_consulta": "Otros",
                }
            )
        self.empresa_existente = (
            Empresa.objects.filter(tipo_documento=tipo, numero_documento=doc).first()
            if doc
            else None
        )
        requiere_detalle = (
            not self.empresa_existente or data.get("actualizar_datos") or estudiante
        )
        if requiere_detalle:
            for name in [
                "sector",
                "oferta_producto_servicio",
                "region",
                "nombre",
                "tipo_usuario",
                "telefono",
                "email",
            ]:
                if not data.get(name):
                    self.add_error(
                        name,
                        "Este dato es obligatorio para registrar o actualizar el contacto.",
                    )
        return data

    def save(self, user=None):
        d = self.cleaned_data
        empresa = self.empresa_existente
        defaults = {k: d[k] for k in DETALLE_EMPRESA if k in d}
        if not empresa:
            empresa = Empresa.objects.create(
                tipo_documento=d["tipo_documento"],
                numero_documento=d["numero_documento"],
                **defaults
            )
        elif d.get("actualizar_datos"):
            for key, value in defaults.items():
                setattr(empresa, key, value)
            empresa.save()
        responsable = (
            self.asesor.responsable
            if self.asesor and self.asesor.responsable
            else d["responsable"]
        )
        return Atencion.objects.create(
            fecha=timezone.localdate(),
            tipo_atencion=d["tipo_atencion"],
            responsable=responsable,
            empresa=empresa,
            tema_consulta=d.get("tema_consulta", ""),
            registrado_por=user,
            origen="asesor" if user else "publico",
        )


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = [
            "tipo_documento",
            "numero_documento",
            "nombre",
            "tipo_personeria",
            "nombres_apellidos",
            "cargo",
            "tipo_usuario",
            "telefono",
            "email",
            "sector",
            "region",
            "oferta_producto_servicio",
            "activa",
        ]
        widgets = {"oferta_producto_servicio": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class AtencionEdicionForm(forms.ModelForm):
    class Meta:
        model = Atencion
        fields = [
            "fecha",
            "hora",
            "tipo_atencion",
            "responsable",
            "tema_consulta",
        ]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "hora": forms.TimeInput(attrs={"type": "time"}),
            "tema_consulta": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, asesor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if asesor and asesor.responsable and asesor.rol == "asesor":
            self.fields["responsable"].disabled = True
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class AsesorEmailForm(forms.ModelForm):
    """Limited account edition available only to the system administrator."""

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "email", "is_active"]
        labels = {
            "first_name": "Nombres",
            "last_name": "Apellidos",
            "email": "Correo electrónico",
            "is_active": "Cuenta activa",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class MiPerfilForm(forms.Form):
    first_name = forms.CharField(label="Nombres", max_length=150)
    last_name = forms.CharField(label="Apellidos", max_length=150)
    email = forms.EmailField(label="Correo electrónico")
    documento = forms.CharField(label="Documento", max_length=30, required=False)
    cargo = forms.CharField(label="Cargo", max_length=150, required=False)

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.perfil = getattr(user, "perfil_asesor", None)
        self.fields["first_name"].initial = user.first_name
        self.fields["last_name"].initial = user.last_name
        self.fields["email"].initial = user.email
        if self.perfil:
            self.fields["documento"].initial = self.perfil.documento
            self.fields["cargo"].initial = self.perfil.cargo
        else:
            self.fields.pop("documento")
            self.fields.pop("cargo")
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if (
            get_user_model().objects.filter(email__iexact=email)
            .exclude(pk=self.user.pk)
            .exists()
        ):
            raise forms.ValidationError("Este correo pertenece a otra cuenta.")
        return email

    def save(self):
        self.user.first_name = self.cleaned_data["first_name"].strip()
        self.user.last_name = self.cleaned_data["last_name"].strip()
        self.user.email = self.cleaned_data["email"]
        self.user.save(update_fields=["first_name", "last_name", "email"])
        if self.perfil:
            self.perfil.documento = self.cleaned_data.get("documento", "").strip()
            self.perfil.cargo = self.cleaned_data.get("cargo", "").strip()
            self.perfil.save(update_fields=["documento", "cargo"])
        return self.user


class UsuarioInternoForm(forms.Form):
    """Provision an internal account without exposing technical admin controls."""

    first_name = forms.CharField(label="Nombres", max_length=150)
    last_name = forms.CharField(label="Apellidos", max_length=150)
    username = forms.CharField(label="Usuario", max_length=150)
    email = forms.EmailField(label="Correo electrónico")
    password = forms.CharField(
        label="Contraseña temporal",
        min_length=8,
        widget=forms.PasswordInput(render_value=False),
        help_text="El usuario podrá cambiarla después con “Olvidé mi contraseña”.",
    )
    responsable = forms.ModelChoiceField(
        label="Responsable asociado",
        queryset=Responsable.objects.none(),
        empty_label="Seleccionar responsable",
    )
    documento = forms.CharField(label="Documento", max_length=30, required=False)
    cargo = forms.CharField(label="Cargo", max_length=150, required=False)
    rol = forms.ChoiceField(
        label="Rol de acceso",
        choices=[("asesor", "Asesor"), ("coordinador", "Coordinador")],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsable"].queryset = Responsable.objects.filter(
            activo=True, perfil__isnull=True, usuario__isnull=True
        ).order_by("nombre")
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if get_user_model().objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Este usuario ya está registrado.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email

    def save(self):
        data = self.cleaned_data
        user = get_user_model().objects.create_user(
            username=data["username"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            password=data["password"],
            is_active=True,
        )
        responsable = data["responsable"]
        responsable.usuario = user
        responsable.save(update_fields=["usuario"])
        perfil = PerfilAsesor.objects.create(
            usuario=user,
            responsable=responsable,
            documento=data["documento"],
            cargo=data["cargo"],
            rol=data["rol"],
            activo=True,
        )
        return user, perfil
