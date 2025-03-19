from django.shortcuts import render,redirect,get_object_or_404
from pacientes.models import Paciente
from .forms import PacienteForm
from internacion.models import Internacion
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required

@login_required
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


@login_required
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

@login_required
def eliminar_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, idpaciente=paciente_id)
    paciente.delete()
    messages.success(request, '¡Paciente eliminado exitosamente!')
    return redirect('listar_pacientes')


@login_required
def asignar_paciente_cama(request):
    pacientes = Paciente.objects.all()  # Obtén todos los pacientes del sistema
    return render(request, 'asignar_paciente_cama.html', {'pacientes': pacientes})

@login_required
def listar_pacientes(request):
    query = request.GET.get('q', '')
    
    pacientes_list = Paciente.objects.all().order_by('apellido')
    
    if query:
        pacientes_list = pacientes_list.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(dni__icontains=query) |
            Q(telefono__icontains=query)
        )
    
    paginator = Paginator(pacientes_list, 10)
    page_number = request.GET.get('page')
    pacientes = paginator.get_page(page_number)
    
    return render(request, 'listar_pacientes.html', {
        'pacientes': pacientes,
        'request': request  # Para acceder a los parámetros GET en la plantilla
    })

@login_required
def listar_internaciones_historicas(request, paciente_id):
    paciente = get_object_or_404(Paciente, idpaciente=paciente_id)
    internaciones = Internacion.objects.filter(idpaciente=paciente)
    return render(request, 'listar_internaciones_historicas.html', {
        'paciente': paciente,
        'internaciones': internaciones,
    })


@login_required
def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, idpaciente=paciente_id)
    return render(request, 'detalle_paciente.html', {'paciente': paciente})

