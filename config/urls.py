from django.contrib import admin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.urls import include, path, reverse_lazy
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "PROMPERÚ · Administración"
admin.site.site_title = "PROMPERÚ Centro Este"
admin.site.index_title = "Catálogos y configuración"


class PromPeruLoginView(LoginView):
    template_name = "registration/login.html"

    def form_valid(self, form):
        """Remember an internal login so the panel can show its work summary once."""
        user = form.get_user()
        perfil = getattr(user, "perfil_asesor", None)
        if perfil and perfil.activo and perfil.rol in {"asesor", "coordinador"}:
            self.request.session["mostrar_resumen_entrada"] = True
        return super().form_valid(form)

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
    path(
        "cuentas/recuperar/",
        PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.txt",
            html_email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
            success_url=reverse_lazy("password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "cuentas/recuperar/enviado/",
        PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "cuentas/restablecer/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url=reverse_lazy("password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "cuentas/restablecer/completo/",
        PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
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
