from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from atencion.models import Atencion
from .forms import GestionForm, SeguimientoForm
from .models import EstadoAtencion, GestionAtencion, SeguimientoLog


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
        "pendientes": qs.filter(estado__es_cerrado=False).count(),
        "cerradas": qs.filter(estado__es_cerrado=True).count(),
    }
    estado = request.GET.get("estado")
    if estado:
        qs = qs.filter(estado_id=estado)
    qs = qs.order_by("-atencion__fecha", "-atencion__creado")
    return render(
        request,
        "seguimiento/bandeja.html",
        {
            "gestiones": qs,
            "estados": EstadoAtencion.objects.filter(activo=True),
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
    log_form = SeguimientoForm(request.POST or None, prefix="log")
    if request.method == "POST" and form.is_valid() and log_form.is_valid():
        obj = form.save(commit=False)
        obj.actualizado_por = request.user
        obj.save()
        detalle = log_form.cleaned_data.get("detalle", "").strip()
        if detalle:
            SeguimientoLog.objects.create(
                gestion=obj, detalle=detalle, autor=request.user
            )
        messages.success(request, "Seguimiento actualizado.")
        return redirect("seguimiento:gestionar", pk=pk)
    return render(
        request,
        "seguimiento/gestionar.html",
        {"atencion": atencion, "gestion": gestion, "form": form, "log_form": log_form},
    )
