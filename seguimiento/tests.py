from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from atencion.models import Atencion, Empresa, PerfilAsesor, Region, Responsable, Sector
from .models import EstadoAtencion, GestionAtencion


class BandejaSeguimientoTests(TestCase):
    def setUp(self):
        region = Region.objects.create(nombre="Junín")
        sector = Sector.objects.create(nombre="Servicios")
        empresa = Empresa.objects.create(
            tipo_documento="RUC",
            numero_documento="20111111111",
            nombre="Empresa Centro",
            tipo_usuario="Exportador",
            telefono="999111222",
            email="centro@example.com",
            sector=sector,
            region=region,
            oferta_producto_servicio="Servicios empresariales",
        )
        self.responsable = Responsable.objects.create(nombre="Asesor Centro")
        otro_responsable = Responsable.objects.create(nombre="Asesor Norte")
        pendiente = EstadoAtencion.objects.create(nombre="Pendiente", es_cerrado=False)
        cerrado = EstadoAtencion.objects.create(nombre="Cerrado", es_cerrado=True)
        propia = Atencion.objects.create(
            empresa=empresa,
            responsable=self.responsable,
            tipo_atencion="Presencial",
            tema_consulta="Consulta propia",
        )
        ajena = Atencion.objects.create(
            empresa=empresa,
            responsable=otro_responsable,
            tipo_atencion="WhatsApp",
            tema_consulta="Consulta de otro asesor",
        )
        GestionAtencion.objects.create(atencion=propia, estado=pendiente)
        GestionAtencion.objects.create(atencion=ajena, estado=cerrado)
        self.usuario = get_user_model().objects.create_user(
            "asesor-seguimiento", password="test-seguimiento-123"
        )
        PerfilAsesor.objects.create(
            usuario=self.usuario,
            responsable=self.responsable,
            cargo="Asesor",
            rol="asesor",
        )

    def test_asesor_ve_resumen_y_solo_su_carga(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse("seguimiento:bandeja"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["resumen"]["total"], 1)
        self.assertEqual(response.context["resumen"]["pendientes"], 1)
        self.assertEqual(response.context["resumen"]["cerradas"], 0)
        self.assertContains(response, "Las conversaciones que")
        self.assertContains(response, "Consulta propia")
        self.assertNotContains(response, "Consulta de otro asesor")
