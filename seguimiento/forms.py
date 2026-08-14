from django import forms
from .models import GestionAtencion, SeguimientoLog


class GestionForm(forms.ModelForm):
    detalle_consulta = forms.CharField(
        label="DETALLAR CONSULTA",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    sin_observaciones = forms.BooleanField(
        label="Sin observaciones", required=False
    )

    class Meta:
        model = GestionAtencion
        fields = [
            "es_practicante",
            "accion_realizada",
            "estado_atencion",
            "estado_seguimiento",
            "observaciones",
        ]
        labels = {"es_practicante": "Es practicante"}
        widgets = {
            "accion_realizada": forms.Textarea(attrs={"rows": 4}),
            "observaciones": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.atencion_id:
            self.fields["detalle_consulta"].initial = self.instance.atencion.detalle_consulta
            self.fields["sin_observaciones"].initial = not bool(
                (self.instance.observaciones or "").strip()
            )
        for f in self.fields.values():
            f.widget.attrs["class"] = "form-control"

    def clean(self):
        data = super().clean()
        if data.get("sin_observaciones"):
            data["observaciones"] = ""
        return data


class SeguimientoForm(forms.ModelForm):
    class Meta:
        model = SeguimientoLog
        fields = ["detalle"]
        widgets = {
            "detalle": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Describa la interacción o acuerdo...",
                    "class": "form-control",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["detalle"].required = False
