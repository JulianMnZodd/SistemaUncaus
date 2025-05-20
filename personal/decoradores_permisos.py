from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .models import Recepcionista, Medico, Enfermero

def recepcionista_required(redirect_url='home'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            try:
                Recepcionista.objects.get(persona=request.user)
            except Recepcionista.DoesNotExist:
                messages.error(request, 'No tienes permisos para acceder a esta página.')
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def medico_required(redirect_url='home'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            try:
                Medico.objects.get(persona=request.user)
            except Medico.DoesNotExist:
                messages.error(request, 'No tienes permisos para acceder a esta página.')
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def enfermero_required(redirect_url='home'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            try:
                Enfermero.objects.get(persona=request.user)
            except Enfermero.DoesNotExist:
                messages.error(request, 'No tienes permisos para acceder a esta página.')
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def admin_required(redirect_url='home'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_staff:
                messages.error(request, 'No tienes permisos para acceder a esta página.')
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator