from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "PROMPERÚ · Administración"
admin.site.site_title = "PROMPERÚ Centro Este"
admin.site.index_title = "Catálogos y configuración"


class PromPeruLoginView(LoginView):
    template_name = "registration/login.html"

    def get_success_url(self):
        from atencion.middleware import es_cliente

        return (
            self.get_redirect_url()
            or ("/" if es_cliente(self.request.user) else "/panel/")
        )

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "cuentas/ingresar/",
        PromPeruLoginView.as_view(),
        name="login",
    ),
    path("cuentas/salir/", LogoutView.as_view(), name="logout"),
    path("", include("atencion.urls")),
    path("seguimiento/", include("seguimiento.urls")),
    path("rating/", include("rating.urls")),
    path("bi/", include("bi.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = "atencion.views.error_403"
handler404 = "atencion.views.error_404"
handler500 = "atencion.views.error_500"
