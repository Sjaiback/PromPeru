from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "PROMPERÚ · Administración"
admin.site.site_title = "PROMPERÚ Centro Este"
admin.site.index_title = "Catálogos y configuración"

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "cuentas/ingresar/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("cuentas/salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("atencion.urls")),
    path("seguimiento/", include("seguimiento.urls")),
    path("rating/", include("rating.urls")),
    path("bi/", include("bi.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
