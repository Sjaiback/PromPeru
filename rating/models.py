from django.conf import settings
from django.db import models
from atencion.models import Empresa
from atencion.models import Atencion


class EmpresaRating(models.Model):
    empresa = models.OneToOneField(
        Empresa, on_delete=models.CASCADE, related_name="rating"
    )
    condicion_sunat = models.CharField(max_length=120, blank=True)
    linea = models.CharField(max_length=180, blank=True)
    producto = models.TextField(blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    clasificacion = models.CharField(max_length=80, blank=True)
    actualizado = models.DateTimeField(auto_now=True)

    def recalcular(self):
        total = sum((c.puntaje or 0) for c in self.criterios.all())
        self.total = total
        self.clasificacion = (
            "Alta prioridad"
            if total >= 75
            else "Prioridad media" if total >= 50 else "En desarrollo"
        )
        self.save(update_fields=["total", "clasificacion", "actualizado"])

    def __str__(self):
        return f"{self.empresa} · {self.total}"


class PerfilEvaluacionEmpresa(models.Model):
    """Información de evaluación que se reutiliza entre visitas de una empresa."""

    empresa = models.OneToOneField(
        Empresa, on_delete=models.CASCADE, related_name="perfil_evaluacion"
    )
    datos = models.JSONField(default=dict, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)


class EvaluacionVisita(models.Model):
    """Fotografía de la evaluación realizada para una atención concreta."""

    atencion = models.ForeignKey(
        Atencion, on_delete=models.CASCADE, related_name="evaluaciones"
    )
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, related_name="evaluaciones_visita"
    )
    evaluado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    respuestas = models.JSONField(default=dict, blank=True)
    puntajes_seccion = models.JSONField(default=dict, blank=True)
    puntaje_total = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado"]


class CategoriaRating(models.Model):
    nombre = models.CharField(max_length=180, unique=True)
    slug = models.SlugField(max_length=190, unique=True)
    orden = models.PositiveSmallIntegerField(default=0)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class CriterioRating(models.Model):
    categoria = models.ForeignKey(
        CategoriaRating, on_delete=models.PROTECT, related_name="criterios"
    )
    nombre = models.CharField(max_length=255)
    codigo = models.SlugField(max_length=255, unique=True)
    tipo_dato = models.CharField(
        max_length=20,
        choices=[
            ("texto", "Texto"),
            ("booleano", "Sí/No"),
            ("numero", "Número"),
            ("fecha", "Fecha"),
        ],
        default="texto",
    )
    puntaje_maximo = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)
    ayuda = models.TextField(blank=True)
    opciones = models.JSONField(default=list, blank=True)
    origen_excel = models.CharField(max_length=500, blank=True)
    es_puntaje = models.BooleanField(default=False)

    class Meta:
        ordering = ["categoria__orden", "orden", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["categoria", "nombre"], name="criterio_categoria_nombre_unico"
            )
        ]

    def __str__(self):
        return f"{self.categoria}: {self.nombre}"


class ValorCriterio(models.Model):
    rating = models.ForeignKey(
        EmpresaRating, on_delete=models.CASCADE, related_name="criterios"
    )
    criterio = models.ForeignKey(
        CriterioRating, on_delete=models.PROTECT, related_name="valores"
    )
    valor_texto = models.TextField(blank=True)
    valor_numero = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    valor_booleano = models.BooleanField(null=True, blank=True)
    puntaje = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["rating", "criterio"], name="valor_rating_criterio_unico"
            )
        ]


class MapeoColumna(models.Model):
    encabezado_origen = models.CharField(
        max_length=500,
        unique=True,
        help_text="Encabezado normalizado detectado en Excel",
    )
    campo_destino = models.CharField(
        max_length=300,
        help_text="empresa.nombre, empresa.region, rating.total o criterio:<codigo>",
    )
    activo = models.BooleanField(default=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.encabezado_origen} → {self.campo_destino}"


class ImportacionRating(models.Model):
    archivo_nombre = models.CharField(max_length=255)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    fecha = models.DateTimeField(auto_now_add=True)
    filas_detectadas = models.PositiveIntegerField(default=0)
    filas_importadas = models.PositiveIntegerField(default=0)
    filas_actualizadas = models.PositiveIntegerField(default=0)
    filas_ignoradas = models.PositiveIntegerField(default=0)
    filas_fallidas = models.PositiveIntegerField(default=0)
    detalle = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.archivo_nombre} · {self.fecha:%d/%m/%Y %H:%M}"
