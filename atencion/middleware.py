from django.conf import settings
from django.shortcuts import redirect, render


CLIENT_ALLOWED_VIEWS = {
    "atencion:publico",
    "atencion:gracias",
    "atencion:buscar_documento",
    "logout",
}


def es_cliente(user):
    """A client is an authenticated account without an advisor profile."""
    return bool(
        user.is_authenticated
        and not user.is_superuser
        and not getattr(user, "perfil_asesor", None)
    )


class ClientAccessMiddleware:
    """Keep the shared client account strictly inside the customer form."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.es_cliente = es_cliente(getattr(request, "user", None))
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not getattr(request, "es_cliente", False):
            return None
        view_name = request.resolver_match.view_name if request.resolver_match else ""
        if view_name in CLIENT_ALLOWED_VIEWS:
            return None
        return render(request, "errors/403.html", status=403)


class SystemAdminOnlyMiddleware:
    """Reserve Django's technical admin for the designated system account."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.path.startswith("/admin/"):
            return None

        user = request.user
        if not user.is_authenticated:
            return render(request, "errors/403.html", status=403)

        is_system_admin = (
            user.username == settings.SYSTEM_ADMIN_USERNAME
            and user.is_staff
            and user.is_superuser
        )
        if is_system_admin:
            return None

        return render(request, "errors/403.html", status=403)
