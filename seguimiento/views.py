from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Case, IntegerField, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from atencion.models import Atencion
from .forms import GestionForm
from .models import EstadoAtencion, GestionAtencion


def es_asesor(user):
    perfil = getattr(user, "perfil_asesor", None)
    return user.is_superuser or bool(perfil and perfil.activo)


@login_required
@user_passes_test(es_asesor)
def bandeja(request):
    qs = GestionAtencion.objects.select_related(
        "atencion__empresa", "atencion__responsable", "estado"
    )
    perfil = getattr(request.user, "perfil_asesor", None)
    if (
        not request.user.is_superuser
        and perfil
        and perfil.rol == "asesor"
        and perfil.responsable_id
    ):
        qs = qs.filter(atencion__responsable=perfil.responsable)
    resumen = {
        "total": qs.count(),
        "pendientes": qs.filter(estado_seguimiento="en_proceso").count(),
        "cerradas": qs.filter(estado_seguimiento="finalizado").count(),
    }
    estado = request.GET.get("estado")
    if estado in {"en_proceso", "finalizado"}:
        qs = qs.filter(estado_seguimiento=estado)
    qs = qs.annotate(
        grupo_orden=Case(
            When(estado_seguimiento="finalizado", then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by("grupo_orden", "atencion__fecha", "atencion__hora", "atencion__creado")
    return render(
        request,
        "seguimiento/bandeja.html",
        {
            "gestiones": qs,
            "estados": GestionAtencion.ESTADOS_SEGUIMIENTO,
            "estado_actual": estado,
            "resumen": resumen,
        },
    )


@login_required
@user_passes_test(es_asesor)
def gestionar(request, pk):
    atencion = get_object_or_404(Atencion, pk=pk)
    inicial = EstadoAtencion.objects.filter(activo=True).first()
    gestion, _ = GestionAtencion.objects.get_or_create(
        atencion=atencion, defaults={"estado": inicial, "actualizado_por": request.user}
    )
    form = GestionForm(request.POST or None, instance=gestion, prefix="gestion")
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.actualizado_por = request.user
        atencion.detalle_consulta = form.cleaned_data.get("detalle_consulta", "")
        atencion.save(update_fields=["detalle_consulta", "actualizado"])
        obj.save()
        messages.success(request, "Seguimiento actualizado.")
        return redirect("seguimiento:bandeja")
    return render(
        request,
        "seguimiento/gestionar.html",
        {"atencion": atencion, "gestion": gestion, "form": form},
    )
