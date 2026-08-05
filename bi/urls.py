from django.urls import path
from . import views

app_name = "bi"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("exportar/excel/", views.exportar_excel, name="excel"),
    path("exportar/pdf/", views.exportar_pdf, name="pdf"),
    path("archivos/", views.archivos, name="archivos"),
    path(
        "archivos/<int:pk>/descargar/",
        views.descargar_archivo,
        name="descargar_archivo",
    ),
    path("archivos/<int:pk>/depurar/", views.depurar_archivo, name="depurar_archivo"),
]
