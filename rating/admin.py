from django.contrib import admin
from .models import (
    CategoriaRating,
    CriterioRating,
    EmpresaRating,
    ImportacionRating,
    MapeoColumna,
    ValorCriterio,
)

admin.site.register(
    [
        CategoriaRating,
        CriterioRating,
        EmpresaRating,
        ImportacionRating,
        MapeoColumna,
        ValorCriterio,
    ]
)
