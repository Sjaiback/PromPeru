from datetime import date
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
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
        self.cliente = get_user_model().objects.create_user(
            "cliente", password="cliente-seguro-2026"
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

    def test_formulario_publico_requiere_login_cliente(self):
        response = self.client.get(reverse("atencion:publico"))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse("atencion:publico")).status_code, 200)

    def test_publico_crea_empresa_atencion_y_auditoria(self):
        self.client.force_login(self.cliente)
        response = self.client.post(reverse("atencion:publico"), self.payload_nuevo())
        self.assertRedirects(
            response, reverse("atencion:publico"), fetch_redirect_response=False
        )
        self.assertEqual(Empresa.objects.count(), 1)
        self.assertEqual(Atencion.objects.get().origen, "publico")
        self.assertEqual(RegistroAuditoria.objects.get().actor, None)
        response = self.client.get(reverse("atencion:publico"))
        self.assertContains(response, "En un momento te atenderemos")
        self.assertContains(response, self.responsable.nombre)
        self.assertContains(response, "data-confirmation-modal")

    def test_cliente_existente_solo_responde_canal_y_responsable(self):
        self.client.force_login(self.cliente)
        self.client.post(reverse("atencion:publico"), self.payload_nuevo())
        minimal = {
            "tipo_documento": "RUC",
            "numero_documento": "20123456789",
            "tipo_atencion": "WhatsApp",
            "responsable": self.responsable.pk,
            "tema_consulta": "",
        }
        response = self.client.post(reverse("atencion:publico"), minimal)
        self.assertRedirects(response, reverse("atencion:publico"))
        self.assertEqual(Empresa.objects.count(), 1)
        self.assertEqual(Atencion.objects.count(), 2)

    def test_formulario_publico_ajax_devuelve_responsable_para_confirmacion(self):
        self.client.force_login(self.cliente)
        response = self.client.post(
            reverse("atencion:publico"),
            self.payload_nuevo(),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(response.json()["responsable"], self.responsable.nombre)

    def test_registro_asesor_fuerza_su_responsable(self):
        otro = Responsable.objects.create(nombre="Otro asesor")
        self.client.login(username="asesor", password="test-pass-123")
        data = self.payload_nuevo()
        data["responsable"] = otro.pk
        response = self.client.post(reverse("atencion:registrar"), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Atencion.objects.get().responsable, self.responsable)
        self.assertEqual(Atencion.objects.get().registrado_por, self.user)

    def test_detalle_de_atencion_muestra_fecha_sin_error(self):
        atencion = Atencion.objects.create(
            tipo_atencion="Presencial",
            responsable=self.responsable,
            empresa=Empresa.objects.create(
                tipo_documento="DNI",
                numero_documento="12345678",
                nombre="Empresa de prueba",
                tipo_usuario="Exportador",
                telefono="999888777",
                email="empresa@example.test",
                sector=self.sector,
                region=self.region,
                oferta_producto_servicio="Prueba",
            ),
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("atencion:detalle", args=[atencion.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "de")

    def test_api_no_expone_contacto_sin_actualizar(self):
        self.client.force_login(self.cliente)
        self.client.post(reverse("atencion:publico"), self.payload_nuevo())
        data = self.client.get(
            reverse("atencion:buscar_documento"),
            {"tipo": "RUC", "numero": "20123456789"},
        ).json()
        self.assertTrue(data["encontrado"])
        self.assertNotIn("email", data)
        self.assertNotIn("telefono", data)

    def test_auditoria_muestra_registros_del_formulario_publico(self):
        self.client.force_login(self.cliente)
        self.client.post(reverse("atencion:publico"), self.payload_nuevo())
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save(update_fields=["is_staff", "is_superuser"])
        self.client.force_login(self.user)
        response = self.client.get(reverse("atencion:auditoria"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Formulario público")

    def test_configuracion_interna_no_redirige_al_admin_django(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        self.client.force_login(self.user)
        response = self.client.get(reverse("atencion:configuracion"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Catálogos activos")

    def test_cliente_solo_accede_al_formulario_publico(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse("atencion:publico")).status_code, 200)
        response = self.client.get(reverse("atencion:inicio"))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "No deberías estar aquí", status_code=403)
        response = self.client.get(reverse("atencion:empresas"))
        self.assertEqual(response.status_code, 403)

    def test_asesor_actualiza_sus_datos_personales(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("atencion:mi_perfil"),
            {
                "accion": "datos",
                "first_name": "Asesor",
                "last_name": "Actualizado",
                "email": "asesor.actualizado@example.test",
                "documento": "87654321",
                "cargo": "Asesor comercial",
            },
        )
        self.assertRedirects(response, reverse("atencion:mi_perfil"))
        self.user.refresh_from_db()
        self.perfil.refresh_from_db()
        self.assertEqual(self.user.email, "asesor.actualizado@example.test")
        self.assertEqual(self.perfil.documento, "87654321")

    def test_asesor_cambia_su_contrasena_y_mantiene_sesion(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("atencion:mi_perfil"),
            {
                "accion": "password",
                "old_password": "test-pass-123",
                "new_password1": "Nueva-clave-segura-2026",
                "new_password2": "Nueva-clave-segura-2026",
            },
        )
        self.assertRedirects(response, reverse("atencion:mi_perfil"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Nueva-clave-segura-2026"))
        self.assertEqual(self.client.get(reverse("atencion:mi_perfil")).status_code, 200)

    def test_cliente_no_puede_acceder_a_mi_perfil(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse("atencion:mi_perfil")).status_code, 403)

    def test_admin_django_solo_admite_cuenta_de_sistemas(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "No deberías estar aquí", status_code=403)

        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save(update_fields=["is_staff", "is_superuser"])
        self.client.force_login(self.user)
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "No deberías estar aquí", status_code=403)

        system_user = get_user_model().objects.create_superuser(
            "jvillaverdemontes", "sistemas@example.test", "clave-segura-2026"
        )
        self.client.force_login(system_user)
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    @override_settings(DEBUG=False)
    def test_ruta_inexistente_muestra_pagina_404_personalizada(self):
        response = self.client.get("/esta-ruta-no-existe/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Parece que esta página no existe", status_code=404)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_recuperacion_de_contrasena_envia_enlace_al_correo_registrado(self):
        self.user.email = "asesor@example.test"
        self.user.save(update_fields=["email"])
        response = self.client.post(
            reverse("password_reset"), {"email": "asesor@example.test"}
        )
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("restablecer", mail.outbox[0].body)
        self.assertIn("PROMPERÚ", mail.outbox[0].alternatives[0].content)

    def test_aldo_puede_crear_cuentas_con_rol_limitado(self):
        aldo_responsable = Responsable.objects.create(
            nombre="Coordinador - Aldo Palomino"
        )
        aldo = get_user_model().objects.create_user("aldo", password="clave-ald0")
        PerfilAsesor.objects.create(
            usuario=aldo,
            responsable=aldo_responsable,
            rol="coordinador",
            activo=True,
        )
        nuevo_responsable = Responsable.objects.create(nombre="Nueva asesora")
        self.client.force_login(aldo)
        response = self.client.post(
            reverse("atencion:asesor_crear"),
            {
                "first_name": "Ana",
                "last_name": "López",
                "username": "ana.lopez",
                "email": "ana.lopez@example.test",
                "password": "temporal-segura-2026",
                "responsable": nuevo_responsable.pk,
                "documento": "12345678",
                "cargo": "Asesora comercial",
                "rol": "asesor",
            },
        )
        self.assertRedirects(response, reverse("atencion:asesores"))
        perfil_nuevo = PerfilAsesor.objects.get(usuario__username="ana.lopez")
        self.assertEqual(perfil_nuevo.rol, "asesor")
        self.assertEqual(perfil_nuevo.responsable, nuevo_responsable)

        self.client.force_login(self.user)
        self.assertEqual(
            self.client.get(reverse("atencion:asesor_crear")).status_code, 403
        )
