from copy import deepcopy
from decimal import Decimal, InvalidOperation


YES_NO = [("si", "Sí"), ("no", "No")]
YES_NO_NA = YES_NO + [("na", "No aplica")]


def q(code, label, tipo="yesno", **kwargs):
    return {"code": code, "label": label, "type": tipo, **kwargs}


SECCIONES = [
    {
        "code": "obligatorios",
        "title": "Criterios obligatorios",
        "max": Decimal("8"),
        "questions": [
            q("vigencia_18", "¿La empresa tiene una vigencia mayor a 18 meses?"),
            q("correo_corporativo", "¿Cuenta con correo corporativo?"),
            q("web", "¿Cuenta con página web?"),
            q("web_url", "Enlace de la página web", "url", show_if="web:si"),
            q("redes", "¿Cuenta con redes sociales?"),
            q(
                "redes_detalle",
                "Redes sociales registradas",
                "repeat",
                show_if="redes:si",
                add_label="Añadir red social",
                subfields=[
                    {"code": "red", "label": "Red social", "type": "select", "options": [("facebook", "Facebook"), ("instagram", "Instagram"), ("tiktok", "TikTok"), ("linkedin", "LinkedIn"), ("otro", "Otra")]},
                    {"code": "url", "label": "Enlace", "type": "url"},
                ],
            ),
            q("catalogo_es", "¿Cuenta con catálogo en español?"),
            q("catalogo_en", "¿Cuenta con catálogo en inglés?"),
            q("deudas_promperu", "¿Tiene deudas activas con PROMPERÚ?"),
            q("sentinel", "Puntaje de riesgo financiero (Sentinel)", "number", step="0.01", min="0"),
        ],
    },
    {
        "code": "capacidad",
        "title": "Capacidad exportadora",
        "max": Decimal("9"),
        "questions": [
            q("remype", "¿Cuenta con registro REMYPE?", "choice", options=YES_NO_NA),
            q("test_exportador", "Resultado del test exportador", "number", step="0.01", min="0"),
            q("experiencia_exportadora", "Años de experiencia exportadora (incluye envío de muestras)", "number", step="0.1", min="0"),
            q("actividades_promocion", "¿Realizó actividades de promoción comercial?"),
            q("actividades_detalle", "Actividades de promoción comercial", "repeat", show_if="actividades_promocion:si", add_label="Añadir actividad", subfields=[{"code": "actividad", "label": "Actividad", "type": "text"}]),
            q("mercados_2_anios", "¿Exportó a mercados durante los últimos 2 años?"),
            q("mercados_detalle", "Países a los que exportó", "repeat", show_if="mercados_2_anios:si", add_label="Añadir país", subfields=[{"code": "pais", "label": "País", "type": "text"}]),
            q("company_profile", "¿Cuenta con Company Profile PROMPERÚ?"),
            q("company_profile_anio", "Año del Company Profile", "number", show_if="company_profile:si", min="1900", step="1"),
            q("ficha_tecnica", "¿Cuenta con ficha técnica?"),
            q("capacidad_produccion", "Capacidad de producción anual (todos los productos listados)", "number_blank", step="0.01", min="0"),
            q("ventas_nacional_2024", "Ventas 2024 – mercado nacional", "number_blank", step="0.01", min="0"),
            q("ventas_nacional_2025", "Ventas 2025 – mercado nacional", "number_blank", step="0.01", min="0"),
            q("presencia_nacional", "¿Tiene presencia en el mercado nacional?"),
            q("proveedor_exportadores", "¿Es proveedor de exportadores?"),
            *[q(f"ventas_internacional_{year}", f"Ventas al mercado internacional {year} (USD)", "number", step="0.01", min="0") for year in range(2021, 2026)],
            q("exportaciones_indirectas_2024", "Exportaciones indirectas 2024", "number", step="0.01", min="0"),
            q("exportaciones_indirectas_2025", "Exportaciones indirectas 2025", "number", step="0.01", min="0"),
            q("es_exportador", "¿Es exportador?"),
            q("exportador_continuo", "¿Es exportador continuo?"),
            q("marca_indecopi", "¿Tiene marca registrada en INDECOPI?"),
            q("marca_colectiva", "¿Cuenta con marca colectiva?"),
            q("marca_sectorial", "¿Cuenta con marcas sectoriales PROMPERÚ?"),
        ],
    },
    {
        "code": "especificos",
        "title": "Criterios específicos del sector",
        "max": None,
        "questions": [
            q("ruta_exportadora", "Nivel en Ruta Exportadora", "choice", options=[("basico", "Básico"), ("intermedio", "Intermedio"), ("avanzado", "Avanzado")]),
            q("programas_ruta", "¿Recibió programas o asistencia de Ruta Exportadora durante el último año?"),
            q("planta_tienda_oficina", "¿Cuenta con planta de proceso, tiendas u oficinas comerciales?"),
            q("cliente_rutex", "¿La empresa está inscrita en RUTEX?"),
        ],
    },
    {
        "code": "digitalizacion",
        "title": "Digitalización",
        "max": Decimal("4"),
        "groups": ["Página web", "Redes sociales", "Marketing digital", "Imagen corporativa digital", "Ventas online"],
        "questions": [
            q("web_responsiva", "Página web responsiva", group="Página web"),
            q("web_usabilidad", "Buena usabilidad", group="Página web"),
            q("web_actualizada", "Información y contenido actualizados", group="Página web"),
            q("web_idioma", "Disponible en otro idioma", group="Página web"),
            q("facebook", "Facebook", group="Redes sociales"),
            q("instagram", "Instagram", group="Redes sociales"),
            q("linkedin", "LinkedIn (informativo)", group="Redes sociales"),
            q("publicidad_online", "Publicidad online", group="Marketing digital"),
            q("plan_contenido", "Plan de contenido digital", group="Marketing digital"),
            q("catalogo_virtual", "Catálogo virtual o brochure", group="Imagen corporativa digital"),
            q("area_digital", "Área o responsable de gestión digital", group="Imagen corporativa digital"),
            q("manual_marca", "Manual de marca digital / identidad / Brand Book", group="Imagen corporativa digital"),
            q("video_corporativo", "Video corporativo", group="Imagen corporativa digital"),
            q("emarketplace", "E-marketplace (informativo)", group="Ventas online"),
            q("cross_border", "Participó en Cross Border de PROMPERÚ (informativo)", group="Ventas online"),
        ],
    },
    {
        "code": "financiera",
        "title": "Salud financiera",
        "max": Decimal("2.5"),
        "questions": [
            q("plan_negocio", "¿Cuenta con plan de negocio?"),
            q("estructura_costos", "¿Cuenta con estructura de costos?"),
            q("tipo_estructura_costos", "Tipo de estructura de costos", "choice", show_if="estructura_costos:si", options=[("exportacion", "De exportación"), ("produccion", "De producción")]),
            q("medio_pago", "¿Cuenta con medio de pago? (informativo)"),
            q("nivel_bancarizacion", "¿Cuenta con nivel de bancarización? (informativo)"),
            q("estudio_impacto", "¿Cuenta con plan de manejo o estudio de impacto aprobado?"),
        ],
    },
    {
        "code": "gobierno",
        "title": "Gobierno corporativo y competitividad de las exportaciones",
        "max": Decimal("3.75"),
        "questions": [
            q("proyecto_innovacion", "¿Tiene proyectos orientados a innovación e internacionalización?"),
            q("proyecto_innovacion_detalle", "Detalle del proyecto", "textarea", show_if="proyecto_innovacion:si"),
            q("premios", "¿Ha recibido premios o reconocimientos?"),
            q("premios_detalle", "Premios o reconocimientos recibidos", "textarea", show_if="premios:si"),
            q("laboratorio_calidad", "¿Cuenta con laboratorio de control de calidad y área de desarrollo?"),
            q("equipo_investigacion", "¿Cuenta con personal o equipo para investigación?"),
            q("propuesta_valor", "¿Ofrece propuesta de valor?"),
            q("numero_asociados", "Número de asociados", "number", min="0", step="1"),
            q("numero_colaboradores", "Número de colaboradores en planilla", "number", min="0", step="1"),
            q("numero_proveedores", "Número de proveedores de servicio", "number", min="0", step="1"),
            q("nivel_ingles", "Nivel de inglés del gerente general o comercial", "choice", options=[("basico", "Básico"), ("intermedio", "Intermedio"), ("avanzado", "Avanzado")]),
            q("incoterm", "Mejor Incoterm que maneja", "choice", options=[("ninguno", "Ninguno"), ("exw", "EXW"), ("fca", "FCA"), ("fas", "FAS"), ("fob", "FOB"), ("cfr", "CFR"), ("cif", "CIF"), ("cpt", "CPT"), ("cip", "CIP"), ("dap", "DAP"), ("dpu", "DPU"), ("ddp", "DDP")]),
            q("nuevos_mercados", "¿Ingresó a nuevos mercados?"),
            q("nuevos_mercados_detalle", "Mercado nuevo", "text", show_if="nuevos_mercados:si"),
            q("tiempo_gerente", "Tiempo de gestión del gerente actual", "number", min="0", step="1"),
            q("tiempo_gerente_unidad", "Unidad", "choice", options=[("meses", "Meses"), ("anios", "Años")]),
            q("responsable_comercio_exterior", "¿Cuenta con responsable de comercio exterior o pasó por Logística Asistida?"),
            q("operadores_logisticos", "Operadores logísticos con los que trabajó en los últimos 2 años", "number", min="0", step="1"),
            q("respuesta_proveedores_logisticos", "Nivel de respuesta de proveedores logísticos", "choice", options=[("alto", "Alto"), ("medio", "Medio"), ("bajo", "Bajo")]),
            q("empresa_familiar", "¿Es una empresa familiar? (informativo)"),
            q("eslabones", "Eslabones de la cadena de valor (mínimo 2)", "repeat", min_items=2, add_label="Añadir eslabón", subfields=[{"code": "eslabon", "label": "Eslabón", "type": "text"}]),
        ],
    },
    {
        "code": "directorio",
        "title": "Directorio y representantes",
        "max": None,
        "questions": [
            q("direccion", "Dirección", "text"),
            q("contactos", "Personas asesoradas", "repeat", min_items=1, add_label="Añadir persona", subfields=[
                {"code": "nombres", "label": "Nombres", "type": "text"}, {"code": "apellidos", "label": "Apellidos", "type": "text"},
                {"code": "cargo", "label": "Cargo / representante comercial", "type": "text"}, {"code": "telefono", "label": "Teléfono / celular", "type": "text"},
                {"code": "correo1", "label": "Correo 1", "type": "email"},
                {"code": "correo2_estado", "label": "¿Cuenta con correo 2?", "type": "select", "options": [("si", "Sí"), ("no", "No tiene")]},
                {"code": "correo2", "label": "Correo 2", "type": "email"},
            ]),
        ],
    },
]


def numero(value):
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def puntuar(respuestas):
    si = lambda key: respuestas.get(key) == "si"
    oblig = sum([
        si("vigencia_18"), si("correo_corporativo"), si("web"), si("redes"),
        si("catalogo_es"), si("catalogo_en"), respuestas.get("deudas_promperu") == "no",
        numero(respuestas.get("sentinel")) < 2 if respuestas.get("sentinel") not in (None, "") else False,
    ])
    actividades = len([x for x in respuestas.get("actividades_detalle", []) if x.get("actividad")])
    mercados = len([x for x in respuestas.get("mercados_detalle", []) if x.get("pais")])
    internacional = sum(numero(respuestas.get(f"ventas_internacional_{y}")) for y in range(2021, 2026))
    capacidad = Decimal("0")
    capacidad += 1 if numero(respuestas.get("test_exportador")) >= Decimal("1.5") else 0
    capacidad += 1 if numero(respuestas.get("experiencia_exportadora")) >= 2 else 0
    capacidad += Decimal("1") if actividades >= 2 else Decimal("0.5") if actividades == 1 else 0
    capacidad += 1 if mercados >= 2 else 0
    capacidad += Decimal("0.5") if si("presencia_nacional") else 0
    capacidad += Decimal("0.5") if si("proveedor_exportadores") else 0
    capacidad += 1 if internacional >= 150000 else 0
    capacidad += 1 if si("marca_indecopi") else 0
    capacidad += Decimal("0.5") if si("marca_colectiva") or si("marca_sectorial") else 0
    digital = sum(Decimal(str(points)) for key, points in {
        "web_responsiva": .25, "web_usabilidad": .25, "web_actualizada": .25, "web_idioma": .25,
        "facebook": .5, "instagram": .5, "publicidad_online": .5, "plan_contenido": .5,
        "catalogo_virtual": .25, "manual_marca": .5, "video_corporativo": .25,
    }.items() if si(key))
    financiera = (Decimal("1") if si("plan_negocio") else 0)
    if si("estructura_costos"):
        financiera += Decimal("1") if respuestas.get("tipo_estructura_costos") == "exportacion" else Decimal("0.5") if respuestas.get("tipo_estructura_costos") == "produccion" else 0
    financiera += Decimal("0.5") if si("estudio_impacto") else 0
    ingles = {"basico": 0, "intermedio": Decimal("0.5"), "avanzado": Decimal("1")}.get(respuestas.get("nivel_ingles"), 0)
    incoterms = ["fob", "cfr", "cif", "cpt", "cip", "dap", "dpu", "ddp"]
    gobierno = sum(Decimal("0.25") for k in ["proyecto_innovacion", "equipo_investigacion", "propuesta_valor"] if si(k))
    gobierno += ingles + (1 if respuestas.get("incoterm") in incoterms else 0) + (1 if si("responsable_comercio_exterior") else 0)
    puntos = {"obligatorios": Decimal(oblig), "capacidad": capacidad, "digitalizacion": digital, "financiera": financiera, "gobierno": gobierno}
    return puntos, sum(puntos.values(), Decimal("0"))


def preparar_ficha(valores):
    secciones = deepcopy(SECCIONES)
    for seccion in secciones:
        for question in seccion["questions"]:
            value = valores.get(question["code"], "")
            question["value"] = value
            if question["type"] == "repeat":
                rows = value if isinstance(value, list) else []
                minimum = question.get("min_items", 1)
                rows = rows + [{} for _ in range(max(0, minimum - len(rows)))]
                question["rows"] = [
                    {"fields": [{**sub, "value": row.get(sub["code"], "")} for sub in question["subfields"]]}
                    for row in rows
                ]
    return secciones
