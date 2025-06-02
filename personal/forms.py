from django import forms
from .models import Persona, Medico,Recepcionista,Enfermero
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.core.exceptions import ValidationError
from datetime import date
import re

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Correo electrónico", widget=forms.EmailInput(attrs={'class': 'form-control'}))


from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Persona

class CustomUserCreationForm(UserCreationForm):
    usable_password = None
    class Meta:
        model = Persona
        fields = ['first_name', 'last_name', 'email', 'dni', 'telefono', 'domicilio', 'genero', 'fecha_nacimiento']
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'dni': 'DNI',
            'telefono': 'Teléfono',
            'domicilio': 'Domicilio',
            'genero': 'Género',
            'fecha_nacimiento': 'Fecha de nacimiento',
            
            }
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'telefono': forms.TextInput(attrs={'placeholder': 'Ej: 3624-123456'}),
            'dni': forms.NumberInput(attrs={'min': 0}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        
        #agregar validación para que solo contenga letras y espacios
        if not first_name.isalpha() and not all(c.isspace() for c in first_name):
            raise ValidationError("El nombre solo puede contener letras.")
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name.isalpha() and not all(c.isspace() for c in last_name):
            raise ValidationError("El apellido solo puede contener letras.")
        return last_name
        
    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if dni:
            if dni < 1_000_000:  # DNI argentino mínimo 1.000.000
                raise ValidationError("El DNI debe tener al menos 7 dígitos")
            if dni > 99_999_999:  # DNI argentino máximo 99.999.999
                raise ValidationError("El DNI no puede tener más de 8 dígitos")
        return dni

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

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha:
            hoy = date.today()
            edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
            
            if edad < 18:
                raise ValidationError("Debe ser mayor de 18 años")
            if edad > 120:
                raise ValidationError("Edad no válida")
        return fecha 
        
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = Persona
        fields = ['first_name', 'last_name', 'email', 'telefono', 'domicilio',]
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'password': 'Contraseña',
        }

class MedicoForm(forms.ModelForm):
    class Meta:
        model = Medico
        fields = ['especializacion', 'matricula']
        
    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')
        if matricula:
            if not matricula.isdigit():
                raise ValidationError("La matrícula debe contener solo números")
            if len(matricula) < 4 or len(matricula) > 8:
                raise ValidationError("La matrícula debe tener entre 4 y 8 dígitos")
        return matricula
        
class EnfermeroForm(forms.ModelForm):
    class Meta:
        model = Enfermero
        fields = ['matricula']
    
    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')
        if matricula:
            if not matricula.isdigit():
                raise ValidationError("La matrícula debe contener solo números")
            if len(matricula) < 4 or len(matricula) > 8:
                raise ValidationError("La matrícula debe tener entre 4 y 8 dígitos")
        return matricula
        
class RecepcionistaForm(forms.ModelForm):
    class Meta:
        model = Recepcionista
        fields = ['turno']
        widgets = {
            'turno': forms.Select(choices=[('mañana', 'Mañana'), ('tarde', 'Tarde'), ('noche', 'Noche')]),
        }
