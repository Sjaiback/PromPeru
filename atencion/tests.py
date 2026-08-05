from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import (
    Atencion,
    Empresa,
    PerfilAsesor,
    Region,
    RegistroAuditoria,
    Responsable,
    Sector,
)
from seguimiento.models import EstadoAtencion


class FlujoAtencionTests(TestCase):
    def setUp(self):
        self.region = Region.objects.create(nombre="Junín")
        self.sector = Sector.objects.create(nombre="Servicios")
        self.responsable = Responsable.objects.create(nombre="Analista - Irma Vargas")
        EstadoAtencion.objects.create(nombre="Pendiente")
        self.user = get_user_model().objects.create_user(
            "asesor", password="test-pass-123"
        )
        self.perfil = PerfilAsesor.objects.create(
            usuario=self.user, responsable=self.responsable, cargo="Analista"
        )

    def payload_nuevo(self):
        return {
            "tipo_documento": "RUC",
            "numero_documento": "20123456789",
            "actualizar_datos": "on",
            "tipo_atencion": "Presencial",
            "responsable": self.responsable.pk,
            "sector": self.sector.pk,
            "oferta_producto_servicio": "Consultoría",
            "region": self.region.pk,
            "nombre": "Empresa Andina",
            "tipo_personeria": "Persona Jurídica",
            "nombres_apellidos": "Ana Pérez",
            "cargo": "Gerente",
            "tipo_usuario": "Exportador",
            "telefono": "999888777",
            "email": "ana@example.com",
            "tema_consulta": "Orientación",
        }

    def test_formulario_publico_no_requiere_login(self):
        self.assertEqual(self.client.get(reverse("atencion:publico")).status_code, 200)

    def test_publico_crea_empresa_atencion_y_auditoria(self):
        response = self.client.post(reverse("atencion:publico"), self.payload_nuevo())
        self.assertRedirects(response, reverse("atencion:gracias"))
        self.assertEqual(Empresa.objects.count(), 1)
        self.assertEqual(Atencion.objects.get().origen, "publico")
        self.assertEqual(RegistroAuditoria.objects.get().actor, None)

    def test_cliente_existente_solo_responde_canal_y_responsable(self):
        self.client.post(reverse("atencion:publico"), self.payload_nuevo())
        minimal = {
            "tipo_documento": "RUC",
            "numero_documento": "20123456789",
            "tipo_atencion": "WhatsApp",
            "responsable": self.responsable.pk,
            "tema_consulta": "",
        }
        response = self.client.post(reverse("atencion:publico"), minimal)
        self.assertRedirects(response, reverse("atencion:gracias"))
        self.assertEqual(Empresa.objects.count(), 1)
        self.assertEqual(Atencion.objects.count(), 2)

    def test_registro_asesor_fuerza_su_responsable(self):
        otro = Responsable.objects.create(nombre="Otro asesor")
        self.client.login(username="asesor", password="test-pass-123")
        data = self.payload_nuevo()
        data["responsable"] = otro.pk
        response = self.client.post(reverse("atencion:registrar"), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Atencion.objects.get().responsable, self.responsable)
        self.assertEqual(Atencion.objects.get().registrado_por, self.user)

    def test_api_no_expone_contacto_sin_actualizar(self):
        self.client.post(reverse("atencion:publico"), self.payload_nuevo())
        data = self.client.get(
            reverse("atencion:buscar_documento"),
            {"tipo": "RUC", "numero": "20123456789"},
        ).json()
        self.assertTrue(data["encontrado"])
        self.assertNotIn("email", data)
        self.assertNotIn("telefono", data)
