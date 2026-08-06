RESPONSABLE_GESTOR_USUARIOS = "Coordinador - Aldo Palomino"


def puede_gestionar_usuarios(user):
    """Only the systems administrator and Aldo may provision internal accounts."""
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    perfil = getattr(user, "perfil_asesor", None)
    return bool(
        perfil
        and perfil.activo
        and perfil.responsable
        and perfil.responsable.nombre == RESPONSABLE_GESTOR_USUARIOS
    )
