from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from seguimiento.models import EstadoAtencion, GestionAtencion
from .auditoria import registrar as auditar, serializar
from .forms import AtencionEdicionForm, AtencionRegistroForm, EmpresaForm
from .models import Atencion, Empresa, PerfilAsesor


def perfil_activo(user):
    if user.is_superuser:
        return getattr(user, "perfil_asesor", None)
    perfil = getattr(user, "perfil_asesor", None)
    return perfil if perfil and perfil.activo else None


def form_registro(request, publico=False):
    asesor = None if publico else perfil_activo(request.user)
    form = AtencionRegistroForm(request.POST or None, asesor=asesor)
    if request.method == "POST" and form.is_valid():
        antes = serializar(form.empresa_existente)
        atencion = form.save(None if publico else request.user)
        estado = EstadoAtencion.objects.filter(activo=True).order_by("orden").first()
        if estado:
            GestionAtencion.objects.get_or_create(
                atencion=atencion,
                defaults={
                    "estado": estado,
                    "actualizado_por": None if publico else request.user,
                },
            )
        auditar(
            request,
            "crear",
            atencion,
            descripcion=(
                "Atención registrada desde formulario público"
                if publico
                else "Atención registrada por asesor"
            ),
        )
        if form.cleaned_data.get("actualizar_datos") and antes:
            auditar(
                request,
                "editar",
                atencion.empresa,
                antes=antes,
                descripcion="Actualización de datos durante el registro",
            )
        if publico:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": True})
            return redirect("atencion:gracias")
        messages.success(request, f"Atención #{atencion.pk} registrada correctamente.")
        return redirect("atencion:detalle", pk=atencion.pk)
    if (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        and request.method == "POST"
    ):
        return JsonResponse(
            {"success": False, "errors": form.errors.get_json_data()}, status=400
        )
    return render(
        request,
        "atencion/registro.html",
        {"form": form, "publico": publico, "asesor": asesor},
    )


def registro_publico(request):
    return form_registro(request, publico=True)


def gracias(request):
    return render(request, "atencion/gracias.html")


@login_required
def inicio(request):
    perfil = perfil_activo(request.user)
    if not request.user.is_superuser and not perfil:
        return render(request, "atencion/sin_acceso.html", status=403)
    qs = Atencion.objects.filter(anulada=False).select_related("empresa", "responsable")
    if perfil and perfil.rol == "asesor" and perfil.responsable:
        qs = qs.filter(responsable=perfil.responsable)
    return render(
        request,
        "atencion/inicio.html",
        {"recientes": qs[:8], "total": qs.count(), "perfil": perfil},
    )


@login_required
def registrar(request):
    if not request.user.is_superuser and not perfil_activo(request.user):
        return render(request, "atencion/sin_acceso.html", status=403)
    return form_registro(request)


@login_required
def detalle(request, pk):
    obj = get_object_or_404(
        Atencion.objects.select_related("empresa", "responsable"), pk=pk
    )
    return render(request, "atencion/detalle.html", {"atencion": obj})


@require_GET
def buscar_documento(request):
    empresa = Empresa.objects.filter(
        tipo_documento=request.GET.get("tipo"),
        numero_documento=request.GET.get("numero", "").strip(),
        activa=True,
    ).first()
    if not empresa:
        return JsonResponse({"encontrado": False})
    data = {"encontrado": True, "resumen": empresa.nombre}
    if request.GET.get("actualizar") == "1":
        data.update(
            {
                "nombre": empresa.nombre,
                "tipo_personeria": empresa.tipo_personeria,
                "nombres_apellidos": empresa.nombres_apellidos,
                "cargo": empresa.cargo,
                "tipo_usuario": empresa.tipo_usuario,
                "telefono": empresa.telefono,
                "email": empresa.email,
                "sector": empresa.sector_id,
                "region": empresa.region_id,
                "oferta_producto_servicio": empresa.oferta_producto_servicio,
            }
        )
    return JsonResponse(data)


@login_required
def empresas(request):
    if not request.user.is_superuser and not perfil_activo(request.user):
        return render(request, "atencion/sin_acceso.html", status=403)
    qs = Empresa.objects.select_related("sector", "region").order_by("nombre")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(nombre__icontains=q)
            | Q(numero_documento__icontains=q)
            | Q(nombres_apellidos__icontains=q)
        )
    return render(
        request,
        "atencion/empresas.html",
        {"page": Paginator(qs, 25).get_page(request.GET.get("page")), "q": q},
    )


@login_required
def empresa_editar(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    antes = serializar(empresa)
    form = EmpresaForm(request.POST or None, instance=empresa)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        auditar(
            request,
            "editar",
            obj,
            antes=antes,
            descripcion="Datos de empresa editados por asesor",
        )
        messages.success(
            request, "Datos actualizados y cambio registrado en auditoría."
        )
        return redirect("atencion:empresas")
    return render(
        request, "atencion/empresa_form.html", {"form": form, "empresa": empresa}
    )


@login_required
@require_POST
def empresa_desactivar(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    antes = serializar(empresa)
    empresa.activa = False
    empresa.save(update_fields=["activa", "actualizado"])
    auditar(
        request,
        "eliminar",
        empresa,
        antes=antes,
        descripcion="Empresa desactivada; registro histórico conservado",
    )
    messages.success(request, "Empresa desactivada. Su historial permanece conservado.")
    return redirect("atencion:empresas")


@login_required
def atencion_editar(request, pk):
    obj = get_object_or_404(Atencion, pk=pk)
    perfil = perfil_activo(request.user)
    antes = serializar(obj)
    form = AtencionEdicionForm(request.POST or None, instance=obj, asesor=perfil)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        auditar(
            request,
            "editar",
            obj,
            antes=antes,
            descripcion="Atención editada por asesor",
        )
        messages.success(request, "Atención actualizada y auditada.")
        return redirect("atencion:detalle", pk=obj.pk)
    return render(
        request, "atencion/atencion_form.html", {"form": form, "atencion": obj}
    )


@login_required
@require_POST
def atencion_anular(request, pk):
    obj = get_object_or_404(Atencion, pk=pk)
    antes = serializar(obj)
    obj.anulada = True
    obj.save(update_fields=["anulada", "actualizado"])
    auditar(
        request, "eliminar", obj, antes=antes, descripcion="Atención anulada por asesor"
    )
    messages.success(request, "Atención anulada; el registro permanece en auditoría.")
    return redirect("atencion:inicio")


@login_required
def auditoria(request):
    perfil = perfil_activo(request.user)
    if not request.user.is_superuser and (
        not perfil or perfil.rol not in ("bi", "admin")
    ):
        return render(request, "atencion/sin_acceso.html", status=403)
    from .models import RegistroAuditoria

    return render(
        request,
        "atencion/auditoria.html",
        {
            "page": Paginator(
                RegistroAuditoria.objects.select_related("actor"), 40
            ).get_page(request.GET.get("page"))
        },
    )
