from django.urls import path
from . import views

app_name = "atencion"
urlpatterns = [
    path("", views.registro_publico, name="publico"),
    path("gracias/", views.gracias, name="gracias"),
    path("panel/", views.inicio, name="inicio"),
    path("panel/atenciones/nueva/", views.registrar, name="registrar"),
    path("panel/atenciones/<int:pk>/", views.detalle, name="detalle"),
    path(
        "panel/atenciones/<int:pk>/editar/",
        views.atencion_editar,
        name="atencion_editar",
    ),
    path(
        "panel/atenciones/<int:pk>/anular/",
        views.atencion_anular,
        name="atencion_anular",
    ),
    path("panel/empresas/", views.empresas, name="empresas"),
    path(
        "panel/empresas/<int:pk>/editar/", views.empresa_editar, name="empresa_editar"
    ),
    path(
        "panel/empresas/<int:pk>/desactivar/",
        views.empresa_desactivar,
        name="empresa_desactivar",
    ),
    path("panel/auditoria/", views.auditoria, name="auditoria"),
    path("panel/configuracion/", views.configuracion, name="configuracion"),
    path("panel/mi-perfil/", views.mi_perfil, name="mi_perfil"),
    path("panel/configuracion/asesores/", views.asesores, name="asesores"),
    path(
        "panel/configuracion/asesores/nuevo/",
        views.asesor_crear,
        name="asesor_crear",
    ),
    path(
        "panel/configuracion/asesores/<int:pk>/",
        views.asesor_editar,
        name="asesor_editar",
    ),
    path("api/empresa/", views.buscar_documento, name="buscar_documento"),
]
