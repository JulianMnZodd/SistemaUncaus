from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.db import models
from django.db.models import Count, Q, F, ExpressionWrapper, fields, Avg, DurationField
from django.db.models.functions import TruncDay
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta
import json
from typing import Dict, Any, List, Optional
import random

from .models import Habitacion, Cama, Sector, Reserva
from internacion.models import Internacion

# Constantes
DEFAULT_DAYS_TREND = 30
MAX_DAYS_TREND = 365

@login_required
def estadisticas_camas(request: HttpRequest) -> HttpResponse:
    """Vista de estadísticas de camas con parámetros configurables y métricas avanzadas"""
    
    def get_days_param() -> int:
        """Obtiene y valida el parámetro de días desde la URL"""
        try:
            days = int(request.GET.get('days', DEFAULT_DAYS_TREND))
            return max(1, min(days, MAX_DAYS_TREND))
        except (ValueError, TypeError):
            return DEFAULT_DAYS_TREND

    def calcular_duracion_promedio() -> str:
        """Calcula y formatea la duración promedio de internaciones"""
        promedio = Internacion.objects.exclude(
            fecha_alta__isnull=True
        ).annotate(
            duracion=ExpressionWrapper(
                F('fecha_alta') - F('fecha_admision'),
                output_field=DurationField()
            )
        ).aggregate(
            avg_duracion=Avg('duracion')
        )['avg_duracion'] or timedelta(0)

        total_seconds = promedio.total_seconds()
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes = remainder // 60
        
        return f"{int(days)}d {int(hours)}h {int(minutes)}m"

    def calcular_metricas_avanzadas(days: int, start_date, now):
        """Calcula métricas avanzadas del hospital"""
        # Tasa de rotación de camas (pacientes por cama por período)
        total_internaciones = Internacion.objects.filter(
            fecha_admision__gte=start_date
        ).count()
        total_camas = Cama.objects.count()
        tasa_rotacion = round(total_internaciones / total_camas, 2) if total_camas > 0 else 0
        
        # Tiempo promedio desde reserva hasta ingreso
        reservas_con_internacion = Reserva.objects.filter(
            fecha_reserva__gte=start_date
        ).prefetch_related('cama__internacion_set')
        
        tiempo_reserva_ingreso = []
        for reserva in reservas_con_internacion:
            internaciones = reserva.cama.internacion_set.filter(
                fecha_admision__gte=reserva.fecha_reserva
            ).first()
            if internaciones:
                delta = internaciones.fecha_admision - reserva.fecha_reserva
                tiempo_reserva_ingreso.append(delta.total_seconds() / 3600)  # en horas
        
        promedio_reserva_ingreso = (
            sum(tiempo_reserva_ingreso) / len(tiempo_reserva_ingreso) 
            if tiempo_reserva_ingreso else 0
        )
        
        # Capacidad de respuesta (porcentaje de camas ocupadas vs disponibles)
        camas_ocupadas = Cama.objects.filter(estado='O').count()
        capacidad_respuesta = round((camas_ocupadas / total_camas * 100), 1) if total_camas > 0 else 0
        
        # Eficiencia operacional (alta rotación + baja duración promedio = mayor eficiencia)
        duracion_promedio_dias = Internacion.objects.exclude(
            fecha_alta__isnull=True
        ).annotate(
            duracion=ExpressionWrapper(
                F('fecha_alta') - F('fecha_admision'),
                output_field=DurationField()
            )
        ).aggregate(avg=Avg('duracion'))['avg']
        
        if duracion_promedio_dias:
            duracion_dias = duracion_promedio_dias.total_seconds() / 86400
            # Fórmula simple: eficiencia = (rotación / duración) * 100
            eficiencia = round((tasa_rotacion / duracion_dias * 100), 1) if duracion_dias > 0 else 0
        else:
            eficiencia = 0
        
        return {
            'tasa_rotacion': tasa_rotacion,
            'promedio_reserva_ingreso': round(promedio_reserva_ingreso, 1),
            'capacidad_respuesta': capacidad_respuesta,
            'eficiencia_operacional': eficiencia
        }

    def generar_alertas_predictivas():
        """Genera alertas predictivas basadas en tendencias - CON ACTUALIZACIÓN EN TIEMPO REAL"""
        alertas = []
        now = timezone.now()  # Siempre usar timestamp actual
        
        # PROBLEMA SOLUCIONADO: Recargar datos desde la BD sin caché
        
        # 1. Alerta de capacidad crítica
        camas_disponibles = Cama.objects.filter(estado='L').count()
        total_camas = Cama.objects.count()
        
        if total_camas > 0:
            porcentaje_disponible = (camas_disponibles / total_camas) * 100
            if porcentaje_disponible < 10:
                alertas.append({
                    'tipo': 'critico',
                    'mensaje': f'🚨 Capacidad crítica: Solo {camas_disponibles} camas disponibles ({porcentaje_disponible:.1f}%)',
                    'icono': 'bi-exclamation-triangle-fill'
                })
            elif porcentaje_disponible < 20:
                alertas.append({
                    'tipo': 'advertencia', 
                    'mensaje': f'⚠️ Capacidad baja: {camas_disponibles} camas disponibles ({porcentaje_disponible:.1f}%)',
                    'icono': 'bi-exclamation-triangle'
                })
        
        # 2. Reservas que vencen hoy - SOLO SI HAY CAMAS REALMENTE RESERVADAS
        camas_reservadas_hoy = Reserva.objects.filter(
            fecha_expiracion__date=now.date(),
            cama__estado='R'  # Solo si la cama está realmente reservada
        ).count()
        
        if camas_reservadas_hoy > 0:
            alertas.append({
                'tipo': 'info',
                'mensaje': f'📅 {camas_reservadas_hoy} reserva{"s" if camas_reservadas_hoy != 1 else ""} vence{"n" if camas_reservadas_hoy != 1 else ""} hoy',
                'icono': 'bi-calendar-check'
            })
        
        # 3. Reservas que vencen en las próximas 2 horas - SOLO SI HAY CAMAS REALMENTE RESERVADAS
        limite_proximo = now + timedelta(hours=2)
        camas_reservadas_pronto = Reserva.objects.filter(
            fecha_expiracion__gt=now,
            fecha_expiracion__lte=limite_proximo,
            cama__estado='R'  # Solo si la cama está realmente reservada
        ).count()
        
        if camas_reservadas_pronto > 0:
            alertas.append({
                'tipo': 'advertencia',
                'mensaje': f'⏰ {camas_reservadas_pronto} reserva{"s" if camas_reservadas_pronto != 1 else ""} vence{"n" if camas_reservadas_pronto != 1 else ""} en las próximas 2 horas',
                'icono': 'bi-clock'
            })
        
        # 4. Reservas vencidas - SOLO SI LA CAMA SIGUE MARCADA COMO RESERVADA
        reservas_vencidas = Reserva.objects.filter(
            fecha_expiracion__lt=now,
            cama__estado='R'  # Solo si la cama aún está marcada como reservada
        ).count()
        
        if reservas_vencidas > 0:
            alertas.append({
                'tipo': 'critico',
                'mensaje': f'🔴 {reservas_vencidas} reserva{"s" if reservas_vencidas != 1 else ""} vencida{"s" if reservas_vencidas != 1 else ""} - Requieren limpieza',
                'icono': 'bi-exclamation-circle-fill'
            })
        
        # 5. Alta ocupación (más del 85%)
        camas_ocupadas = Cama.objects.filter(estado='O').count()
        if total_camas > 0:
            porcentaje_ocupacion = (camas_ocupadas / total_camas) * 100
            if porcentaje_ocupacion > 85:
                alertas.append({
                    'tipo': 'advertencia',
                    'mensaje': f'📊 Alta ocupación: {porcentaje_ocupacion:.1f}% de camas ocupadas',
                    'icono': 'bi-speedometer2'
                })
        
        reservas_activas = Cama.objects.filter(estado='R').count()
        
        if reservas_activas > camas_disponibles and camas_disponibles > 0:
            alertas.append({
                'tipo': 'info',
                'mensaje': f'⚖️ Hay {reservas_activas} reservas activas para {camas_disponibles} camas disponibles',
                'icono': 'bi-bookmark-check'
            })
        
        return alertas

    # Parámetros y contexto inicial
    days = get_days_param()
    now = timezone.now()
    start_date = now - timedelta(days=days)
    
    # Datos básicos mejorados - SIEMPRE ACTUALIZADOS
    camas_stats = Cama.objects.aggregate(
        total=models.Count('idcama'),
        ocupadas=models.Count('idcama', filter=Q(estado='O')),
        reservadas=models.Count('idcama', filter=Q(estado='R')),
        libres=models.Count('idcama', filter=Q(estado='L'))
    )
    
    # Tendencia temporal con más detalle
    tendencia_data = (
        Internacion.objects
        .filter(fecha_admision__gte=start_date)
        .annotate(fecha=TruncDay('fecha_admision'))
        .values('fecha')
        .annotate(total=Count('idinternacion'))
        .order_by('fecha')
    )
    
    # Datos para gráficos mejorados
    distribucion_sector = (
        Sector.objects
        .prefetch_related('habitaciones__camas')
        .annotate(
            total_camas=Count('habitaciones__camas'),
            ocupadas=Count('habitaciones__camas', filter=Q(habitaciones__camas__estado='O')),
            reservadas=Count('habitaciones__camas', filter=Q(habitaciones__camas__estado='R')),
            disponibles=Count('habitaciones__camas', filter=Q(habitaciones__camas__estado='L'))
        )
        .filter(total_camas__gt=0)  # Solo sectores con camas
    )
    
    # Distribución por tipo de habitación
    tipos_habitacion = (
        Habitacion.objects
        .values('tipo')
        .annotate(
            total=Count('idhabitacion'),
            total_camas=Count('camas'),
            ocupadas=Count('camas', filter=Q(camas__estado='O')),
            disponibles=Count('camas', filter=Q(camas__estado='L'))
        )
        .order_by('-total_camas')
    )
    
    # Análisis de admisiones por día de la semana
    admisiones_por_dia_semana = []
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    for dia in range(7):  # 0=Lunes, 6=Domingo
        count = Internacion.objects.filter(
            fecha_admision__gte=start_date,
            fecha_admision__week_day=(dia + 2) % 7 + 1  # Ajuste para week_day de Django
        ).count()
        admisiones_por_dia_semana.append(count)
    
    # Análisis de admisiones por hora del día
    admisiones_por_hora = []
    for hora in range(24):
        count = Internacion.objects.filter(
            fecha_admision__gte=start_date,
            fecha_admision__hour=hora
        ).count()
        admisiones_por_hora.append(count)
    
    # Métricas avanzadas
    metricas_avanzadas = calcular_metricas_avanzadas(days, start_date, now)
    
    # CLAVE: Alertas predictivas CON datos actualizados
    alertas = generar_alertas_predictivas()
    
    # Comparación con período anterior
    periodo_anterior = now - timedelta(days=days*2)
    internaciones_actual = Internacion.objects.filter(fecha_admision__gte=start_date).count()
    internaciones_anterior = Internacion.objects.filter(
        fecha_admision__gte=periodo_anterior,
        fecha_admision__lt=start_date
    ).count()
    
    variacion_internaciones = internaciones_actual - internaciones_anterior
    porcentaje_variacion = (
        (variacion_internaciones / internaciones_anterior * 100) 
        if internaciones_anterior > 0 else 0
    )

    # DATOS ACTUALIZADOS EN TIEMPO REAL PARA RESERVAS
    # CORRECCIÓN: Las reservas activas son las camas con estado 'R'
    reservas_activas_count = Cama.objects.filter(estado='R').count()
    reservas_vencidas_count = Reserva.objects.filter(fecha_expiracion__lte=now).count()

    context = {
        # Datos básicos - SIEMPRE ACTUALIZADOS
        'total_camas': camas_stats['total'],
        'camas_ocupadas': camas_stats['ocupadas'],
        'camas_reservadas': camas_stats['reservadas'],
        'camas_disponibles': camas_stats['libres'],
        
        # Porcentajes para gráficos de dona
        'porcentaje_ocupadas': round((camas_stats['ocupadas'] / camas_stats['total'] * 100), 1) if camas_stats['total'] > 0 else 0,
        'porcentaje_reservadas': round((camas_stats['reservadas'] / camas_stats['total'] * 100), 1) if camas_stats['total'] > 0 else 0,
        'porcentaje_disponibles': round((camas_stats['libres'] / camas_stats['total'] * 100), 1) if camas_stats['total'] > 0 else 0,
        
        # Tendencias
        'tendencia_labels': json.dumps([d['fecha'].strftime('%d %b') for d in tendencia_data]),
        'tendencia_data': json.dumps([d['total'] for d in tendencia_data]),
        'variacion_internaciones': variacion_internaciones,
        'porcentaje_variacion': round(porcentaje_variacion, 1),
        
        # Distribuciones
        'distribucion_labels': json.dumps([s.nombre for s in distribucion_sector]),
        'distribucion_total': json.dumps([s.total_camas for s in distribucion_sector]),
        'distribucion_ocupadas': json.dumps([s.ocupadas for s in distribucion_sector]),
        'distribucion_reservadas': json.dumps([s.reservadas for s in distribucion_sector]),
        'distribucion_disponibles': json.dumps([s.disponibles for s in distribucion_sector]),
        
        # Tipos de habitación
        'tipos_habitacion_labels': json.dumps([dict(Habitacion.TIPOS_HABITACION).get(t['tipo'], t['tipo']) for t in tipos_habitacion]),
        'tipos_habitacion_data': json.dumps([t['total_camas'] for t in tipos_habitacion]),
        'tipos_habitacion_ocupadas': json.dumps([t['ocupadas'] for t in tipos_habitacion]),
        
        # Análisis temporal
        'dias_semana_labels': json.dumps(dias_semana),
        'dias_semana_data': json.dumps(admisiones_por_dia_semana),
        'horas_labels': json.dumps([f"{h:02d}:00" for h in range(24)]),
        'horas_data': json.dumps(admisiones_por_hora),
        
        # Métricas avanzadas
        'tasa_rotacion': metricas_avanzadas['tasa_rotacion'],
        'promedio_reserva_ingreso': metricas_avanzadas['promedio_reserva_ingreso'],
        'capacidad_respuesta': metricas_avanzadas['capacidad_respuesta'],
        'eficiencia_operacional': metricas_avanzadas['eficiencia_operacional'],
        
        # DATOS DE RESERVAS ACTUALIZADOS
        'duracion_promedio': calcular_duracion_promedio(),
        'reservas_activas': reservas_activas_count,
        'reservas_vencidas': reservas_vencidas_count,
        'total_internaciones_periodo': internaciones_actual,
        
        # Sistema de alertas actualizado
        'alertas': alertas,
        'total_alertas': len(alertas),
        'alertas_criticas': len([a for a in alertas if a['tipo'] == 'critico']),
        
        # Configuración
        'selected_days': days,
        'days_options': [7, 15, 30, 60, 90],
        'last_update': now.strftime('%d/%m/%Y %H:%M:%S')
    }
    
    return render(request, 'estadisticas.html', context)


@login_required
def estadisticas_avanzadas(request: HttpRequest) -> HttpResponse:
    """Vista de estadísticas avanzadas con análisis predictivo y métricas especializadas"""
    
    def calcular_analisis_predictivo():
        """Genera análisis predictivo basado en tendencias históricas"""
        now = timezone.now()
        
        # Análisis de los últimos 30 días para predicción
        datos_historicos = []
        for i in range(30):
            fecha = now - timedelta(days=29-i)
            ocupacion = Internacion.objects.filter(
                fecha_admision__date=fecha.date()
            ).count()
            datos_historicos.append(ocupacion)
        
        # Predicción simple basada en promedio móvil
        if len(datos_historicos) >= 7:
            promedio_semanal = sum(datos_historicos[-7:]) / 7
            prediccion_7_dias = []
            
            for i in range(7):
                # Simulación con algo de variabilidad
                factor_estacional = 1.0
                if i in [5, 6]:  # Fin de semana
                    factor_estacional = 0.8
                elif i in [0, 1]:  # Inicio de semana
                    factor_estacional = 1.2
                
                prediccion = int(promedio_semanal * factor_estacional * random.uniform(0.85, 1.15))
                prediccion_7_dias.append(prediccion)
        else:
            prediccion_7_dias = [0] * 7
        
        return {
            'historicos': datos_historicos,
            'prediccion': prediccion_7_dias,
            'promedio_semanal': round(sum(datos_historicos[-7:]) / 7, 1) if len(datos_historicos) >= 7 else 0
        }
    
    def calcular_metricas_calidad():
        """Calcula métricas de calidad de servicio"""
        now = timezone.now()
        mes_actual = now - timedelta(days=30)
        
        # Tiempo promedio de resolución (desde reserva hasta alta)
        reservas_con_internacion = []
        for reserva in Reserva.objects.filter(fecha_reserva__gte=mes_actual):
            internacion = Internacion.objects.filter(
                cama=reserva.cama,
                fecha_admision__gte=reserva.fecha_reserva
            ).first()
            
            if internacion and internacion.fecha_alta:
                tiempo_total = internacion.fecha_alta - reserva.fecha_reserva
                reservas_con_internacion.append(tiempo_total.total_seconds() / 3600)  # en horas
        
        tiempo_promedio_resolucion = (
            sum(reservas_con_internacion) / len(reservas_con_internacion)
            if reservas_con_internacion else 0
        )
        
        # Tasa de cancelación de reservas
        total_reservas = Reserva.objects.filter(fecha_reserva__gte=mes_actual).count()
        reservas_vencidas = Reserva.objects.filter(
            fecha_reserva__gte=mes_actual,
            fecha_expiracion__lt=now
        ).count()
        
        tasa_cancelacion = (
            (reservas_vencidas / total_reservas * 100) 
            if total_reservas > 0 else 0
        )
        
        # Satisfacción estimada (basada en duración vs promedio)
        internaciones_cortas = Internacion.objects.exclude(
            fecha_alta__isnull=True
        ).annotate(
            duracion=ExpressionWrapper(
                F('fecha_alta') - F('fecha_admision'),
                output_field=DurationField()
            )
        ).filter(duracion__lt=timedelta(days=3)).count()
        
        total_internaciones = Internacion.objects.exclude(fecha_alta__isnull=True).count()
        indice_satisfaccion = (
            (internaciones_cortas / total_internaciones * 100)
            if total_internaciones > 0 else 0
        )
        
        return {
            'tiempo_resolucion': round(tiempo_promedio_resolucion, 1),
            'tasa_cancelacion': round(tasa_cancelacion, 1),
            'indice_satisfaccion': round(indice_satisfaccion, 1)
        }
    
    def generar_recomendaciones():
        """Genera recomendaciones basadas en el análisis de datos"""
        recomendaciones = []
        
        # Análisis de capacidad
        camas_disponibles = Cama.objects.filter(estado='L').count()
        total_camas = Cama.objects.count()
        porcentaje_disponible = (camas_disponibles / total_camas * 100) if total_camas > 0 else 0
        
        if porcentaje_disponible < 15:
            recomendaciones.append({
                'tipo': 'critico',
                'titulo': 'Capacidad Crítica',
                'mensaje': 'Considere activar protocolos de emergencia para liberación de camas.',
                'accion': 'Revisar internaciones prolongadas y evaluar altas tempranas.'
            })
        elif porcentaje_disponible < 30:
            recomendaciones.append({
                'tipo': 'advertencia',
                'titulo': 'Capacidad Limitada',
                'mensaje': 'Monitorear closely la disponibilidad de camas.',
                'accion': 'Preparar plan de contingencia para aumento de demanda.'
            })
        
        # Análisis de eficiencia
        promedio_duracion = Internacion.objects.exclude(
            fecha_alta__isnull=True
        ).annotate(
            duracion=ExpressionWrapper(
                F('fecha_alta') - F('fecha_admision'),
                output_field=DurationField()
            )
        ).aggregate(avg=Avg('duracion'))['avg']
        
        if promedio_duracion and promedio_duracion.total_seconds() > 86400 * 7:  # > 7 días
            recomendaciones.append({
                'tipo': 'info',
                'titulo': 'Optimización de Estancia',
                'mensaje': 'La duración promedio de internación es alta.',
                'accion': 'Revisar protocolos de alta y seguimiento post-internación.'
            })
        
        # Análisis de reservas - CORRECCIÓN APLICADA
        # CORRECCIÓN: Las reservas activas son las camas con estado 'R'
        reservas_activas = Cama.objects.filter(estado='R').count()
        camas_disponibles = Cama.objects.filter(estado='L').count()
        if reservas_activas > camas_disponibles * 1.5:
            recomendaciones.append({
                'tipo': 'advertencia',
                'titulo': 'Exceso de Reservas',
                'mensaje': 'Hay más reservas activas que camas disponibles.',
                'accion': 'Revisar política de reservas y tiempos de expiración.'
            })
        
        return recomendaciones
    
    # Obtener datos
    analisis_predictivo = calcular_analisis_predictivo()
    metricas_calidad = calcular_metricas_calidad()
    recomendaciones = generar_recomendaciones()
    
    # Análisis de sectores más demandados
    sectores_demanda = (
        Sector.objects
        .prefetch_related('habitaciones__camas__internacion_set')
        .annotate(
            total_internaciones=Count('habitaciones__camas__internacion')
        )
        .order_by('-total_internaciones')[:5]
    )
    
    # Horarios pico (análisis más detallado)
    horarios_pico = []
    for hora in range(24):
        count = Internacion.objects.filter(
            fecha_admision__hour=hora,
            fecha_admision__gte=timezone.now() - timedelta(days=30)
        ).count()
        horarios_pico.append({
            'hora': f"{hora:02d}:00",
            'count': count,
            'es_pico': count > 0 and count == max([
                Internacion.objects.filter(
                    fecha_admision__hour=h,
                    fecha_admision__gte=timezone.now() - timedelta(days=30)
                ).count() for h in range(24)
            ])
        })
    
    context = {
        # Análisis predictivo
        'datos_historicos': json.dumps(analisis_predictivo['historicos']),
        'prediccion_7_dias': json.dumps(analisis_predictivo['prediccion']),
        'promedio_semanal': analisis_predictivo['promedio_semanal'],
        
        # Métricas de calidad
        'tiempo_resolucion': metricas_calidad['tiempo_resolucion'],
        'tasa_cancelacion': metricas_calidad['tasa_cancelacion'],
        'indice_satisfaccion': metricas_calidad['indice_satisfaccion'],
        
        # Recomendaciones
        'recomendaciones': recomendaciones,
        
        # Análisis adicional
        'sectores_demanda': sectores_demanda,
        'horarios_pico': horarios_pico,
        
        # Fechas
        'fechas_historicas': json.dumps([
            (timezone.now() - timedelta(days=29-i)).strftime('%d %b')
            for i in range(30)
        ]),
        'fechas_prediccion': json.dumps([
            (timezone.now() + timedelta(days=i+1)).strftime('%d %b')
            for i in range(7)
        ]),
        
        'last_update': timezone.now().strftime('%d/%m/%Y %H:%M:%S')
    }
    
    return render(request, 'estadisticas_avanzadas.html', context)


@login_required
def limpiar_reservas_vencidas(request):
    """Vista para limpiar reservas vencidas - SOLUCIONADO: Actualiza correctamente las alertas"""
    if request.method == 'POST':
        now = timezone.now()
        reservas_vencidas = Reserva.objects.filter(fecha_expiracion__lt=now)
        count = reservas_vencidas.count()
        
        # CRÍTICO: Liberar las camas de las reservas vencidas ANTES de eliminar las reservas
        camas_liberadas = 0
        for reserva in reservas_vencidas:
            if reserva.cama.estado == 'R':
                reserva.cama.estado = 'L'  # Liberar la cama
                reserva.cama.save()
                camas_liberadas += 1
        
        # Eliminar las reservas vencidas
        reservas_vencidas.delete()
        
        messages.success(
            request, 
            f'✅ Se limpiaron {count} reservas vencidas y se liberaron {camas_liberadas} camas. '
            f'Las alertas se actualizarán automáticamente.'
        )
        
        return redirect('estadisticas')
    
    # Mostrar página de confirmación
    now = timezone.now()
    reservas_vencidas = Reserva.objects.filter(fecha_expiracion__lt=now).select_related(
        'cama__habitacion', 
        'medico__persona'
    )
    
    context = {
        'reservas_vencidas': reservas_vencidas,
        'count': reservas_vencidas.count()
    }
    
    return render(request, 'limpiar_reservas.html', context)
