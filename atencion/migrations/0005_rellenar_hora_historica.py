from django.db import migrations
from django.utils import timezone


def rellenar_hora(apps, schema_editor):
    Atencion = apps.get_model("atencion", "Atencion")
    for atencion in Atencion.objects.only("pk", "creado").iterator():
        if atencion.creado:
            hora = timezone.localtime(atencion.creado).time().replace(microsecond=0)
            Atencion.objects.filter(pk=atencion.pk).update(hora=hora)


class Migration(migrations.Migration):
    dependencies = [("atencion", "0004_atencion_detalle_consulta_atencion_hora")]
    operations = [migrations.RunPython(rellenar_hora, migrations.RunPython.noop)]
