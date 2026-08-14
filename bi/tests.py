import tempfile, zipfile
from io import BytesIO
from unittest import mock
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from openpyxl import load_workbook
from atencion.models import (
    ArchivoAtenciones,
    Atencion,
    Empresa,
    PerfilAsesor,
    Region,
    Responsable,
    RespaldoLimpieza,
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

    def test_dashboard_renderiza_graficos_interactivos(self):
        response = self.client.get(reverse("bi:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboards")
        self.assertContains(response, "dashboard-chart-data")
        self.assertContains(response, "trendChart")
        self.assertContains(response, "statusLegend")
        self.assertContains(response, 'data-chart-period="dia"')
        self.assertContains(response, 'data-chart-period="semana"')
        self.assertContains(response, 'data-chart-period="mes"')
        self.assertIn("tendencias", response.context["chart_data"])
        self.assertEqual(
            set(response.context["chart_data"]["tendencias"]),
            {"dia", "semana", "mes"},
        )

    def test_respaldos_privados_solo_sistemas(self):
        url = reverse("rating:respaldos")
        self.assertEqual(self.client.get(url).status_code, 403)
        sistemas = get_user_model().objects.create_superuser(
            settings.SYSTEM_ADMIN_USERNAME,
            "sistemas@example.test",
            "clave-segura-2026",
        )
        self.client.force_login(sistemas)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_excel_respeta_las_23_columnas_y_el_orden_oficial(self):
        response = self.client.get(reverse("bi:excel"))
        self.assertEqual(response.status_code, 200)
        workbook = load_workbook(BytesIO(response.content), data_only=True)
        headers = [cell.value for cell in workbook.active[1]]
        self.assertEqual(
            headers,
            [
                "N°", "FECHA", "TIPO DE ATENCIÓN", "RESPONSABLE", "SECTOR",
                "LÍNEA", "PRODUCTO", "REGIÓN", "TIPO DE DOCUMENTO",
                "N° DEL DOCUMENTO", "EMPRESA / INSTITUCIÓN / PERSONA NATURAL",
                "TIPO DE USUARIO", "TIPO DE PERSONERÍA", "NOMBRE Y APELLIDO",
                "CARGO", "TELEFONO/CELULAR", "E-MAIL", "TEMA DE CONSULTA",
                "DETALLAR CONSULTA", "ACCIÓN REALIZADA", "ESTADO DE LA ATENCIÓN",
                "SEGUIMIENTO", "OBSERVACIONES",
            ],
        )
        self.assertEqual(workbook.active["F2"].value, None)

    @mock.patch("rating.views.subir_respaldo")
    def test_limpieza_exige_exportacion_checkbox_y_confirmacion(self, subir):
        subir.return_value = {
            "bucket": "promperu-respaldos",
            "ruta": "limpiezas/prueba.xlsx",
            "tamano": 2048,
            "checksum": "a" * 64,
        }
        limpiar_url = reverse("rating:limpiar_datos")
        response = self.client.get(limpiar_url)
        self.assertContains(response, "Primero exporta los datos")

        self.client.post(
            limpiar_url,
            {"datos_exportados": "1", "confirmacion": "LIMPIAR"},
        )
        self.assertEqual(Atencion.objects.count(), 1)

        export = self.client.get(reverse("bi:excel") + "?respaldo=1")
        self.assertEqual(export.status_code, 200)
        self.assertIn("ultima_exportacion_limpieza", self.client.session)

        nueva = Atencion.objects.create(
            tipo_atencion="Presencial",
            responsable=self.user.perfil_asesor.responsable,
            empresa=self.empresa,
            registrado_por=self.user,
            origen="asesor",
        )
        response = self.client.post(
            limpiar_url,
            {"datos_exportados": "1", "confirmacion": "LIMPIAR"},
        )
        self.assertRedirects(response, reverse("rating:intercambiar"))
        self.assertEqual(Atencion.objects.count(), 1)
        self.assertTrue(Atencion.objects.filter(pk=nueva.pk).exists())
        self.assertTrue(Empresa.objects.filter(pk=self.empresa.pk).exists())
        self.assertEqual(RespaldoLimpieza.objects.count(), 1)
        self.assertEqual(RespaldoLimpieza.objects.get().total_atenciones, 1)

    @mock.patch("rating.views.subir_respaldo", side_effect=RuntimeError("sin storage"))
    def test_limpieza_se_cancela_si_falla_el_respaldo_privado(self, subir):
        self.client.get(reverse("bi:excel") + "?respaldo=1")
        response = self.client.post(
            reverse("rating:limpiar_datos"),
            {"datos_exportados": "1", "confirmacion": "LIMPIAR"},
        )
        self.assertRedirects(response, reverse("rating:limpiar_datos"))
        self.assertEqual(Atencion.objects.count(), 1)
        self.assertEqual(RespaldoLimpieza.objects.count(), 0)
