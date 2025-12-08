from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from .models import Persona, Medico, Enfermero, Recepcionista
from .profile_forms import (UserProfileForm, PasswordChangeForm, 
                            MedicoProfileForm, EnfermeroProfileForm, 
                            RecepcionistaProfileForm)

@login_required
def user_profile(request):
    """
    Vista para mostrar el perfil del usuario actual.
    """
    user = request.user
    
    # Determinar el rol del usuario
    user_role = None
    role_info = None
    role_instance = None
    
    # Verificar si el usuario es médico
    try:
        medico = Medico.objects.get(persona=user)
        user_role = "Médico"
        role_instance = medico
        role_info = {
            'especializacion': medico.especializacion,
            'matricula': medico.matricula
        }
    except Medico.DoesNotExist:
        pass
    
    # Verificar si el usuario es enfermero
    if not user_role:
        try:
            enfermero = Enfermero.objects.get(persona=user)
            user_role = "Enfermero"
            role_instance = enfermero
            role_info = {
                'matricula': enfermero.matricula
            }
        except Enfermero.DoesNotExist:
            pass
    
    # Verificar si el usuario es recepcionista
    if not user_role:
        try:
            recepcionista = Recepcionista.objects.get(persona=user)
            user_role = "Recepcionista"
            role_instance = recepcionista
            role_info = {
                'turno': recepcionista.get_turno_display() if recepcionista.turno else "No especificado"
            }
        except Recepcionista.DoesNotExist:
            pass
            
    # Si no tiene ningún rol específico pero es staff
    if not user_role and user.is_staff:
        user_role = "Administrador"
    
    # Si aún no tiene rol, asignar "Usuario"
    if not user_role:
        user_role = "Usuario"
    
    context = {
        'user': user,
        'user_role': user_role,
        'role_info': role_info,
        'role_instance': role_instance
    }
    
    return render(request, 'profile/user_profile.html', context)

@login_required
def edit_profile(request):
    """
    Vista para editar el perfil del usuario actual.
    Incluye datos de Persona y datos específicos del rol.
    """
    user = request.user
    
    # Determinar el rol del usuario y obtener la instancia
    role_instance = None
    role_form = None
    role_type = None
    
    try:
        medico = Medico.objects.get(persona=user)
        role_instance = medico
        role_type = 'medico'
    except Medico.DoesNotExist:
        pass
    
    if not role_instance:
        try:
            enfermero = Enfermero.objects.get(persona=user)
            role_instance = enfermero
            role_type = 'enfermero'
        except Enfermero.DoesNotExist:
            pass
    
    if not role_instance:
        try:
            recepcionista = Recepcionista.objects.get(persona=user)
            role_instance = recepcionista
            role_type = 'recepcionista'
        except Recepcionista.DoesNotExist:
            pass
    
    if request.method == 'POST':
        # Formulario principal de Persona
        form = UserProfileForm(request.POST, instance=user)
        
        # Formulario del rol específico
        if role_type == 'medico':
            role_form = MedicoProfileForm(request.POST, instance=role_instance)
        elif role_type == 'enfermero':
            role_form = EnfermeroProfileForm(request.POST, instance=role_instance)
        elif role_type == 'recepcionista':
            role_form = RecepcionistaProfileForm(request.POST, instance=role_instance)
        
        # Validar ambos formularios
        forms_valid = form.is_valid()
        if role_form:
            forms_valid = forms_valid and role_form.is_valid()
        
        if forms_valid:
            form.save()
            if role_form:
                role_form.save()
            messages.success(request, 'Tu perfil ha sido actualizado exitosamente.')
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=user)
        
        # Crear el formulario del rol si existe
        if role_type == 'medico':
            role_form = MedicoProfileForm(instance=role_instance)
        elif role_type == 'enfermero':
            role_form = EnfermeroProfileForm(instance=role_instance)
        elif role_type == 'recepcionista':
            role_form = RecepcionistaProfileForm(instance=role_instance)
    
    context = {
        'form': form,
        'role_form': role_form,
        'role_type': role_type
    }
    
    return render(request, 'profile/edit_profile.html', context)

@login_required
def change_password(request):
    """
    Vista para cambiar la contraseña del usuario actual.
    """
    user = request.user
    
    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            # Cambiar la contraseña
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            
            # Actualizar la sesión para que el usuario no sea desconectado
            update_session_auth_hash(request, user)
            
            messages.success(request, 'Tu contraseña ha sido cambiada exitosamente.')
            return redirect('user_profile')
    else:
        form = PasswordChangeForm(user)
    
    context = {
        'form': form
    }
    
    return render(request, 'profile/change_password.html', context)
