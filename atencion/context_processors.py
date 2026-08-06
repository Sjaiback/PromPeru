from .permisos import puede_gestionar_usuarios


def permisos(request):
    return {"puede_gestionar_usuarios": puede_gestionar_usuarios(request.user)}
