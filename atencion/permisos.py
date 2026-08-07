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
