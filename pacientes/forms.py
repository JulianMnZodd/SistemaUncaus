from django import forms
from .models import Paciente
from django.core.exceptions import ValidationError
from datetime import date, datetime
import re

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['nombre', 'apellido', 'dni', 'email', 'pais', 'provincia', 'pasaporte', 'nro_afiliado',
                 'domicilio', 'localidad', 'telefono', 'fecha_nacimiento', 'genero', 
                 'obra_social', 'diabetes', 'hipertension', 'fumador', 'alergias', 
                 'antecedentes', 'cirugias','estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Juan'}),
            'apellido': forms.TextInput(attrs={'placeholder': 'Ej: Perez'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'telefono': forms.TextInput(attrs={'placeholder': 'Ej: 3624-123456'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Ej: nombre@gmail.com'}),
            'dni': forms.NumberInput(attrs={'placeholder': 'Ej: 12345678'}),
            'genero': forms.Select(choices=[('M', 'Masculino'), ('F', 'Femenino')]),
            'obra_social': forms.Select(choices=[('PAMI', 'PAMI'), ('OSDE', 'OSDE'), 
                                               ('IOMA', 'IOMA'), ('INSSSEP', 'INSSSEP'), 
                                               ('Otra', 'Otra')]),
            'domicilio': forms.TextInput(attrs={'placeholder': 'Ej: Calle 21 entre 38 y 40'}),
            'localidad': forms.TextInput(attrs={'placeholder': 'Ej: Ciudad Autónoma de Buenos Aires'}),
            'provincia': forms.TextInput(attrs={'placeholder': 'Ej: Buenos Aires'}),
            'diabetes': forms.CheckboxInput(),
            'hipertension': forms.CheckboxInput(),
            'fumador': forms.CheckboxInput(),
            'alergias': forms.Textarea(attrs={'rows': 4}),
            'antecedentes': forms.Textarea(attrs={'rows': 4}),
            'cirugias': forms.Textarea(attrs={'rows': 4}),
            'estado': forms.Select(choices=[('Vivo', 'Vivo'), ('Difunto', 'Difunto')]),
            'nro_afiliado': forms.NumberInput(attrs={'placeholder': 'Ej: 123456'}),
        }
        
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que DNI y pasaporte no sean obligatorios por defecto
        self.fields['dni'].required = False
        self.fields['pasaporte'].required = False

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if dni:  # Solo validar si se proporciona DNI
            if dni <= 0:
                raise ValidationError("El DNI debe ser un número positivo.")
            if len(str(dni)) not in (7, 8):  # Validación para Argentina
                raise ValidationError("El DNI debe tener 7 u 8 dígitos.")
        return dni

    def clean_pasaporte(self):
        pasaporte = self.cleaned_data.get('pasaporte')
        if pasaporte:  # Solo validar si se proporciona pasaporte
            # Validación de formato internacional básico
            if not re.match(r'^[A-Za-z]{1,3}\d{6,9}$', pasaporte):
                raise ValidationError(
                    "Formato de pasaporte inválido. Ejemplo válido: AB123456 o A12345678"
                )
        return pasaporte

    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        
        if not fecha_nacimiento:
            return fecha_nacimiento  # Dejar que el modelo valide si es requerido
        
        hoy = date.today()
        
        # Validar que la fecha no sea en el futuro
        if fecha_nacimiento > hoy:
            raise ValidationError("La fecha de nacimiento no puede ser en el futuro.")
        
        # Validar que el paciente tenga al menos 1 año (ajustar según necesidades)
        edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
        
        # Validar que no sea demasiado viejo (ej. 120 años)
        if edad > 120:
            raise ValidationError("Por favor ingrese una fecha de nacimiento válida.")
        
        return fecha_nacimiento
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        
        if not telefono:  # Si el campo es opcional
            return telefono
            
        # Limpiar el número: eliminar espacios, guiones, paréntesis, etc.
        telefono_limpio = re.sub(r'[+\-\s\(\)]', '', telefono)
        
        # Validar que solo contenga números y posiblemente un + al inicio
        if not re.match(r'^\+?\d+$', telefono_limpio):
            raise ValidationError("El teléfono solo puede contener números y un signo + al inicio")
        
        # Validar longitud mínima y máxima (ajusta según tu país)
        if len(telefono_limpio) < 8 or len(telefono_limpio) > 15:
            raise ValidationError("El número debe tener entre 8 y 15 dígitos (incluyendo código de país)")
        
        # Formatear opcionalmente el número antes de guardar
        # Ejemplo: convertir "3624123456" a "3624-123456"
        if len(telefono_limpio) == 10 and not telefono_limpio.startswith('+'):
            telefono_limpio = f"{telefono_limpio[:4]}-{telefono_limpio[4:]}"
            
        return telefono_limpio
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            # Validar que solo contenga letras y espacios
            if not re.match(r'^[a-zA-Z\s]+$', nombre):
                raise ValidationError("El nombre solo puede contener letras y espacios.")
            # Validar longitud mínima y máxima
            if len(nombre) < 2 or len(nombre) > 50:
                raise ValidationError("El nombre debe tener entre 2 y 50 caracteres.")
        else:
            raise ValidationError("El nombre es obligatorio.")

        return nombre

    def clean(self):
        cleaned_data = super().clean()
        dni = cleaned_data.get('dni')
        pasaporte = cleaned_data.get('pasaporte')

        # Validar que al menos uno de los dos campos esté completo
        if not dni and not pasaporte:
            raise ValidationError({
                'dni': "Debe ingresar DNI o Pasaporte.",
                'pasaporte': "Debe ingresar DNI o Pasaporte."
            })

        return cleaned_data