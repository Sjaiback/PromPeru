from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


def hora_local_actual():
    return timezone.localtime().time().replace(microsecond=0)

TIPOS_ATENCION = [
    (x, x)
    for x in [
        "WhatsApp",
        "Correo Electrónico",
        "Presencial",
        "Telefónica",
        "Reunión Virtual",
        "Visita a empresa",
    ]
]
TIPOS_DOCUMENTO = [(x, x) for x in ["RUC", "DNI", "Pasaporte", "Carné de Extranjería"]]
PERSONERIAS = [
    (x, x)
    for x in [
        "Persona Natural",
        "Persona Natural con Negocio",
        "Persona Jurídica",
        "Cooperativa",
        "Asociación",
    ]
]
TIPOS_USUARIO = [
    (x, x)
    for x in [
        "Empresa con Potencial Exportador",
        "Exportador",
        "Importador",
        "Representante de una Institución",
        "Investigador",
        "Estudiante",
    ]
]


class CatalogoBase(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    activo = models.BooleanField(default=True)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Region(CatalogoBase):
    class Meta(CatalogoBase.Meta):
        verbose_name = "Región"
        verbose_name_plural = "Regiones"


class Sector(CatalogoBase):
    class Meta(CatalogoBase.Meta):
        verbose_name = "Sector"
        verbose_name_plural = "Sectores"


class Responsable(CatalogoBase):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="responsable",
    )

    class Meta(CatalogoBase.Meta):
        verbose_name = "Responsable"
        verbose_name_plural = "Responsables"


class PerfilAsesor(models.Model):
    ROLES = [
        ("asesor", "Asesor"),
        ("coordinador", "Coordinador"),
        ("bi", "Administrador / BI"),
        ("admin", "Administrador general"),
    ]
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil_asesor"
    )
    responsable = models.OneToOneField(
        Responsable,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="perfil",
    )
    documento = models.CharField(max_length=30, blank=True)
    cargo = models.CharField(max_length=150, blank=True)
    rol = models.CharField(max_length=20, choices=ROLES, default="asesor")
    acceso_bi = models.BooleanField(default=False)
    puede_archivar = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username


class Empresa(models.Model):
    tipo_documento = models.CharField(
        "TIPO DE DOCUMENTO*", max_length=30, choices=TIPOS_DOCUMENTO
    )
    numero_documento = models.CharField("N° DEL DOCUMENTO", max_length=30)
    nombre = models.CharField(
        "NOMBRE DE LA EMPRESA / INSTITUCIÓN / PERSONA NATURAL*", max_length=255
    )
    tipo_personeria = models.CharField(
        "TIPO DE PERSONERÍA", max_length=40, choices=PERSONERIAS, blank=True
    )
    nombres_apellidos = models.CharField(
        "NOMBRES Y APELLIDOS", max_length=200, blank=True
    )
    cargo = models.CharField("CARGO", max_length=120, blank=True)
    tipo_usuario = models.CharField(
        "TIPO DE USUARIO*", max_length=60, choices=TIPOS_USUARIO
    )
    telefono = models.CharField(
        "TELÉFONO / CELULAR*",
        max_length=30,
        validators=[
            RegexValidator(
                r"^[0-9+() -]+$", "Ingrese solo números y signos telefónicos."
            )
        ],
    )
    email = models.EmailField("E-MAIL*")
    sector = models.ForeignKey(
        Sector, on_delete=models.PROTECT, related_name="empresas"
    )
    region = models.ForeignKey(
        Region, on_delete=models.PROTECT, related_name="empresas"
    )
    oferta_producto_servicio = models.TextField(
        "OFERTA, PRODUCTO O SERVICIO QUE OFRECE*"
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    activa = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tipo_documento", "numero_documento"],
                name="empresa_documento_unico",
            )
        ]
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.numero_documento} · {self.nombre}"


class Atencion(models.Model):
    fecha = models.DateField("FECHA*", default=timezone.localdate)
    hora = models.TimeField("HORA DE ATENCIÓN", default=hora_local_actual)
    tipo_atencion = models.CharField(
        "TIPO DE ATENCIÓN*", max_length=30, choices=TIPOS_ATENCION
    )
    responsable = models.ForeignKey(
        Responsable,
        verbose_name="RESPONSABLE CON QUIEN DESEA ENTREVISTARSE*",
        on_delete=models.PROTECT,
        related_name="atenciones",
    )
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, related_name="atenciones"
    )
    tema_consulta = models.TextField("REGISTRE EL TEMA DE CONSULTA", blank=True)
    detalle_consulta = models.TextField("DETALLAR CONSULTA", blank=True)
    origen = models.CharField(
        max_length=20,
        choices=[
            ("publico", "Formulario público"),
            ("asesor", "Registrado por asesor"),
            ("importado", "Importado"),
        ],
        default="publico",
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="atenciones_registradas",
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    anulada = models.BooleanField(default=False)

    class Meta:
        ordering = ["-fecha", "-creado"]

    def __str__(self):
        return f"Atención #{self.pk} · {self.empresa.nombre}"


class RegistroAuditoria(models.Model):
    ACCIONES = [
        ("crear", "Creación"),
        ("editar", "Edición"),
        ("eliminar", "Eliminación"),
        ("archivar", "Archivo"),
        ("depurar", "Depuración"),
    ]
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="acciones_auditadas",
    )
    accion = models.CharField(max_length=20, choices=ACCIONES)
    entidad = models.CharField(max_length=100)
    objeto_id = models.CharField(max_length=64, blank=True)
    descripcion = models.CharField(max_length=300, blank=True)
    antes = models.JSONField(default=dict, blank=True)
    despues = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_hora"]

    def __str__(self):
        return f"{self.fecha_hora:%d/%m/%Y %H:%M} · {self.accion} {self.entidad}"


class ArchivoAtenciones(models.Model):
    desde = models.DateField()
    hasta = models.DateField()
    generado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    generado = models.DateTimeField(auto_now_add=True)
    archivo = models.FileField(upload_to="archives/%Y/%m/")
    checksum_sha256 = models.CharField(max_length=64)
    total_atenciones = models.PositiveIntegerField(default=0)
    descargado_en = models.DateTimeField(null=True, blank=True)
    depurado = models.BooleanField(default=False)
    depurado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-generado"]

    def __str__(self):
        return f"Archivo {self.desde}–{self.hasta} ({self.total_atenciones})"


class AperturaFormularioPublico(models.Model):
    activado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="aperturas_formulario_activadas",
    )
    inicio = models.DateTimeField(default=timezone.now)
    fin_programado = models.DateTimeField()
    fin_real = models.DateTimeField(null=True, blank=True)
    desactivado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="aperturas_formulario_desactivadas",
    )

    class Meta:
        ordering = ["-inicio"]

    @property
    def activa(self):
        return self.fin_real is None and timezone.now() < self.fin_programado

    @classmethod
    def actual(cls):
        return (
            cls.objects.filter(fin_real__isnull=True, fin_programado__gt=timezone.now())
            .select_related("activado_por")
            .first()
        )


class RespaldoLimpieza(models.Model):
    bucket = models.CharField(max_length=120)
    ruta_storage = models.CharField(max_length=500, unique=True)
    nombre_archivo = models.CharField(max_length=255)
    desde = models.DateField()
    hasta = models.DateField()
    total_atenciones = models.PositiveIntegerField(default=0)
    tamano_bytes = models.PositiveBigIntegerField(default=0)
    checksum_sha256 = models.CharField(max_length=64)
    generado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="respaldos_limpieza",
    )
    generado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generado"]

    def __str__(self):
        return self.nombre_archivo
