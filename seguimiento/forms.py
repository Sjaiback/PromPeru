from django import forms
from .models import GestionAtencion, SeguimientoLog


class GestionForm(forms.ModelForm):
    class Meta:
        model = GestionAtencion
        fields = ["accion", "accion_otro", "estado", "observaciones"]
        widgets = {"observaciones": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["accion"].queryset = self.fields["accion"].queryset.filter(
            activo=True
        )
        self.fields["estado"].queryset = self.fields["estado"].queryset.filter(
            activo=True
        )
        for f in self.fields.values():
            f.widget.attrs["class"] = "form-control"


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
