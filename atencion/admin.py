from django.contrib import admin
from .models import (
    ArchivoAtenciones,
    Atencion,
    Empresa,
    PerfilAsesor,
    Region,
    RegistroAuditoria,
    Responsable,
    Sector,
)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = (
        "numero_documento",
        "nombre",
        "tipo_usuario",
        "sector",
        "region",
        "actualizado",
    )
    search_fields = ("numero_documento", "nombre", "nombres_apellidos", "email")
    list_filter = ("tipo_documento", "tipo_usuario", "sector", "region")


@admin.register(Atencion)
class AtencionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "fecha",
        "empresa",
        "tipo_atencion",
        "responsable",
        "registrado_por",
    )
    list_filter = ("fecha", "tipo_atencion", "responsable")
    search_fields = ("empresa__nombre", "empresa__numero_documento", "tema_consulta")


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("fecha_hora", "actor", "accion", "entidad", "objeto_id", "ip")
    list_filter = ("accion", "entidad", "fecha_hora")
    search_fields = ("actor__username", "descripcion", "objeto_id")
    readonly_fields = (
        "actor",
        "accion",
        "entidad",
        "objeto_id",
        "descripcion",
        "antes",
        "despues",
        "ip",
        "fecha_hora",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


for model in (Region, Sector, Responsable, PerfilAsesor, ArchivoAtenciones):
    admin.site.register(model)
