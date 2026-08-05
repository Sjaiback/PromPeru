import io, re, unicodedata
from decimal import Decimal, InvalidOperation
from openpyxl import load_workbook
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from atencion.models import Empresa, Region, Sector
from .forms import ImportarExcelForm
from .forms import EvaluacionDinamicaForm
from .models import (
    CategoriaRating,
    CriterioRating,
    EmpresaRating,
    ImportacionRating,
    MapeoColumna,
    ValorCriterio,
)
from atencion.auditoria import registrar as auditar


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
    rating, _ = EmpresaRating.objects.get_or_create(empresa=empresa)
    criterios = CriterioRating.objects.filter(activo=True).select_related("categoria")
    valores_obj = {
        v.criterio_id: v for v in rating.criterios.select_related("criterio")
    }
    iniciales = {k: _valor_inicial(v) for k, v in valores_obj.items()}
    form = EvaluacionDinamicaForm(
        request.POST or None, criterios=criterios, valores=iniciales
    )
    if request.method == "POST" and form.is_valid():
        for criterio in criterios:
            value = form.cleaned_data.get(f"criterio_{criterio.pk}")
            defaults = {"valor_texto": "", "valor_numero": None, "valor_booleano": None}
            if criterio.tipo_dato == "booleano":
                defaults["valor_booleano"] = (
                    True if value == "si" else False if value == "no" else None
                )
            elif criterio.tipo_dato == "numero":
                defaults["valor_numero"] = value
            else:
                defaults["valor_texto"] = str(value or "")
            ValorCriterio.objects.update_or_create(
                rating=rating, criterio=criterio, defaults=defaults
            )
        rating.recalcular()
        auditar(
            request,
            "editar",
            rating,
            descripcion=f"Evaluación de {empresa.nombre} actualizada",
        )
        messages.success(
            request,
            "Evaluación guardada. Todas las respuestas quedaron vinculadas al asesor y la empresa.",
        )
        return redirect("rating:evaluar", empresa_id=empresa.pk)
    categorias = []
    for categoria in CategoriaRating.objects.filter(activa=True):
        names = [
            f"criterio_{c.pk}" for c in criterios if c.categoria_id == categoria.pk
        ]
        fields = [form[name] for name in names if name in form.fields]
        if fields:
            categorias.append((categoria, fields))
    return render(
        request,
        "rating/evaluar.html",
        {"empresa": empresa, "rating": rating, "form": form, "categorias": categorias},
    )
