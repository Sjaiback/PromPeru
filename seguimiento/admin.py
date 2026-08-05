from django.contrib import admin
from .models import AccionRealizada, EstadoAtencion, GestionAtencion, SeguimientoLog

admin.site.register([AccionRealizada, EstadoAtencion, GestionAtencion, SeguimientoLog])
