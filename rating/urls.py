from django.urls import path
from . import views

app_name = "rating"
urlpatterns = [
    path("datos/", views.intercambiar_datos, name="intercambiar"),
    path("datos/limpiar/", views.limpiar_datos_exportados, name="limpiar_datos"),
    path("datos/respaldos/", views.respaldos_limpieza, name="respaldos"),
    path(
        "datos/respaldos/<int:pk>/descargar/",
        views.descargar_respaldo_limpieza,
        name="descargar_respaldo",
    ),
    path("importar/", views.importar, name="importar"),
    path("importar/confirmar/", views.confirmar, name="confirmar"),
    path("empresa/<int:empresa_id>/evaluar/", views.evaluar_empresa, name="evaluar"),
    path("atencion/<int:atencion_id>/evaluar/", views.evaluar_visita, name="evaluar_visita"),
    path("evaluacion/<int:evaluacion_id>/exportar/", views.exportar_evaluacion, name="exportar_evaluacion"),
]
