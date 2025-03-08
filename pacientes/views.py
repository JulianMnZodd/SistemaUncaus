from django.shortcuts import render,redirect,get_object_or_404
from pacientes.models import Paciente
from .forms import PacienteForm
from internacion.models import Internacion
from django.contrib import messages

def crear_paciente(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Paciente creado exitosamente!')
            return redirect('listar_pacientes')
    else:
        form = PacienteForm()
    return render(request, 'crear_paciente.html', {'form': form})

def editar_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, idpaciente=paciente_id)
    
    if request.method == 'POST':
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Paciente actualizado exitosamente!')
            return redirect('listar_pacientes')  # Redirige a la lista de pacientes
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = PacienteForm(instance=paciente)
    
    return render(request, 'editar_paciente.html', {'form': form})

def eliminar_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, idpaciente=paciente_id)
    paciente.delete()
    messages.success(request, '¡Paciente eliminado exitosamente!')
    return redirect('listar_pacientes')



def asignar_paciente_cama(request):
    pacientes = Paciente.objects.all()  # Obtén todos los pacientes del sistema
    return render(request, 'asignar_paciente_cama.html', {'pacientes': pacientes})

def listar_pacientes(request):
    pacientes = Paciente.objects.all()  # Obtén todos los pacientes del sistema
    return render(request, 'listar_pacientes.html', {'pacientes': pacientes})

def listar_internaciones_historicas(request, paciente_id):
    paciente = get_object_or_404(Paciente, idpaciente=paciente_id)
    internaciones = Internacion.objects.filter(idpaciente=paciente)
    return render(request, 'listar_internaciones_historicas.html', {
        'paciente': paciente,
        'internaciones': internaciones,
    })



def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, idpaciente=paciente_id)
    return render(request, 'detalle_paciente.html', {'paciente': paciente})

