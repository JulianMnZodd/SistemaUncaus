from django import forms
from .models import Diagnostico, Seguimiento, Medicacion, SignosVitales
from personal.models import Medico
from .models import Paciente, Cama
from django_select2.forms import ModelSelect2Widget


from django import forms

from django import forms
from django.core.exceptions import ValidationError
from .models import Paciente, Internacion

class AsignarCamaForm(forms.Form):
    paciente_id = forms.IntegerField(widget=forms.HiddenInput())  # Campo oculto para el ID del paciente
    nota_ingreso = forms.CharField(
        widget=forms.Textarea(attrs={
            "rows": 4,
            "class": "w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
        }), 
        label="Nota de Ingreso"
    )

    def clean_paciente_id(self):
        paciente_id = self.cleaned_data.get('paciente_id')
        if not paciente_id:
            raise ValidationError("Debes seleccionar un paciente.")

        # Verificar si el paciente ya está asignado a una cama y no ha sido dado de alta
        paciente = Paciente.objects.get(idpaciente=paciente_id)
        internacion_activa = Internacion.objects.filter(
            idpaciente=paciente,
            fecha_alta__isnull=True  # Solo si no tiene fecha de alta
        ).exists()

        if internacion_activa:
            raise ValidationError("Este paciente ya está asignado a una cama y no ha sido dado de alta.")

        return paciente_id


class DiagnosticoForm(forms.ModelForm):
    class Meta:
        model = Diagnostico
        fields = ['fecha', 'detalles', 'gravedad', 'tratamiento', 'idmedico_derivado']
        widgets = {
            'fecha': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'detalles': forms.Textarea(attrs={'rows': 4}),
            'gravedad': forms.TextInput(attrs={'placeholder': 'Ej: Leve'}),
            'tratamiento': forms.Textarea(attrs={'rows': 4}),
            'idmedico_derivado': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'fecha': 'Fecha',
            'detalles': 'Detalles',
            'gravedad': 'Gravedad',
            'tratamiento': 'Tratamiento',
            'idmedico_derivado': 'Médico Derivado (opcional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['idmedico_derivado'].queryset = Medico.objects.all()

class SeguimientoForm(forms.ModelForm):
    class Meta:
        model = Seguimiento
        fields = ["observacion"]
        widgets = {
            "observacion": forms.Textarea(attrs={"rows": 4}),
        }


class MedicacionForm(forms.ModelForm):
    class Meta:
        model = Medicacion
        fields = ["tipo", "nombre", "hora_medicacion"]
        widgets = {
            "hora_medicacion": forms.TimeInput(attrs={"type": "time"}),
        }


class SignosVitalesForm(forms.ModelForm):
    class Meta:
        model = SignosVitales
        fields = ["temperatura_corporal", "pulso", "frecuencia_respiratoria"]
        widgets = {
            "temperatura_corporal": forms.NumberInput(attrs={"step": 0.1}),
            "pulso": forms.NumberInput(attrs={"step": 1}),
            "frecuencia_respiratoria": forms.NumberInput(attrs={"step": 1}),
        }


