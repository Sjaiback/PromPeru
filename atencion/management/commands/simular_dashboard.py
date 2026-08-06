from datetime import datetime, timedelta
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from atencion.models import Atencion, Empresa, RegistroAuditoria, Region, Responsable, Sector
from seguimiento.models import EstadoAtencion, GestionAtencion


TAG = "[SIMULACIÓN DASHBOARD]"
EMPRESA_PREFIX = "SIMULACIÓN · "


class Command(BaseCommand):
    help = "Carga datos ficticios para comprobar los Dashboards. Se pueden borrar con --limpiar."

    def add_arguments(self, parser):
        parser.add_argument("--registros", type=int, default=100)
        parser.add_argument("--limpiar", action="store_true")
        parser.add_argument("--recrear", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        demo_qs = Atencion.objects.filter(tema_consulta__startswith=TAG)
        if options["limpiar"]:
            total = demo_qs.count()
            demo_qs.delete()
            Empresa.objects.filter(nombre__startswith=EMPRESA_PREFIX).delete()
            self._auditar("eliminar", f"Se eliminaron {total} atenciones de simulación.")
            self.stdout.write(self.style.SUCCESS(f"Simulación eliminada: {total} atenciones."))
            return

        if demo_qs.exists():
            if not options["recrear"]:
                raise CommandError(
                    "Ya existe una simulación. Usa --recrear para reemplazarla o --limpiar para quitarla."
                )
            total = demo_qs.count()
            demo_qs.delete()
            Empresa.objects.filter(nombre__startswith=EMPRESA_PREFIX).delete()
            self.stdout.write(f"Se reemplazó la simulación anterior ({total} atenciones).")

        registros = options["registros"]
        if registros < 1 or registros > 1000:
            raise CommandError("Indica entre 1 y 1000 registros de simulación.")

        rng = random.Random(20260806)
        responsables = list(Responsable.objects.filter(activo=True).order_by("id"))
        regiones = list(Region.objects.filter(activo=True).order_by("id"))
        sectores = list(Sector.objects.filter(activo=True).order_by("id"))
        estados = list(EstadoAtencion.objects.filter(activo=True).order_by("orden"))
        if not all((responsables, regiones, sectores, estados)):
            raise CommandError("Faltan catálogos activos para crear la simulación.")

        empresas = []
        nombres = [
            "Andes Exporta", "Cosecha Perú", "Mares del Sur", "Textiles Wari",
            "Café de Altura", "Nativa Foods", "Innova Andina", "Selva Pura",
            "Manos del Centro", "Pacífico Selecto", "Quinua Real", "Raíces del Perú",
        ]
        total_empresas = min(max(45, registros // 2), registros)
        for indice in range(total_empresas):
            sector = sectores[indice % len(sectores)]
            region = regiones[(indice * 3) % len(regiones)]
            empresa, _ = Empresa.objects.get_or_create(
                tipo_documento="DNI",
                numero_documento=str(88000000 + indice),
                defaults={
                    "nombre": f"{EMPRESA_PREFIX}{nombres[indice % len(nombres)]} {indice + 1:02d}",
                    "tipo_personeria": "Persona Jurídica",
                    "nombres_apellidos": f"Contacto Demo {indice + 1:02d}",
                    "cargo": "Gerencia comercial",
                    "tipo_usuario": rng.choice(["Exportador", "Empresa con Potencial Exportador", "Importador"]),
                    "telefono": f"9{rng.randrange(10000000, 99999999)}",
                    "email": f"demo{indice + 1:02d}@simulacion.local",
                    "sector": sector,
                    "region": region,
                    "oferta_producto_servicio": "Registro ficticio para validar visualizaciones del dashboard.",
                },
            )
            empresas.append(empresa)

        hoy = timezone.localdate()
        inicio = hoy - timedelta(days=210)
        canales = ["WhatsApp", "Correo Electrónico", "Presencial", "Telefónica", "Reunión Virtual", "Visita a empresa"]
        pesos_canales = [28, 13, 24, 10, 16, 9]
        pesos_estados = [16, 8, 27, 12, 37]
        cerrados = [estado for estado in estados if estado.es_cerrado]
        for indice in range(registros):
            fecha = inicio + timedelta(days=rng.randrange(211))
            responsable = rng.choices(responsables, weights=[max(1, len(responsables) - i) for i in range(len(responsables))])[0]
            estado = rng.choices(estados, weights=pesos_estados[: len(estados)])[0]
            atencion = Atencion.objects.create(
                fecha=fecha,
                tipo_atencion=rng.choices(canales, weights=pesos_canales)[0],
                responsable=responsable,
                empresa=empresas[indice % total_empresas],
                tema_consulta=f"{TAG} Orientación comercial y preparación exportadora #{indice + 1:03d}.",
                origen="importado",
            )
            iniciada = timezone.make_aware(
                datetime.combine(fecha, datetime.min.time()) + timedelta(hours=8 + indice % 8)
            )
            resuelta = None
            if estado.es_cerrado:
                resuelta = iniciada + timedelta(hours=rng.randint(4, 96))
            GestionAtencion.objects.create(
                atencion=atencion,
                estado=estado,
                observaciones="Dato ficticio generado exclusivamente para probar gráficos.",
                iniciada=iniciada,
                resuelta=resuelta,
            )

        self._auditar("crear", f"Se cargaron {registros} atenciones ficticias para Dashboards.")
        self.stdout.write(self.style.SUCCESS(f"Simulación creada: {registros} atenciones y {total_empresas} empresas."))

    def _auditar(self, accion, descripcion):
        actor = get_user_model().objects.filter(username="jvillaverdemontes").first()
        RegistroAuditoria.objects.create(
            actor=actor,
            accion=accion,
            entidad="SimulacionDashboard",
            descripcion=descripcion,
        )
