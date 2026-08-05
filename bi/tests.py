import tempfile, zipfile
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from atencion.models import (
    ArchivoAtenciones,
    Atencion,
    Empresa,
    PerfilAsesor,
    Region,
    Responsable,
    Sector,
)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ArchivoMensualTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("adminbi", password="x")
        responsable = Responsable.objects.create(nombre="Asesor Uno")
        PerfilAsesor.objects.create(
            usuario=user,
            responsable=responsable,
            acceso_bi=True,
            puede_archivar=True,
            rol="admin",
        )
        region = Region.objects.create(nombre="Junín")
        sector = Sector.objects.create(nombre="Servicios")
        empresa = Empresa.objects.create(
            tipo_documento="RUC",
            numero_documento="20123456789",
            nombre="Empresa",
            tipo_usuario="Exportador",
            telefono="999999999",
            email="a@b.com",
            sector=sector,
            region=region,
            oferta_producto_servicio="Servicio",
        )
        Atencion.objects.create(
            tipo_atencion="WhatsApp",
            responsable=responsable,
            empresa=empresa,
            registrado_por=user,
            origen="asesor",
        )
        self.user = user
        self.empresa = empresa
        self.client.force_login(user)

    def test_zip_segmentado_y_depuracion_conserva_empresa(self):
        response = self.client.post(
            reverse("bi:archivos"), {"desde": "2020-01-01", "hasta": "2030-12-31"}
        )
        self.assertEqual(response.status_code, 302)
        archivo = ArchivoAtenciones.objects.get()
        with zipfile.ZipFile(archivo.archivo.path) as zf:
            self.assertIn("00_GLOBAL_atenciones.xlsx", zf.namelist())
            self.assertTrue(any(n.startswith("asesores/") for n in zf.namelist()))
        self.client.get(reverse("bi:descargar_archivo", args=[archivo.pk]))
        self.client.post(
            reverse("bi:depurar_archivo", args=[archivo.pk]),
            {"confirmacion": "DEPURAR"},
        )
        self.assertEqual(Atencion.objects.count(), 0)
        self.assertTrue(Empresa.objects.filter(pk=self.empresa.pk).exists())
        archivo.refresh_from_db()
        self.assertTrue(archivo.depurado)
