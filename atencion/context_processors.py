from .permisos import (
    es_cuenta_sistemas,
    puede_controlar_formulario_publico,
    puede_gestionar_usuarios,
)


def permisos(request):
    return {
        "puede_gestionar_usuarios": puede_gestionar_usuarios(request.user),
        "es_cuenta_sistemas": es_cuenta_sistemas(request.user),
        "puede_controlar_formulario_publico": puede_controlar_formulario_publico(
            request.user
        ),
    }
