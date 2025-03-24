from django.http import HttpResponse, JsonResponse
from django.db import models
from django.shortcuts import redirect, render, get_object_or_404
from .models import Habitacion,Cama,Sector
from .models import Cama, Medico, Reserva
from internacion.models import Internacion
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch

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
def liberar_cama(request, idcama):
    cama = get_object_or_404(Cama, idcama=idcama)
    if request.method == 'POST':
        cama.liberar()
        return redirect('lista_habitaciones')  # Redirige a la lista de internaciones o a otra vista relevante
    return redirect('lista_habitaciones')

from django.utils import timezone
from datetime import timedelta

@login_required
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
        
        
        
import matplotlib.pyplot as plt
import io
import base64
from django.shortcuts import render
from .models import Sector
from internacion.models import Internacion
from datetime import datetime, timedelta

@login_required
def generar_grafico_porcentaje_internados():
    # Obtener los datos de internaciones por sector
    sectores = Sector.objects.all()
    data = []
    labels = []

    for sector in sectores:
        total_camas = sector.habitaciones.aggregate(total_camas=models.Count('camas'))['total_camas']
        camas_ocupadas = sector.habitaciones.filter(camas__estado='O').count()
        porcentaje_ocupacion = (camas_ocupadas / total_camas) * 100 if total_camas > 0 else 0
        data.append(porcentaje_ocupacion)
        labels.append(sector.tipo)

    # Crear el gráfico
    fig, ax = plt.subplots()
    ax.pie(data, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Para asegurar que el gráfico sea un círculo

    # Guardar el gráfico en un buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    # Codificar la imagen en base64
    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')

    return graphic

@login_required
def reporte_grafico_porcentaje_internados(request):
    graphic = generar_grafico_porcentaje_internados()
    context = {
        'graphic': graphic,
    }
    return render(request, 'reporte_grafico_porcentaje_internados.html', context)
        