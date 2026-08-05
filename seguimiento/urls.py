from django.urls import path
from . import views

app_name = "seguimiento"
urlpatterns = [
    path("", views.bandeja, name="bandeja"),
    path("<int:pk>/", views.gestionar, name="gestionar"),
]
