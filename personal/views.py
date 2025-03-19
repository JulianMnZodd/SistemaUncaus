from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from personal.forms import CustomAuthenticationForm
from .forms import CustomUserCreationForm, MedicoForm, RecepcionistaForm, EnfermeroForm
from personal.models import Medico, Enfermero, Recepcionista

class CustomLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('lista_habitaciones') 

def registro(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario registrado exitosamente.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registro.html', {'form': form})



@login_required
def crear_medico(request):
    if request.method == 'POST':
        # Crear ambos formularios
        persona_form = CustomUserCreationForm(request.POST)
        medico_form = MedicoForm(request.POST)

        if persona_form.is_valid() and medico_form.is_valid():
            # Guardar la persona primero
            persona = persona_form.save()

            # Crear el médico y asociarlo con la persona
            medico = medico_form.save(commit=False)
            medico.persona = persona  # Relacionar el médico con la persona
            medico.save()

            messages.success(request, '¡Médico creado exitosamente!')
            return redirect('crear_medico')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        persona_form = CustomUserCreationForm()
        medico_form = MedicoForm()

    return render(request, 'crear_medico.html', {
        'persona_form': persona_form,
        'medico_form': medico_form,
    })
    
def editar_medico(request, medico_id):
    medico = get_object_or_404(Medico, persona_id=medico_id)
    
    if request.method == 'POST':
        persona_form =  CustomUserCreationForm(request.POST, instance=medico.persona)
        medico_form = MedicoForm(request.POST, instance=medico)
        if persona_form.is_valid() and medico_form.is_valid():
            persona_form.save()
            medico_form.save()
            messages.success(request, '¡Médico actualizado exitosamente!')
            return redirect('listar_medicos')  # Redirige a la lista de médicos
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        persona_form =  CustomUserCreationForm(instance=medico.persona)
        medico_form = MedicoForm(instance=medico)
    
    return render(request, 'editar_medico.html', {
        'persona_form': persona_form,
        'medico_form': medico_form,
    })


@login_required
def crear_enfermero(request):
    if request.method == 'POST':
        # Crear ambos formularios
        persona_form = CustomUserCreationForm(request.POST)
        enfermero_form = EnfermeroForm(request.POST)

        if persona_form.is_valid() and enfermero_form.is_valid():
            # Guardar la persona primero
            persona = persona_form.save()

            # Crear el enfermero y asociarlo con la persona
            enfermero = enfermero_form.save(commit=False)
            enfermero.persona = persona  # Relacionar el enfermero con la persona
            enfermero.save()

            messages.success(request, '¡Enfermero creado exitosamente!')
            return redirect('crear_enfermero')
    else:
        persona_form = CustomUserCreationForm()
        enfermero_form = EnfermeroForm()

    return render(request, 'crear_enfermero.html', {
        'persona_form': persona_form,
        'enfermero_form': enfermero_form,
    })
    

@login_required
def editar_enfermero(request, id_enfermero):
    enfermero = get_object_or_404(Enfermero, persona_id=id_enfermero)
    
    if request.method == 'POST':
        persona_form = CustomUserCreationForm(request.POST, instance=enfermero.persona)
        enfermero_form = EnfermeroForm(request.POST, instance=enfermero)
        if persona_form.is_valid() and enfermero_form.is_valid():
            persona_form.save()
            enfermero_form.save()
            messages.success(request, '¡Enfermero actualizado exitosamente!')
            return redirect('listar_enfermeros')  # Redirige a la lista de enfermeros
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        persona_form = CustomUserCreationForm(instance=enfermero.persona)
        enfermero_form = EnfermeroForm(instance=enfermero)
    
    return render(request, 'editar_enfermero.html', {
        'persona_form': persona_form,
        'enfermero_form': enfermero_form,
    })


@login_required
def crear_recepcionista(request):
    if request.method == 'POST':
        # Crear ambos formularios
        persona_form = CustomUserCreationForm(request.POST)
        recepcionista_form = RecepcionistaForm(request.POST)

        if persona_form.is_valid() and recepcionista_form.is_valid():
            # Guardar la persona primero
            persona = persona_form.save()

            # Crear el recepcionista y asociarlo con la persona
            recepcionista = recepcionista_form.save(commit=False)
            recepcionista.persona = persona  # Relacionar el recepcionista con la persona
            recepcionista.save()

            messages.success(request, '¡Recepcionista creado exitosamente!')
            return redirect('listar_recepcionistas')
    else:
        persona_form = CustomUserCreationForm()
        recepcionista_form = RecepcionistaForm()

    return render(request, 'crear_recepcionista.html', {
        'persona_form': persona_form,
        'recepcionista_form': recepcionista_form,
    })
    
    
@login_required
def listar_medicos(request):
    medicos = Medico.objects.all()
    return render(request, 'listar_medicos.html', {'medicos': medicos})


@login_required
def eliminar_medico(request, id_medico):
    medico = get_object_or_404(Medico, persona_id=id_medico)
    medico.delete()
    messages.success(request, '¡Médico eliminado exitosamente!')
    return redirect('listar_medicos')


@login_required
def listar_enfermeros(request):
    enfermeros = Enfermero.objects.all()
    return render(request, 'listar_enfermeros.html', {'enfermeros': enfermeros})

@login_required
def eliminar_enfermero(request, id_enfermero):
    enfermero = get_object_or_404(Enfermero, persona_id=id_enfermero)
    enfermero.delete()
    messages.success(request, '¡Enfermero eliminado exitosamente!')
    return redirect('listar_enfermeros')

@login_required
def listar_recepcionistas(request):
    recepcionistas = Recepcionista.objects.all()
    return render(request, 'listar_recepcionistas.html', {'recepcionistas': recepcionistas})


@login_required
def editar_recepcionista(request, recepcionista_id):
    recepcionista = get_object_or_404(Recepcionista, persona_id=recepcionista_id)
    
    if request.method == 'POST':
        persona_form = CustomUserCreationForm(request.POST, instance=recepcionista.persona)
        recepcionista_form = RecepcionistaForm(request.POST, instance=recepcionista)
        if persona_form.is_valid() and recepcionista_form.is_valid():
            persona_form.save()
            recepcionista_form.save()
            messages.success(request, '¡Recepcionista actualizado exitosamente!')
            return redirect('listar_recepcionistas')  # Redirige a la lista de recepcionistas
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        persona_form = CustomUserCreationForm(instance=recepcionista.persona)
        recepcionista_form = RecepcionistaForm(instance=recepcionista)
    
    return render(request, 'editar_recepcionista.html', {
        'persona_form': persona_form,
        'recepcionista_form': recepcionista_form,
    })

@login_required
def eliminar_recepcionista(request, id_recepcionista):
    recepcionista = get_object_or_404(Recepcionista, persona_id=id_recepcionista)
    recepcionista.delete()
    messages.success(request, '¡Recepcionista eliminado exitosamente!')
    return redirect('listar_recepcionistas')
