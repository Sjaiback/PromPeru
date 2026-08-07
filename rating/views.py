import io, re, unicodedata
from decimal import Decimal, InvalidOperation
from openpyxl import load_workbook
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
import re
from django.utils.text import slugify
from atencion.models import Atencion, Empresa, Region, Sector
from openpyxl import Workbook
from .forms import ImportarExcelForm
from .forms import EvaluacionDinamicaForm
from .models import (
    CategoriaRating,
    CriterioRating,
    EmpresaRating,
    ImportacionRating,
    MapeoColumna,
    ValorCriterio,
    EvaluacionVisita,
    PerfilEvaluacionEmpresa,
)
from atencion.auditoria import registrar as auditar
from .ficha import SECCIONES, preparar_ficha, puntuar


def norm(value):
    value = (
        unicodedata.normalize("NFKD", str(value or ""))
        .encode("ascii", "ignore")
        .decode()
        .lower()
    )
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


ALIASES = {
    "ruc": "empresa.numero_documento",
    "razon social": "empresa.nombre",
    "razon_social": "empresa.nombre",
    "sector": "empresa.sector",
    "ubicacion": "empresa.region",
    "region": "empresa.region",
    "condicion sunat": "rating.condicion_sunat",
    "linea": "rating.linea",
    "producto": "rating.producto",
    "total": "rating.total",
    "rating": "rating.total",
}


def leer_excel(data, fila_inicio, cantidad):
    wb = load_workbook(io.BytesIO(data), data_only=True, read_only=False)
    ws = wb.active
    # Propaga valores de celdas combinadas para reconstruir encabezados multinivel.
    merged = {}
    for rng in ws.merged_cells.ranges:
        top = ws.cell(rng.min_row, rng.min_col).value
        for row in range(rng.min_row, rng.max_row + 1):
            for col in range(rng.min_col, rng.max_col + 1):
                merged[(row, col)] = top
    headers = []
    for col in range(1, ws.max_column + 1):
        parts = []
        for row in range(fila_inicio, fila_inicio + cantidad):
            value = merged.get((row, col), ws.cell(row, col).value)
            if value and str(value).strip() not in parts:
                parts.append(str(value).strip())
        headers.append(" / ".join(parts) or f"Columna {col}")
    rows = []
    for values in ws.iter_rows(min_row=fila_inicio + cantidad, values_only=True):
        if any(v not in (None, "") for v in values):
            rows.append(["" if v is None else str(v) for v in values])
    return headers, rows


def sugerir(header):
    n = norm(header)
    saved = MapeoColumna.objects.filter(encabezado_origen=n, activo=True).first()
    if saved:
        return saved.campo_destino
    for alias, target in sorted(ALIASES.items(), key=lambda x: -len(x[0])):
        if norm(alias) in n:
            return target
    return ""


@staff_member_required
def importar(request):
    form = ImportarExcelForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        upload = form.cleaned_data["archivo"]
        if not upload.name.lower().endswith(".xlsx"):
            form.add_error("archivo", "Solo se admiten archivos .xlsx.")
        else:
            headers, rows = leer_excel(
                upload.read(),
                form.cleaned_data["fila_inicio_encabezado"],
                form.cleaned_data["filas_encabezado"],
            )
            request.session["rating_preview"] = {
                "archivo": upload.name,
                "headers": headers,
                "rows": rows[:1000],
            }
            columnas = [
                {"indice": i, "encabezado": h, "sugerencia": sugerir(h)}
                for i, h in enumerate(headers)
            ]
            return render(
                request,
                "rating/preview.html",
                {
                    "headers": headers,
                    "columnas": columnas,
                    "rows": rows[:10],
                    "total": len(rows),
                },
            )
    return render(
        request,
        "rating/importar.html",
        {"form": form, "logs": ImportacionRating.objects.all()[:10]},
    )


@staff_member_required
@transaction.atomic
def confirmar(request):
    if request.method != "POST" or "rating_preview" not in request.session:
        return redirect("rating:importar")
    data = request.session["rating_preview"]
    headers = data["headers"]
    rows = data["rows"]
    mappings = [request.POST.get(f"map_{i}", "").strip() for i in range(len(headers))]
    duplicate_mode = request.POST.get("duplicados", "actualizar")
    log = ImportacionRating.objects.create(
        archivo_nombre=data["archivo"], usuario=request.user, filas_detectadas=len(rows)
    )
    errors = []
    for idx, row in enumerate(rows, start=1):
        record = {m: row[i] for i, m in enumerate(mappings) if m and i < len(row)}
        doc = re.sub(r"\.0$", "", record.get("empresa.numero_documento", "")).strip()
        if not doc:
            errors.append({"fila": idx, "error": "RUC/documento no identificado"})
            continue
        existing = Empresa.objects.filter(numero_documento=doc).first()
        if existing and duplicate_mode == "ignorar":
            log.filas_ignoradas += 1
            continue
        sector_name = record.get("empresa.sector", "Sin clasificar") or "Sin clasificar"
        region_name = record.get("empresa.region", "Lima") or "Lima"
        sector, _ = Sector.objects.get_or_create(nombre=sector_name)
        region, _ = Region.objects.get_or_create(nombre=region_name)
        defaults = {
            "nombre": record.get(
                "empresa.nombre", existing.nombre if existing else f"Empresa {doc}"
            ),
            "sector": sector,
            "region": region,
            "tipo_usuario": "Exportador",
            "telefono": existing.telefono if existing else "000000000",
            "email": existing.email if existing else "pendiente@example.local",
            "oferta_producto_servicio": record.get("rating.producto", "Por completar"),
        }
        empresa, created = Empresa.objects.update_or_create(
            numero_documento=doc,
            defaults={"tipo_documento": "RUC" if len(doc) == 11 else "DNI", **defaults},
        )
        rating, _ = EmpresaRating.objects.get_or_create(empresa=empresa)
        for field in ("condicion_sunat", "linea", "producto"):
            if f"rating.{field}" in record:
                setattr(rating, field, record[f"rating.{field}"])
        try:
            rating.total = Decimal(
                str(record.get("rating.total", rating.total)).replace(",", ".")
            )
        except InvalidOperation:
            pass
        rating.save()
        for destination, value in record.items():
            if not destination.startswith("criterio:"):
                continue
            code = destination.split(":", 1)[1]
            criterio = CriterioRating.objects.filter(codigo=code).first()
            if criterio:
                ValorCriterio.objects.update_or_create(
                    rating=rating,
                    criterio=criterio,
                    defaults={"valor_texto": str(value)},
                )
        for header, destination in zip(headers, mappings):
            if destination:
                MapeoColumna.objects.update_or_create(
                    encabezado_origen=norm(header),
                    defaults={"campo_destino": destination},
                )
        if created:
            log.filas_importadas += 1
        else:
            log.filas_actualizadas += 1
    log.filas_fallidas = len(errors)
    log.detalle = {"errores": errors}
    log.save()
    del request.session["rating_preview"]
    messages.success(
        request,
        f"Importación terminada: {log.filas_importadas} nuevas, {log.filas_actualizadas} actualizadas, {log.filas_fallidas} fallidas.",
    )
    return redirect("rating:importar")


def _valor_inicial(valor):
    if valor.criterio.tipo_dato == "booleano":
        return (
            "si"
            if valor.valor_booleano
            else "no" if valor.valor_booleano is False else ""
        )
    if valor.criterio.tipo_dato == "numero":
        return valor.valor_numero
    return valor.valor_texto


@login_required
def evaluar_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    atencion = empresa.atenciones.filter(anulada=False).order_by("-fecha", "-creado").first()
    if not atencion:
        messages.error(request, "La empresa aún no tiene una atención asociada.")
        return redirect("atencion:empresas")
    return redirect("rating:evaluar_visita", atencion_id=atencion.pk)


def _datos_iniciales(empresa):
    return {"contactos": [{"nombres": empresa.nombres_apellidos, "apellidos": "", "cargo": empresa.cargo, "telefono": empresa.telefono, "correo1": empresa.email, "correo2": ""}]}


def _leer_respuestas(post):
    respuestas = {}
    for seccion in SECCIONES:
        for question in seccion["questions"]:
            code = question["code"]
            if question["type"] == "repeat":
                columns = {sub["code"]: post.getlist(f"{code}__{sub['code']}[]") for sub in question["subfields"]}
                total = max([len(values) for values in columns.values()] or [0])
                respuestas[code] = [
                    {key: (values[index].strip() if index < len(values) else "") for key, values in columns.items()}
                    for index in range(total)
                    if any(index < len(values) and values[index].strip() for values in columns.values())
                ]
            elif question["type"] == "number_blank" and post.get(f"{code}__blank"):
                respuestas[code] = ""
            else:
                respuestas[code] = post.get(code, "").strip()
    for seccion in SECCIONES:
        for question in seccion["questions"]:
            if question.get("show_if"):
                parent, expected = question["show_if"].split(":", 1)
                if respuestas.get(parent) != expected:
                    respuestas[question["code"]] = [] if question["type"] == "repeat" else ""
    return respuestas


@login_required
def evaluar_visita(request, atencion_id):
    atencion = get_object_or_404(Atencion.objects.select_related("empresa", "responsable"), pk=atencion_id)
    empresa = atencion.empresa
    perfil, _ = PerfilEvaluacionEmpresa.objects.get_or_create(empresa=empresa, defaults={"datos": _datos_iniciales(empresa)})
    evaluacion = EvaluacionVisita.objects.filter(atencion=atencion).first()
    if not evaluacion:
        evaluacion = EvaluacionVisita(atencion=atencion, empresa=empresa, evaluado_por=request.user)
    valores = {**perfil.datos, **evaluacion.respuestas}
    redes = valores.get("redes_detalle", [])
    plataformas = {row.get("red") for row in redes if isinstance(row, dict)}
    if valores.get("web_url") and not valores.get("web"):
        valores["web"] = "si"
    for plataforma in ("facebook", "instagram", "linkedin"):
        if plataforma in plataformas and not valores.get(plataforma):
            valores[plataforma] = "si"
    if request.method == "POST":
        respuestas = _leer_respuestas(request.POST)
        puntos, total = puntuar(respuestas)
        evaluacion.empresa = empresa
        evaluacion.evaluado_por = request.user
        evaluacion.respuestas = respuestas
        evaluacion.puntajes_seccion = {key: str(value) for key, value in puntos.items()}
        evaluacion.puntaje_total = total
        evaluacion.save()
        perfil.datos = respuestas
        perfil.save(update_fields=["datos", "actualizado"])
        auditar(request, "editar", evaluacion, descripcion=f"Ficha de evaluación de atención #{atencion.pk} actualizada")
        messages.success(request, "Evaluación guardada y datos permanentes actualizados.")
        return redirect("rating:evaluar_visita", atencion_id=atencion.pk)
    secciones = preparar_ficha(valores)
    for seccion in secciones:
        seccion["score"] = (evaluacion.puntajes_seccion or {}).get(seccion["code"], "0")
    return render(request, "rating/ficha.html", {"empresa": empresa, "atencion": atencion, "evaluacion": evaluacion, "secciones": secciones})


@login_required
def exportar_evaluacion(request, atencion_id):
    evaluacion = get_object_or_404(EvaluacionVisita.objects.select_related("empresa", "atencion", "evaluado_por"), atencion_id=atencion_id)
    wb = Workbook()
    ws = wb.active
    ws.title = "Evaluación"
    ws.append(["PROMPERÚ – Ficha de evaluación por visita"])
    ws.append(["Empresa / persona", evaluacion.empresa.nombre])
    ws.append(["Documento", evaluacion.empresa.numero_documento])
    ws.append(["Atención", evaluacion.atencion_id])
    ws.append(["Fecha", evaluacion.atencion.fecha])
    ws.append(["Asesor", evaluacion.evaluado_por.get_full_name() if evaluacion.evaluado_por else ""])
    ws.append([])
    ws.append(["Sección", "Pregunta", "Respuesta", "Puntaje de sección"])
    for seccion in SECCIONES:
        for index, question in enumerate(seccion["questions"]):
            value = evaluacion.respuestas.get(question["code"], "")
            if isinstance(value, list):
                value = "; ".join(", ".join(str(v) for v in row.values() if v) for row in value)
            ws.append([seccion["title"], question["label"], value, evaluacion.puntajes_seccion.get(seccion["code"], "") if index == 0 else ""])
    ws.append([])
    ws.append(["PUNTAJE TOTAL", "", "", float(evaluacion.puntaje_total)])
    ws.freeze_panes = "A9"
    for col, width in {"A": 32, "B": 62, "C": 48, "D": 20}.items():
        ws.column_dimensions[col].width = width
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="evaluacion_atencion_{atencion_id}.xlsx"'
    wb.save(response)
    return response
