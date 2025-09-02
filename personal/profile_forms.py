from django import forms
from .models import Persona
from django.core.exceptions import ValidationError
import re

class UserProfileForm(forms.ModelForm):
    """
    Formulario para editar el perfil de usuario, excluyendo campos sensibles
    como contraseñas y permisos.
    """
    class Meta:
        model = Persona
        fields = ['first_name', 'last_name', 'email', 'dni', 'telefono', 
                 'domicilio', 'genero', 'fecha_nacimiento']
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
            'fecha_nacimiento': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-input w-full px-4 py-2.5 rounded-lg border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-2.5 rounded-lg border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-2.5 rounded-lg border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input w-full px-4 py-2.5 rounded-lg border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
            }),
            'dni': forms.NumberInput(attrs={
                'min': 0,
                'class': 'form-input w-full px-4 py-2.5 rounded-lg border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
            }),
            'telefono': forms.TextInput(attrs={
                'placeholder': 'Ej: 3624-123456',
                'class': 'form-input w-full px-4 py-2.5 rounded-lg border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
            }),
            'domicilio': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-2.5 rounded-lg border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
            }),
            'genero': forms.Select(attrs={
                'class': 'form-select w-full px-4 py-2.5 rounded-lg border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
            }),
        }
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not all(c.isalpha() or c.isspace() for c in first_name):
            raise ValidationError("El nombre solo puede contener letras y espacios.")
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not all(c.isalpha() or c.isspace() for c in last_name):
            raise ValidationError("El apellido solo puede contener letras y espacios.")
        return last_name
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Eliminar caracteres no numéricos para la validación
            telefono_limpio = re.sub(r'[^\d]', '', telefono)
            if not telefono_limpio.isdigit() or len(telefono_limpio) < 7:
                raise ValidationError("Ingrese un número de teléfono válido.")
        return telefono

class PasswordChangeForm(forms.Form):
    """
    Formulario para cambiar la contraseña del usuario.
    """
    current_password = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full px-4 py-2.5 rounded-lg border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
        })
    )
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full px-4 py-2.5 rounded-lg border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
        })
    )
    new_password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full px-4 py-2.5 rounded-lg border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise ValidationError("La contraseña actual es incorrecta.")
        return current_password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError("Las nuevas contraseñas no coinciden.")
                
        return cleaned_data
