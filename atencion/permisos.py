def puede_gestionar_usuarios(user):
    """Allow systems and active coordinators to manage internal accounts."""
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    perfil = getattr(user, "perfil_asesor", None)
    return bool(
        perfil
        and perfil.activo
        and perfil.rol == "coordinador"
    )


def es_cuenta_sistemas(user):
    if not getattr(user, "is_authenticated", False):
        return False
    from django.conf import settings

    return bool(
        user.username == settings.SYSTEM_ADMIN_USERNAME
        and user.is_staff
        and user.is_superuser
    )


def puede_controlar_formulario_publico(user):
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    perfil = getattr(user, "perfil_asesor", None)
    return bool(
        perfil
        and perfil.activo
        and perfil.rol in {"asesor", "coordinador"}
    )
