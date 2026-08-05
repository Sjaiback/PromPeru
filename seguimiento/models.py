from django.conf import settings
from django.db import models
from django.utils import timezone
from atencion.models import Atencion, CatalogoBase


class EstadoAtencion(CatalogoBase):
    color = models.CharField(max_length=7, default="#64748b")
    es_cerrado = models.BooleanField(default=False)

    class Meta(CatalogoBase.Meta):
        verbose_name = "Estado de atención"
        verbose_name_plural = "Estados de atención"


class AccionRealizada(CatalogoBase):
    class Meta(CatalogoBase.Meta):
        verbose_name = "Acción frecuente"
        verbose_name_plural = "Acciones frecuentes"


class GestionAtencion(models.Model):
    atencion = models.OneToOneField(
        Atencion, on_delete=models.CASCADE, related_name="gestion"
    )
    accion = models.ForeignKey(
        AccionRealizada, null=True, blank=True, on_delete=models.SET_NULL
    )
    accion_otro = models.CharField(max_length=250, blank=True)
    estado = models.ForeignKey(
        EstadoAtencion, on_delete=models.PROTECT, related_name="gestiones"
    )
    observaciones = models.TextField(blank=True)
    iniciada = models.DateTimeField(default=timezone.now)
    resuelta = models.DateTimeField(null=True, blank=True)
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )

    def save(self, *args, **kwargs):
        if self.estado_id and self.estado.es_cerrado and not self.resuelta:
            self.resuelta = timezone.now()
        elif self.estado_id and not self.estado.es_cerrado:
            self.resuelta = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Gestión {self.atencion_id} · {self.estado}"


class SeguimientoLog(models.Model):
    gestion = models.ForeignKey(
        GestionAtencion, on_delete=models.CASCADE, related_name="seguimientos"
    )
    detalle = models.TextField("SEGUIMIENTO")
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_hora"]

    def __str__(self):
        return f"Seguimiento {self.gestion_id} · {self.fecha_hora:%d/%m/%Y}"
