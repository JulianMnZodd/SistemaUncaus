from django import forms
from .models import Habitacion, Cama, Sector

class SectorForm(forms.ModelForm):
    class Meta:
        model = Sector
        fields = ['tipo', 'cantidad_habitaciones', 'piso']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select w-full px-4 py-2.5 rounded-lg focus:outline-none'}),
            'cantidad_habitaciones': forms.NumberInput(attrs={'class': 'form-input w-full px-4 py-2.5 rounded-lg focus:outline-none', 'min': 1}),
            'piso': forms.NumberInput(attrs={'class': 'form-input w-full px-4 py-2.5 rounded-lg focus:outline-none', 'min': 0}),
        }
        labels = {
            'tipo': 'Tipo de Sector',
            'cantidad_habitaciones': 'Cantidad de Habitaciones',
            'piso': 'Número de Piso',
        }

class HabitacionForm(forms.ModelForm):
    class Meta:
        model = Habitacion
        fields = ['idsector', 'numero', 'cantidad_camas', 'tipo']
        widgets = {
            'idsector': forms.Select(attrs={'class': 'form-select w-full px-4 py-2.5 rounded-lg focus:outline-none'}),
            'numero': forms.NumberInput(attrs={'class': 'form-input w-full px-4 py-2.5 rounded-lg focus:outline-none', 'min': 1}),
            'cantidad_camas': forms.NumberInput(attrs={'class': 'form-input w-full px-4 py-2.5 rounded-lg focus:outline-none', 'min': 1}),
            'tipo': forms.Select(attrs={'class': 'form-select w-full px-4 py-2.5 rounded-lg focus:outline-none'}),
        }
        labels = {
            'idsector': 'Sector',
            'numero': 'Número de Habitación',
            'cantidad_camas': 'Cantidad de Camas',
            'tipo': 'Tipo de Habitación',
        }

class CamaForm(forms.ModelForm):
    class Meta:
        model = Cama
        fields = ['habitacion', 'estado', 'nro_cama']
        widgets = {
            'habitacion': forms.Select(attrs={'class': 'form-select w-full px-4 py-2.5 rounded-lg focus:outline-none'}),
            'estado': forms.Select(attrs={'class': 'form-select w-full px-4 py-2.5 rounded-lg focus:outline-none'}),
            'nro_cama': forms.NumberInput(attrs={'class': 'form-input w-full px-4 py-2.5 rounded-lg focus:outline-none', 'min': 1}),
        }
        labels = {
            'habitacion': 'Habitación',
            'estado': 'Estado',
            'nro_cama': 'Número de Cama',
        }
