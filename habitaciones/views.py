from django.db import models
from django.shortcuts import redirect, render, get_object_or_404
from .models import Habitacion,Cama,Sector,Cama, Medico, Reserva
from internacion.models import Internacion
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Count, Q, F, ExpressionWrapper, fields, Avg, DurationField
import matplotlib.pyplot as plt
import io
import base64
from django.db.models.functions import TruncDay
from django.utils import timezone
import json
from datetime import timedelta
from personal.decoradores_permisos import enfermero_or_staff_required, recepcionista_or_staff_required, enfermero_or_recepcionista_required_or_staff_required
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.http import HttpRequest, HttpResponse
import matplotlib
matplotlib.use('Agg')  # Configuración para evitar problemas con hilos
from typing import Dict, Any, List, Optional
import random



@login_required
def lista_habitaciones(request):
    # Parámetros de filtrado
    selected_sectors = request.GET.getlist('sector')
    available_beds = 'available_beds' in request.GET
    
    # Convertir a enteros solo si hay valores válidos
    selected_sectors_ids = []
    if selected_sectors:  # Verifica si hay valores en selected_sectors
        selected_sectors_ids = [int(s_id) for s_id in selected_sectors if s_id.isdigit()]
    
    # Configurar prefetch con filtros
    camas_filter = Cama.objects.filter(estado='L') if available_beds else Cama.objects.all()
    habitaciones_prefetch = Prefetch(
        'habitaciones',
        queryset=Habitacion.objects.prefetch_related(
            Prefetch('camas', queryset=camas_filter)
        )
    )
    
    # Obtener sectores con filtros
    sectores = Sector.objects.prefetch_related(habitaciones_prefetch)
    if selected_sectors_ids:  # Aplicar filtro solo si hay IDs válidos
        sectores = sectores.filter(idsector__in=selected_sectors_ids)
    
    # Mapa de pacientes
    cama_paciente_map = {}
    internaciones = Internacion.objects.filter(fecha_alta__isnull=True).select_related('idpaciente', 'cama')
    for internacion in internaciones:
        cama_paciente_map[internacion.cama.idcama] = f"{internacion.idpaciente.nombre} {internacion.idpaciente.apellido}"

    context = {
        'sectores': sectores,
        'all_sectors': Sector.objects.all(),
        'selected_sectors': selected_sectors_ids,
        'available_beds': available_beds,
        'cama_paciente_map': cama_paciente_map,
    }
    return render(request, 'lista_habitaciones.html', context)

@login_required
@enfermero_or_staff_required(redirect_url='lista_habitaciones')
def liberar_cama(request, idcama):
    cama = get_object_or_404(Cama, idcama=idcama)
    if request.method == 'POST':
        internacion = cama.internacion_set.last()
        if internacion:
            cama.liberar()
            return redirect('generar_informe_alta', internacion_id=internacion.idinternacion)

        cama.liberar()
        return redirect('lista_habitaciones')  # Redirige si no hay internación
    return redirect('lista_habitaciones')

@login_required
@enfermero_or_recepcionista_required_or_staff_required(redirect_url='lista_habitaciones')
def liberar_cama_reservada(request, idcama):
    cama = get_object_or_404(Cama, idcama=idcama)
    if request.method == 'POST':
        cama.liberar()  # Solo libera la cama sin generar el informe
        return redirect('lista_habitaciones')  # Redirige a la lista de habitaciones
    return redirect('lista_habitaciones')

from django.utils import timezone
from datetime import timedelta

@login_required
@recepcionista_or_staff_required(redirect_url='lista_habitaciones')
def reservar_cama(request, idcama):
    cama = get_object_or_404(Cama, idcama=idcama)
    medicos = Medico.objects.all()
    
    if request.method == 'POST':
        medico_id = request.POST.get('medico_id')
        medico = get_object_or_404(Medico, persona_id=medico_id)
        dias_expiracion = int(request.POST.get('dias_expiracion', 7))  # Por defecto 7 días
        fecha_expiracion = timezone.now() + timedelta(days=dias_expiracion)
        
        # Eliminar cualquier reserva existente para esta cama
        Reserva.objects.filter(cama=cama).delete()
        
        # Crear una nueva reserva
        reserva = Reserva.objects.create(cama=cama, medico=medico, fecha_expiracion=fecha_expiracion)
        cama.estado = 'R'  # Suponiendo que 'R' es el estado para 'Reservada'
        cama.save()
        return redirect('lista_habitaciones')  # Redirigir a la lista de habitaciones después de reservar
    
    return render(request, 'reservar_cama.html', {'cama': cama, 'medicos': medicos})

@login_required
@recepcionista_or_staff_required(redirect_url='lista_habitaciones')
def ver_reserva(request, idcama):
    cama = get_object_or_404(Cama, idcama=idcama)
    reservas = Reserva.objects.filter(cama=cama).order_by('-fecha_reserva')
    reserva = reservas.first()  # Obtener la reserva más reciente
    return render(request, 'ver_reserva.html', {'cama': cama, 'reserva': reserva})

from celery import shared_task
from django.utils import timezone

@shared_task
def liberar_camas_expiradas():
    now = timezone.now()
    reservas_expiradas = Reserva.objects.filter(fecha_expiracion__lt=now)
    for reserva in reservas_expiradas:
        cama = reserva.cama
        cama.estado = 'L'  # Suponiendo que 'L' es el estado para 'Libre'
        cama.save()
        reserva.delete()
        
        


# Constantes para mejor mantenibilidad
MAX_DAYS_TREND = 365
DEFAULT_DAYS_TREND = 7
CACHE_TIMEOUT = 60 * 15  # 15 minutos

@login_required
def generar_grafico_porcentaje_internados() -> Optional[str]:
    """
    Genera un gráfico de porcentaje de ocupación por sector
    Retorna una imagen codificada en base64 o None en caso de error
    """
    try:
        sectores = Sector.objects.prefetch_related('habitaciones__camas').all()
        
        data = []
        labels = []
        colores = []

        for sector in sectores:
            total_camas = sector.total_camas()
            if total_camas == 0:
                continue  # Saltar sectores sin camas
                
            camas_ocupadas = sector.camas_ocupadas()
            porcentaje = (camas_ocupadas / total_camas) * 100
            
            data.append(porcentaje)
            labels.append(sector.tipo)
            colores.append(sector.color_grafico or '#%06x' % random.randint(0, 0xFFFFFF))

        if not data:
            return None

        # Configuración del gráfico
        plt.figure(figsize=(10, 7))
        plt.pie(
            data,
            labels=labels,
            colors=colores,
            autopct=lambda p: f'{p:.1f}%' if p > 0 else '',
            startangle=90,
            wedgeprops={'edgecolor': 'white', 'linewidth': 0.5}
        )
        plt.title('Ocupación por Sector', pad=20)
        plt.tight_layout()

        # Generar imagen
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        plt.close()
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
        
    except Exception as e:
        # Loggear error aquí
        return None

@method_decorator(cache_page(CACHE_TIMEOUT), name='dispatch')
@login_required
def reporte_grafico_porcentaje_internados(request: HttpRequest) -> HttpResponse:
    """Vista para mostrar el reporte gráfico de ocupación con caché"""
    graphic = cache.get_or_set(
        'grafico_ocupacion', 
        generar_grafico_porcentaje_internados, 
        CACHE_TIMEOUT
    )
    
    return render(request, 'reportes/ocupacion.html', {
        'graphic': graphic,
        'error': not graphic
    })

# Imports para vistas de creación
from .forms import SectorForm, HabitacionForm, CamaForm
from django.contrib import messages

@login_required
@enfermero_or_staff_required(redirect_url='lista_habitaciones')
def crear_sector(request):
    """
    Vista para crear un nuevo sector hospitalario.
    """
    if request.method == 'POST':
        form = SectorForm(request.POST)
        if form.is_valid():
            sector = form.save()
            messages.success(request, f'El sector {sector.tipo} ha sido creado exitosamente.')
            return redirect('lista_habitaciones')
    else:
        form = SectorForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Nuevo Sector',
        'boton_texto': 'Crear Sector',
        'accion': 'crear'
    }
    return render(request, 'crear_sector.html', context)

@login_required
@enfermero_or_staff_required(redirect_url='lista_habitaciones')
def crear_habitacion(request):
    """
    Vista para crear una nueva habitación y sus camas asociadas.
    """
    if request.method == 'POST':
        form = HabitacionForm(request.POST)
        if form.is_valid():
            # Guardar la habitación
            habitacion = form.save()
            
            # Crear las camas automáticamente
            cantidad_camas = habitacion.cantidad_camas
            for i in range(1, cantidad_camas + 1):
                Cama.objects.create(
                    habitacion=habitacion,
                    estado='L',  # Libre por defecto
                    nro_cama=i
                )
            
            messages.success(request, f'La habitación {habitacion.numero} ha sido creada exitosamente con {cantidad_camas} camas.')
            return redirect('lista_habitaciones')
    else:
        form = HabitacionForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Nueva Habitación',
        'boton_texto': 'Crear Habitación',
        'accion': 'crear'
    }
    return render(request, 'crear_habitacion.html', context)

@login_required
@enfermero_or_staff_required(redirect_url='lista_habitaciones')
def crear_cama(request):
    """
    Vista para crear una nueva cama.
    """
    if request.method == 'POST':
        form = CamaForm(request.POST)
        if form.is_valid():
            cama = form.save()
            messages.success(request, f'La cama {cama.nro_cama} ha sido creada exitosamente.')
            return redirect('lista_habitaciones')
    else:
        form = CamaForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Nueva Cama',
        'boton_texto': 'Crear Cama',
        'accion': 'crear'
    }
    return render(request, 'crear_cama.html', context)