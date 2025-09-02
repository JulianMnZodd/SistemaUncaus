from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from .models import Persona, Medico, Enfermero, Recepcionista
from .profile_forms import UserProfileForm, PasswordChangeForm

@login_required
def user_profile(request):
    """
    Vista para mostrar el perfil del usuario actual.
    """
    user = request.user
    
    # Determinar el rol del usuario
    user_role = None
    role_info = None
    
    # Verificar si el usuario es médico
    try:
        medico = Medico.objects.get(persona=user)
        user_role = "Médico"
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
        'role_info': role_info
    }
    
    return render(request, 'profile/user_profile.html', context)

@login_required
def edit_profile(request):
    """
    Vista para editar el perfil del usuario actual.
    """
    user = request.user
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil ha sido actualizado exitosamente.')
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=user)
    
    context = {
        'form': form
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
