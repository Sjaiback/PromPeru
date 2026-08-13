from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Min, Q
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from seguimiento.models import EstadoAtencion, GestionAtencion
from .auditoria import registrar as auditar, serializar
from .forms import (
    AsesorEmailForm,
    AtencionEdicionForm,
    AtencionRegistroForm,
    EmpresaForm,
    UsuarioInternoForm,
    MiPerfilForm,
)
from .models import Atencion, Empresa, PerfilAsesor
from .middleware import es_cliente
from .permisos import puede_gestionar_usuarios


def error_403(request, exception=None):
    return render(request, "errors/403.html", status=403)


def error_404(request, exception=None):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)


def perfil_activo(user):
    if user.is_superuser:
        return getattr(user, "perfil_asesor", None)
    perfil = getattr(user, "perfil_asesor", None)
    return perfil if perfil and perfil.activo else None


def form_registro(request, publico=False, confirmacion_responsable=None):
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
            usar_actor_sesion=not publico,
        )
        if form.cleaned_data.get("actualizar_datos") and antes:
            auditar(
                request,
                "editar",
                atencion.empresa,
                antes=antes,
                descripcion="Actualización de datos durante el registro",
                usar_actor_sesion=not publico,
            )
        if publico:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": True, "responsable": atencion.responsable.nombre}
                )
            # Solo guardamos temporalmente el responsable para la confirmación;
            # no exponemos datos del cliente en la siguiente pantalla.
            request.session["responsable_ultima_atencion"] = atencion.responsable.nombre
            return redirect("atencion:publico")
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
        {
            "form": form,
            "publico": publico,
            "asesor": asesor,
            "confirmacion_responsable": confirmacion_responsable,
        },
    )


@login_required
def registro_publico(request):
    if not es_cliente(request.user):
        return redirect("atencion:inicio")
    confirmacion_responsable = None
    if request.method == "GET":
        confirmacion_responsable = request.session.pop(
            "responsable_ultima_atencion", None
        )
    return form_registro(
        request,
        publico=True,
        confirmacion_responsable=confirmacion_responsable,
    )


@login_required
def gracias(request):
    responsable = request.session.pop("responsable_ultima_atencion", None)
    return render(request, "atencion/gracias.html", {"responsable": responsable})


@login_required
def inicio(request):
    perfil = perfil_activo(request.user)
    if not request.user.is_superuser and not perfil:
        return render(request, "atencion/sin_acceso.html", status=403)
    qs = Atencion.objects.filter(anulada=False).select_related("empresa", "responsable")
    if perfil and perfil.rol == "asesor" and perfil.responsable:
        qs = qs.filter(responsable=perfil.responsable)
    resumen_entrada = None
    if (
        perfil
        and perfil.rol in {"asesor", "coordinador"}
        and request.session.pop("mostrar_resumen_entrada", False)
    ):
        pendientes = qs.filter(
            Q(gestion__isnull=True) | Q(gestion__estado__es_cerrado=False)
        ).distinct()
        # La ficha permanente se reutiliza en visitas futuras: solo alertamos
        # empresas que todavía no tienen ninguna evaluación guardada.
        sin_evaluacion = qs.filter(
            empresa__evaluaciones_visita__isnull=True
        ).distinct()
        empresas_prioritarias = list(
            sin_evaluacion.values("empresa_id")
            .annotate(primera_fecha=Min("fecha"))
            .order_by("primera_fecha")[:3]
        )
        evaluaciones = [
            sin_evaluacion.filter(empresa_id=item["empresa_id"])
            .order_by("fecha", "creado")
            .first()
            for item in empresas_prioritarias
        ]
        resumen_entrada = {
            "pendientes": pendientes.count(),
            "empresas_sin_evaluar": sin_evaluacion.values("empresa_id")
            .distinct()
            .count(),
            "evaluaciones": evaluaciones,
        }
    return render(
        request,
        "atencion/inicio.html",
        {
            "recientes": qs[:8],
            "total": qs.count(),
            "perfil": perfil,
            "resumen_entrada": resumen_entrada,
        },
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


@login_required
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
        not perfil
        or (
            perfil.rol not in ("coordinador", "bi", "admin")
            and not perfil.puede_archivar
        )
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


@login_required
def configuracion(request):
    """Internal settings overview; Django's technical admin remains off-menu."""
    if not request.user.is_staff and not puede_gestionar_usuarios(request.user):
        return render(request, "atencion/sin_acceso.html", status=403)
    from .models import Region, Responsable, Sector

    return render(
        request,
        "atencion/configuracion.html",
        {
            "perfil": perfil_activo(request.user),
            "total_responsables": Responsable.objects.filter(activo=True).count(),
            "total_regiones": Region.objects.filter(activo=True).count(),
            "total_sectores": Sector.objects.filter(activo=True).count(),
            "puede_gestionar_usuarios": puede_gestionar_usuarios(request.user),
        },
    )


@login_required
def asesores(request):
    if not puede_gestionar_usuarios(request.user):
        return render(request, "atencion/sin_acceso.html", status=403)
    perfiles = PerfilAsesor.objects.select_related("usuario", "responsable").order_by(
        "usuario__first_name", "usuario__last_name"
    )
    return render(request, "atencion/asesores.html", {"perfiles": perfiles})


@login_required
def asesor_crear(request):
    if not puede_gestionar_usuarios(request.user):
        return render(request, "atencion/sin_acceso.html", status=403)
    form = UsuarioInternoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user, perfil = form.save()
        auditar(
            request,
            "crear",
            user,
            descripcion=(
                f"Cuenta interna creada para {perfil.responsable.nombre} "
                f"con rol {perfil.get_rol_display()}"
            ),
        )
        messages.success(request, "Cuenta creada correctamente.")
        return redirect("atencion:asesores")
    return render(request, "atencion/asesor_crear.html", {"form": form})


@login_required
def asesor_editar(request, pk):
    if not puede_gestionar_usuarios(request.user):
        return render(request, "atencion/sin_acceso.html", status=403)
    perfil = get_object_or_404(
        PerfilAsesor.objects.select_related("usuario", "responsable"), pk=pk
    )
    antes = serializar(perfil.usuario)
    form = AsesorEmailForm(request.POST or None, instance=perfil.usuario)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        auditar(
            request,
            "editar",
            user,
            antes=antes,
            descripcion=f"Cuenta del asesor {perfil.responsable.nombre} actualizada",
        )
        messages.success(request, "Cuenta del asesor actualizada correctamente.")
        return redirect("atencion:asesores")
    return render(
        request,
        "atencion/asesor_form.html",
        {"form": form, "perfil": perfil},
    )


@login_required
def mi_perfil(request):
    if es_cliente(request.user):
        return render(request, "errors/403.html", status=403)

    datos_form = MiPerfilForm(
        request.POST or None if request.POST.get("accion") == "datos" else None,
        user=request.user,
    )
    password_form = PasswordChangeForm(
        request.user,
        request.POST or None if request.POST.get("accion") == "password" else None,
    )
    for field in password_form.fields.values():
        field.widget.attrs.setdefault("class", "form-control")

    if request.method == "POST" and request.POST.get("accion") == "datos" and datos_form.is_valid():
        antes = serializar(request.user)
        datos_form.save()
        auditar(request, "editar", request.user, antes=antes, descripcion="Datos personales actualizados por el usuario")
        messages.success(request, "Tus datos personales fueron actualizados.")
        return redirect("atencion:mi_perfil")

    if request.method == "POST" and request.POST.get("accion") == "password" and password_form.is_valid():
        password_form.save()
        update_session_auth_hash(request, request.user)
        auditar(request, "editar", request.user, descripcion="Contraseña actualizada por el propio usuario")
        messages.success(request, "Tu contraseña fue actualizada correctamente.")
        return redirect("atencion:mi_perfil")

    return render(request, "atencion/mi_perfil.html", {"datos_form": datos_form, "password_form": password_form})
