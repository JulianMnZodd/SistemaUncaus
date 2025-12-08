from django.db import models
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
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
    bed_status = request.GET.get('bed_status', '')  # Filtro por estado específico
    search_patient = request.GET.get('search_patient', '').strip()  # Búsqueda de paciente
    
    # Convertir a enteros solo si hay valores válidos
    selected_sectors_ids = []
    if selected_sectors:
        selected_sectors_ids = [int(s_id) for s_id in selected_sectors if s_id.isdigit()]
    
    # Prefetch de internaciones activas para las camas (SIEMPRE se aplica)
    internaciones_activas_prefetch = Prefetch(
        'internacion_set',
        queryset=Internacion.objects.filter(fecha_alta__isnull=True).select_related('idpaciente'),
        to_attr='internaciones_activas'
    )
    
    # Configurar queryset base de camas
    camas_queryset = Cama.objects.all()
    
    # Aplicar filtros de estado
    if available_beds:
        camas_queryset = camas_queryset.filter(estado='L')
    elif bed_status:  # Filtro por estado específico
        camas_queryset = camas_queryset.filter(estado=bed_status)
    
    # Filtro por búsqueda de paciente
    camas_con_paciente = None
    if search_patient:
        # Buscar internaciones que coincidan con el nombre del paciente
        internaciones_encontradas = Internacion.objects.filter(
            fecha_alta__isnull=True
        ).filter(
            Q(idpaciente__nombre__icontains=search_patient) |
            Q(idpaciente__apellido__icontains=search_patient) |
            Q(idpaciente__dni__icontains=search_patient)
        ).select_related('cama')
        
        # Obtener IDs de camas que tienen esos pacientes
        camas_con_paciente = [int.cama.idcama for int in internaciones_encontradas]
        
        if camas_con_paciente:
            camas_queryset = camas_queryset.filter(idcama__in=camas_con_paciente)
        else:
            # Si no se encuentra ningún paciente, mostrar conjunto vacío
            camas_queryset = camas_queryset.none()
    
    # Aplicar prefetch de internaciones
    camas_queryset = camas_queryset.prefetch_related(internaciones_activas_prefetch)
    
    habitaciones_prefetch = Prefetch(
        'habitaciones',
        queryset=Habitacion.objects.prefetch_related(
            Prefetch('camas', queryset=camas_queryset)
        )
    )
    
    # Obtener sectores con filtros
    sectores = Sector.objects.prefetch_related(habitaciones_prefetch)
    if selected_sectors_ids:
        sectores = sectores.filter(idsector__in=selected_sectors_ids)
    
    # Mapa de pacientes para búsqueda rápida
    cama_paciente_map = {}
    internaciones = Internacion.objects.filter(fecha_alta__isnull=True).select_related('idpaciente', 'cama')
    for internacion in internaciones:
        cama_paciente_map[internacion.cama.idcama] = f"{internacion.idpaciente.nombre} {internacion.idpaciente.apellido}"

    context = {
        'sectores': sectores,
        'all_sectors': Sector.objects.all(),
        'selected_sectors': selected_sectors_ids,
        'available_beds': available_beds,
        'bed_status': bed_status,
        'search_patient': search_patient,
        'cama_paciente_map': cama_paciente_map,
        'camas_encontradas': camas_con_paciente if search_patient else None,
    }
    return render(request, 'lista_habitaciones.html', context)

@login_required
@enfermero_or_staff_required(redirect_url='lista_habitaciones')
def liberar_cama(request, idcama):
    cama = get_object_or_404(Cama, idcama=idcama)
    if request.method == 'POST':
        # Obtener la internación activa (sin fecha de alta) ANTES de liberar
        internacion = Internacion.objects.filter(cama=cama, fecha_alta__isnull=True).first()
        
        # Liberar la cama (esto marca la fecha de alta en la internación)
        cama.liberar()
        
        # Si había una internación activa, generar el PDF directamente
        if internacion:
            # Importar la función de generación de PDF
            from internacion.views import generar_informe_alta
            return generar_informe_alta(request, internacion.idinternacion)
        
        # Si no había internación, redirigir a la lista
        return redirect('lista_habitaciones')
    return redirect('lista_habitaciones')

@login_required
@enfermero_or_recepcionista_required_or_staff_required(redirect_url='lista_habitaciones')
def liberar_cama_reservada(request, idcama):
    cama = get_object_or_404(Cama, idcama=idcama)
    if request.method == 'POST':
        # Eliminar las reservas asociadas
        Reserva.objects.filter(cama=cama).delete()
        cama.estado = 'L'
        cama.save()
        messages.success(request, f'Cama {cama.nro_cama} liberada exitosamente')
        return redirect('lista_habitaciones')
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
            labels.append(sector.nombre)
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
            messages.success(request, f'El sector {sector.nombre} ha sido creado exitosamente.')
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

# ========================
# VISTAS ABM DE SECTORES
# ========================

@login_required
@enfermero_or_staff_required(redirect_url='lista_habitaciones')
def listar_sectores(request):
    """Vista para listar todos los sectores con sus habitaciones"""
    sectores = Sector.objects.prefetch_related('habitaciones').annotate(
        total_habitaciones=Count('habitaciones')
    ).order_by('piso', 'nombre')
    
    context = {
        'sectores': sectores,
        'titulo': 'Gestión de Sectores'
    }
    return render(request, 'listar_sectores.html', context)

@login_required
@enfermero_or_staff_required(redirect_url='lista_habitaciones')
def editar_sector(request, idsector):
    """Vista para editar un sector existente"""
    sector = get_object_or_404(Sector, idsector=idsector)
    
    if request.method == 'POST':
        form = SectorForm(request.POST, instance=sector)
        if form.is_valid():
            sector_editado = form.save()
            messages.success(request, f'El sector {sector_editado.nombre} ha sido actualizado exitosamente.')
            return redirect('listar_sectores')
    else:
        form = SectorForm(instance=sector)
    
    context = {
        'form': form,
        'titulo': 'Editar Sector',
        'boton_texto': 'Guardar Cambios',
        'accion': 'editar',
        'sector': sector
    }
    return render(request, 'crear_sector.html', context)

@login_required
@enfermero_or_staff_required(redirect_url='lista_habitaciones')
def eliminar_sector(request, idsector):
    """Vista para eliminar un sector"""
    sector = get_object_or_404(Sector, idsector=idsector)
    
    if request.method == 'POST':
        # Verificar si tiene habitaciones antes de eliminar
        if sector.habitaciones.exists():
            messages.error(request, f'No se puede eliminar el sector {sector.nombre} porque tiene habitaciones asociadas.')
        else:
            nombre_sector = sector.nombre
            sector.delete()
            messages.success(request, f'El sector {nombre_sector} ha sido eliminado exitosamente.')
        return redirect('listar_sectores')
    
    context = {
        'sector': sector,
        'titulo': 'Confirmar Eliminación de Sector'
    }
    return render(request, 'confirmar_eliminar_sector.html', context)

# ===========================
# VISTAS ABM DE HABITACIONES
# ===========================

@login_required
@enfermero_or_staff_required(redirect_url='lista_habitaciones')
def listar_habitaciones_admin(request):
    """Vista administrativa para listar todas las habitaciones con opciones de edición"""
    # Filtros opcionales
    sector_id = request.GET.get('sector')
    tipo = request.GET.get('tipo')
    
    habitaciones = Habitacion.objects.select_related('idsector').prefetch_related('camas').annotate(
        total_camas=Count('camas'),
        camas_ocupadas=Count('camas', filter=Q(camas__estado='O')),
        camas_libres=Count('camas', filter=Q(camas__estado='L')),
        camas_reservadas=Count('camas', filter=Q(camas__estado='R'))
    )
    
    if sector_id:
        habitaciones = habitaciones.filter(idsector_id=sector_id)
    if tipo:
        habitaciones = habitaciones.filter(tipo=tipo)
    
    habitaciones = habitaciones.order_by('idsector__piso', 'numero')
    
    context = {
        'habitaciones': habitaciones,
        'sectores': Sector.objects.all().order_by('piso', 'nombre'),
        'tipos_habitacion': Habitacion.TIPOS_HABITACION,
        'sector_filtrado': sector_id,
        'tipo_filtrado': tipo,
        'titulo': 'Gestión de Habitaciones'
    }
    return render(request, 'listar_habitaciones_admin.html', context)

@login_required
@enfermero_or_staff_required(redirect_url='lista_habitaciones')
def editar_habitacion(request, idhabitacion):
    """Vista para editar una habitación existente"""
    habitacion = get_object_or_404(Habitacion, idhabitacion=idhabitacion)
    cantidad_camas_original = habitacion.cantidad_camas
    
    if request.method == 'POST':
        form = HabitacionForm(request.POST, instance=habitacion)
        if form.is_valid():
            habitacion_editada = form.save()
            nueva_cantidad = habitacion_editada.cantidad_camas
            
            # Ajustar camas si cambió la cantidad
            camas_actuales = habitacion_editada.camas.count()
            
            if nueva_cantidad > camas_actuales:
                # Crear camas adicionales
                ultimo_nro = habitacion_editada.camas.order_by('-nro_cama').first()
                nro_inicial = ultimo_nro.nro_cama + 1 if ultimo_nro else 1
                
                for i in range(nueva_cantidad - camas_actuales):
                    Cama.objects.create(
                        habitacion=habitacion_editada,
                        estado='L',
                        nro_cama=nro_inicial + i
                    )
                messages.success(request, f'Se agregaron {nueva_cantidad - camas_actuales} camas nuevas.')
            
            elif nueva_cantidad < camas_actuales:
                # Verificar que no haya camas ocupadas antes de eliminar
                camas_a_eliminar = habitacion_editada.camas.order_by('-nro_cama')[:(camas_actuales - nueva_cantidad)]
                camas_ocupadas = [c for c in camas_a_eliminar if c.estado != 'L']
                
                if camas_ocupadas:
                    messages.error(request, 'No se puede reducir la cantidad de camas porque algunas están ocupadas o reservadas.')
                    return redirect('editar_habitacion', idhabitacion=habitacion.idhabitacion)
                else:
                    for cama in camas_a_eliminar:
                        cama.delete()
                    messages.success(request, f'Se eliminaron {camas_actuales - nueva_cantidad} camas.')
            
            messages.success(request, f'La habitación {habitacion_editada.numero} ha sido actualizada exitosamente.')
            return redirect('listar_habitaciones_admin')
    else:
        form = HabitacionForm(instance=habitacion)
    
    context = {
        'form': form,
        'titulo': 'Editar Habitación',
        'boton_texto': 'Guardar Cambios',
        'accion': 'editar',
        'habitacion': habitacion
    }
    return render(request, 'crear_habitacion.html', context)

@login_required
@enfermero_or_staff_required(redirect_url='lista_habitaciones')
def eliminar_habitacion(request, idhabitacion):
    """Vista para eliminar una habitación"""
    habitacion = get_object_or_404(Habitacion, idhabitacion=idhabitacion)
    
    if request.method == 'POST':
        # Verificar si tiene camas ocupadas
        camas_ocupadas = habitacion.camas.filter(estado__in=['O', 'R']).exists()
        
        if camas_ocupadas:
            messages.error(request, f'No se puede eliminar la habitación {habitacion.numero} porque tiene camas ocupadas o reservadas.')
        else:
            numero_habitacion = habitacion.numero
            habitacion.delete()  # Esto también elimina las camas por CASCADE
            messages.success(request, f'La habitación {numero_habitacion} y sus camas han sido eliminadas exitosamente.')
        
        return redirect('listar_habitaciones_admin')
    
    context = {
        'habitacion': habitacion,
        'titulo': 'Confirmar Eliminación de Habitación'
    }
    return render(request, 'confirmar_eliminar_habitacion.html', context)