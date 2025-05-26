from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .models import Recepcionista, Medico, Enfermero

def medico_or_enfermero_or_staff_required(redirect_url='home'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not (
                request.user.is_staff
                or request.user.medico_set.exists()
                or request.user.enfermero_set.exists()
            ):
                messages.error(request, 'No tienes permisos para acceder a esta página.')
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def medico_or_staff_required(redirect_url='home'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not (
                request.user.is_staff
                or request.user.medico_set.exists()
            ):
                messages.error(request, 'No tienes permisos para acceder a esta página.')
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def enfermero_or_staff_required(redirect_url='home'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not (
                request.user.is_staff
                or request.user.enfermero_set.exists()
            ):
                messages.error(request, 'No tienes permisos para acceder a esta página.')
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def recepcionista_or_staff_required(redirect_url='home'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not (
                request.user.is_staff
                or request.user.recepcionista_set.exists()
            ):
                messages.error(request, 'No tienes permisos para acceder a esta página.')
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def staff_required(redirect_url='home'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_staff:
                messages.error(request, 'No tienes permisos para acceder a esta página.')
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def enfermero_or_recepcionista_required_or_staff_required(redirect_url='home'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not (
                request.user.is_staff
                or request.user.enfermero_set.exists()
                or request.user.recepcionista_set.exists()
            ):
                messages.error(request, 'No tienes permisos para acceder a esta página.')
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator