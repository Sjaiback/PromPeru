from django.urls import path
from . import views

app_name = "rating"
urlpatterns = [
    path("importar/", views.importar, name="importar"),
    path("importar/confirmar/", views.confirmar, name="confirmar"),
    path("empresa/<int:empresa_id>/evaluar/", views.evaluar_empresa, name="evaluar"),
]
