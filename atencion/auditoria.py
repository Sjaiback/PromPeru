from datetime import date, datetime
from decimal import Decimal
from django.forms.models import model_to_dict
from .models import RegistroAuditoria


def serializar(obj):
    if obj is None:
        return {}
    data = model_to_dict(obj)
    for key, value in list(data.items()):
        if isinstance(value, (date, datetime, Decimal)):
            data[key] = str(value)
        elif hasattr(value, "pk"):
            data[key] = value.pk
        elif not isinstance(value, (str, int, float, bool, type(None), dict, list)):
            data[key] = str(value)
    return data


def registrar(
    request, accion, obj=None, entidad=None, antes=None, despues=None, descripcion=""
):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
    ip = forwarded or request.META.get("REMOTE_ADDR")
    return RegistroAuditoria.objects.create(
        actor=(
            request.user
            if getattr(request, "user", None) and request.user.is_authenticated
            else None
        ),
        accion=accion,
        entidad=entidad or obj.__class__.__name__,
        objeto_id=str(getattr(obj, "pk", "") or ""),
        descripcion=descripcion,
        antes=antes or {},
        despues=despues if despues is not None else serializar(obj),
        ip=ip,
    )
