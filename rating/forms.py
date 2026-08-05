from django import forms


class ImportarExcelForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo Excel histórico (.xlsx)",
        widget=forms.ClearableFileInput(
            attrs={"accept": ".xlsx", "class": "form-control"}
        ),
    )
    fila_inicio_encabezado = forms.IntegerField(
        label="Primera fila de encabezado",
        initial=5,
        min_value=1,
        max_value=20,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    filas_encabezado = forms.IntegerField(
        label="Cantidad de filas de encabezado",
        initial=3,
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class EvaluacionDinamicaForm(forms.Form):
    def __init__(self, *args, criterios=None, valores=None, **kwargs):
        super().__init__(*args, **kwargs)
        valores = valores or {}
        for criterio in criterios or []:
            name = f"criterio_{criterio.pk}"
            initial = valores.get(criterio.pk)
            if criterio.tipo_dato == "booleano":
                field = forms.ChoiceField(
                    label=criterio.nombre,
                    choices=[("", "Sin responder"), ("si", "Sí"), ("no", "No")],
                    required=False,
                )
            elif criterio.tipo_dato == "numero":
                field = forms.DecimalField(
                    label=criterio.nombre, required=False, decimal_places=2
                )
            elif criterio.tipo_dato == "fecha":
                field = forms.DateField(
                    label=criterio.nombre,
                    required=False,
                    widget=forms.DateInput(attrs={"type": "date"}),
                )
            else:
                field = forms.CharField(
                    label=criterio.nombre,
                    required=False,
                    widget=forms.Textarea(attrs={"rows": 2}),
                )
            field.help_text = criterio.ayuda
            field.initial = initial
            field.widget.attrs["class"] = "form-control"
            self.fields[name] = field
