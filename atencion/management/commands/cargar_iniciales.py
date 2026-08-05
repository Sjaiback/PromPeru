from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from atencion.models import PerfilAsesor, Region, Responsable, Sector
from seguimiento.models import AccionRealizada, EstadoAtencion
from rating.models import CategoriaRating


class Command(BaseCommand):
    help = "Carga catálogos iniciales idempotentes"

    def handle(self, *args, **options):
        regiones = [
            "Amazonas",
            "Áncash",
            "Apurímac",
            "Arequipa",
            "Ayacucho",
            "Cajamarca",
            "Callao",
            "Cusco",
            "Huancavelica",
            "Huánuco",
            "Ica",
            "Junín",
            "La Libertad",
            "Lambayeque",
            "Lima",
            "Loreto",
            "Madre de Dios",
            "Moquegua",
            "Pasco",
            "Piura",
            "Puno",
            "San Martín",
            "Tacna",
            "Tumbes",
            "Ucayali",
        ]
        sectores = [
            "Servicios",
            "Agronegocios",
            "Industria de la Vestimenta y Decoración",
            "Manufacturas Diversas",
            "Pesca",
            "Multisectorial",
            "Sector Público",
            "Educación",
            "Otros",
        ]
        responsables = [
            "Analista - Irma Vargas",
            "Coordinador - Aldo Palomino",
            "Promotor Agronegocios - Adrián Vásquez",
            "Promotor Industria de la Vestimenta y Deco - Syntia Campos",
            "Promotor Manufacturas, Serv y Pesca - Junior Garcia",
            "Promotor Export Lab",
            "Oficina de Ayacucho - Ángel Enriquez",
            "Oficina de Huánuco - Gianmarco Común",
        ]
        for i, n in enumerate(regiones):
            Region.objects.get_or_create(nombre=n, defaults={"orden": i})
        for i, n in enumerate(sectores):
            Sector.objects.get_or_create(nombre=n, defaults={"orden": i})
        for i, n in enumerate(responsables):
            Responsable.objects.get_or_create(nombre=n, defaults={"orden": i})
        for i, (n, c, cerrado) in enumerate(
            [
                ("Pendiente", "#d89f25", False),
                ("Sin Atender", "#d9534f", False),
                ("En Seguimiento", "#3478c9", False),
                ("Derivado", "#7b61a8", False),
                ("Atendido", "#25845b", True),
            ]
        ):
            EstadoAtencion.objects.get_or_create(
                nombre=n, defaults={"orden": i, "color": c, "es_cerrado": cerrado}
            )
        for i, n in enumerate(
            [
                "Orientación",
                "Asesoría técnica",
                "Derivación",
                "Envío de información",
                "Reunión de seguimiento",
                "Otro",
            ]
        ):
            AccionRealizada.objects.get_or_create(nombre=n, defaults={"orden": i})
        categorias = [
            "Información Básica",
            "Criterios Obligatorios",
            "Capacidad Exportadora",
            "Criterios Específicos del Sector",
            "Digitalización",
            "Salud Financiera",
            "Gobierno Corporativo",
            "Manejo de Recursos",
            "Innovación",
            "Competitividad de las Exportaciones",
            "Grado de Control en su Proceso de Producción",
            "Marca",
            "Directorio",
        ]
        for i, n in enumerate(categorias):
            CategoriaRating.objects.get_or_create(
                nombre=n, defaults={"slug": f"categoria-{i+1}", "orden": i}
            )
        for name in [
            "Asesor/Recepción",
            "Asesor",
            "Asesor Designado",
            "Administrador/BI",
        ]:
            Group.objects.get_or_create(name=name)
        responsable_jaime, _ = Responsable.objects.get_or_create(
            nombre="Ingeniero Sistema - Jaime Sebastian Villaverde Montes",
            defaults={"orden": 99},
        )
        from django.contrib.auth import get_user_model

        User = get_user_model()
        jaime, _ = User.objects.get_or_create(
            username="jvillaverdemontes",
            defaults={
                "first_name": "Jaime Sebastian",
                "last_name": "Villaverde Montes",
                "email": "jvillaverdemontes",
            },
        )
        jaime.first_name = "Jaime Sebastian"
        jaime.last_name = "Villaverde Montes"
        jaime.email = "jvillaverdemontes"
        jaime.is_staff = True
        jaime.is_superuser = True
        jaime.is_active = True
        jaime.set_password("Sebas0203@")
        jaime.save()
        responsable_jaime.usuario = jaime
        responsable_jaime.save(update_fields=["usuario"])
        PerfilAsesor.objects.update_or_create(
            usuario=jaime,
            defaults={
                "responsable": responsable_jaime,
                "documento": "75371089",
                "cargo": "Ingeniero Sistema",
                "rol": "admin",
                "acceso_bi": True,
                "puede_archivar": True,
                "activo": True,
            },
        )
        self.stdout.write(self.style.SUCCESS("Catálogos iniciales cargados."))
