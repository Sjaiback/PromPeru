from django.db import migrations


def normalizar(apps, schema_editor):
    Gestion = apps.get_model("seguimiento", "GestionAtencion")
    for gestion in Gestion.objects.select_related("estado").iterator():
        accion = gestion.accion_otro or ""
        if not accion and gestion.accion_id:
            accion = gestion.accion.nombre
        finalizado = bool(gestion.estado_id and gestion.estado.es_cerrado)
        Gestion.objects.filter(pk=gestion.pk).update(
            accion_realizada=accion,
            estado_atencion="atendido" if finalizado else "sin_atender",
            estado_seguimiento="finalizado" if finalizado else "en_proceso",
        )


class Migration(migrations.Migration):
    dependencies = [("seguimiento", "0002_gestionatencion_accion_realizada_and_more")]
    operations = [migrations.RunPython(normalizar, migrations.RunPython.noop)]
