"""
Script para generar internaciones y seguimientos con fechas históricas (hasta 90 días atrás)
Útil para probar estadísticas y reportes
"""
import os
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uncausproject.settings')
django.setup()

from internacion.models import Internacion, Diagnostico, Seguimiento, Medicacion, SignosVitales
from pacientes.models import Paciente
from habitaciones.models import Cama
from personal.models import Medico, Enfermero

# Datos para generar contenido realista
DIAGNOSTICOS = [
    ('Neumonía', 'Moderada', 'Antibióticos y reposo'),
    ('Fractura de cadera', 'Grave', 'Cirugía y rehabilitación'),
    ('Insuficiencia cardíaca', 'Grave', 'Medicación cardiológica'),
    ('Apendicitis aguda', 'Moderada', 'Apendicectomía'),
    ('COVID-19', 'Leve', 'Aislamiento y tratamiento sintomático'),
    ('Diabetes descompensada', 'Moderada', 'Insulina y control glucémico'),
    ('Accidente cerebrovascular', 'Grave', 'Tratamiento neurológico urgente'),
    ('Infección urinaria', 'Leve', 'Antibióticos'),
    ('Hipertensión arterial', 'Moderada', 'Antihipertensivos'),
    ('Gastroenteritis aguda', 'Leve', 'Hidratación y dieta'),
    ('Bronquitis aguda', 'Leve', 'Broncodilatadores y reposo'),
    ('Cálculos renales', 'Moderada', 'Analgésicos y litotripsia'),
    ('Infarto agudo de miocardio', 'Grave', 'Angioplastia de emergencia'),
    ('Pancreatitis aguda', 'Grave', 'Ayuno y analgesia'),
    ('Trombosis venosa profunda', 'Moderada', 'Anticoagulantes'),
]

OBSERVACIONES_SEGUIMIENTO = [
    'Paciente estable, signos vitales normales',
    'Mejoría clínica evidente',
    'Dolor controlado con medicación',
    'Presenta fiebre leve',
    'Sin cambios significativos',
    'Evolución favorable',
    'Requiere monitoreo continuo',
    'Paciente colaborador',
    'Se solicita interconsulta',
    'Saturación de oxígeno normal',
    'Paciente refiere dolor',
    'Control de herida quirúrgica',
    'Se modifica tratamiento',
    'Estable, continúa con tratamiento',
    'Presenta náuseas ocasionales',
]

MEDICAMENTOS = [
    ('Analgésico', 'Paracetamol 500mg'),
    ('Antibiótico', 'Amoxicilina 500mg'),
    ('Antihipertensivo', 'Enalapril 10mg'),
    ('Antiinflamatorio', 'Ibuprofeno 400mg'),
    ('Broncodilatador', 'Salbutamol'),
    ('Antidiabético', 'Metformina 850mg'),
    ('Anticoagulante', 'Heparina'),
    ('Protector gástrico', 'Omeprazol 20mg'),
    ('Diurético', 'Furosemida 40mg'),
    ('Antipirético', 'Dipirona 1g'),
]

NOTAS_INGRESO = [
    'Ingreso por guardia con cuadro agudo',
    'Derivado desde consultorio externo',
    'Ingreso programado para cirugía',
    'Traslado desde otro sector',
    'Ingreso por emergencia',
    'Admisión para estudios complementarios',
    'Ingreso por complicación post-operatoria',
    'Derivación desde otra institución',
]

def generar_fecha_aleatoria(dias_atras_max=90):
    """Genera una fecha aleatoria dentro de los últimos N días (default: 90 días)"""
    dias_atras = random.randint(0, dias_atras_max)
    horas = random.randint(0, 23)
    minutos = random.randint(0, 59)
    fecha = timezone.now() - timedelta(days=dias_atras, hours=horas, minutes=minutos)
    return fecha

def generar_signos_vitales():
    """Genera signos vitales realistas dentro de rangos válidos"""
    return {
        'temperatura': round(random.uniform(35.5, 39.5), 1),  # 30-45°C válido, mayoría 35.5-39.5
        'pulso': random.randint(55, 120),  # 30-200 válido, mayoría 55-120
        'frecuencia_respiratoria': random.randint(12, 24)  # 5-60 válido, mayoría 12-24
    }

def generar_internaciones(cantidad=30, incluir_altas=True):
    """
    Genera internaciones con fechas históricas
    
    Args:
        cantidad: Número de internaciones a crear
        incluir_altas: Si True, algunas internaciones tendrán fecha de alta
    """
    print(f"\n{'='*70}")
    print(f"GENERANDO {cantidad} INTERNACIONES HISTÓRICAS")
    print(f"{'='*70}\n")
    
    # Verificar datos necesarios
    pacientes = list(Paciente.objects.filter(estado='Vivo'))
    camas = list(Cama.objects.all())
    medicos = list(Medico.objects.all())
    enfermeros = list(Enfermero.objects.all())
    
    if not pacientes:
        print("❌ No hay pacientes disponibles. Ejecute generate_patients_improved.py primero.")
        return
    if not camas:
        print("❌ No hay camas disponibles. Ejecute generate_rooms_improved.py primero.")
        return
    if not medicos:
        print("❌ No hay médicos disponibles. Cree médicos primero.")
        return
    if not enfermeros:
        print("❌ No hay enfermeros disponibles. Cree enfermeros primero.")
        return
    
    print(f"✓ Pacientes disponibles: {len(pacientes)}")
    print(f"✓ Camas disponibles: {len(camas)}")
    print(f"✓ Médicos disponibles: {len(medicos)}")
    print(f"✓ Enfermeros disponibles: {len(enfermeros)}\n")
    
    internaciones_creadas = 0
    diagnosticos_creados = 0
    seguimientos_creados = 0
    
    # Asegurar que no se reutilicen pacientes
    pacientes_usados = set()
    # Asegurar que no se reutilicen camas para internaciones activas
    camas_ocupadas = set()
    
    for i in range(cantidad):
        try:
            # Seleccionar paciente que no esté ya internado
            pacientes_disponibles = [p for p in pacientes if p.idpaciente not in pacientes_usados]
            if not pacientes_disponibles:
                print(f"⚠️  No hay más pacientes disponibles después de {internaciones_creadas} internaciones")
                break
            
            paciente = random.choice(pacientes_disponibles)
            pacientes_usados.add(paciente.idpaciente)
            
            # Generar fecha de admisión (entre 0 y 90 días atrás)
            fecha_admision = generar_fecha_aleatoria(90)
            
            # Decidir si tiene alta (70% de las internaciones tienen alta)
            tiene_alta = incluir_altas and random.random() < 0.7
            
            # Seleccionar una cama apropiada
            if tiene_alta:
                # Para internaciones con alta, cualquier cama está bien
                cama = random.choice(camas)
            else:
                # Para internaciones activas, seleccionar una cama que no esté ocupada
                camas_disponibles = [c for c in camas if c.idcama not in camas_ocupadas]
                if not camas_disponibles:
                    print(f"⚠️  No hay más camas disponibles para internaciones activas después de {internaciones_creadas} internaciones")
                    break
                cama = random.choice(camas_disponibles)
                camas_ocupadas.add(cama.idcama)
            
            medico = random.choice(medicos)
            
            if tiene_alta:
                # La fecha de alta es entre 1 y 30 días después de la admisión
                dias_internado = random.randint(1, 30)
                fecha_alta = fecha_admision + timedelta(
                    days=dias_internado,
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                # Asegurar que la fecha de alta no sea futura
                if fecha_alta > timezone.now():
                    fecha_alta = timezone.now() - timedelta(hours=random.randint(1, 24))
                
                # Si tiene alta, la cama debe estar libre
                estado_cama_final = 'L'
            else:
                fecha_alta = None
                # Si no tiene alta (internación activa), la cama está ocupada
                estado_cama_final = 'O'
            
            # Crear internación
            internacion = Internacion.objects.create(
                idpaciente=paciente,
                cama=cama,
                fecha_admision=fecha_admision,
                fecha_alta=fecha_alta,
                nota_ingreso=random.choice(NOTAS_INGRESO)
            )
            internaciones_creadas += 1
            
            # Actualizar estado de la cama
            cama.estado = estado_cama_final
            cama.save()
            
            # Crear diagnóstico
            diagnostico_info = random.choice(DIAGNOSTICOS)
            diagnostico = Diagnostico.objects.create(
                idmedico=medico,
                idpaciente=paciente,
                idinternacion=internacion,
                fecha=fecha_admision,
                detalles=diagnostico_info[0],
                gravedad=diagnostico_info[1],
                tratamiento=diagnostico_info[2],
                idmedico_derivado=random.choice(medicos) if random.random() < 0.3 else None
            )
            diagnosticos_creados += 1
            
            # Generar seguimientos (entre 1 y 10 seguimientos por internación)
            if fecha_alta:
                dias_internado = (fecha_alta - fecha_admision).days
            else:
                dias_internado = (timezone.now() - fecha_admision).days
            
            num_seguimientos = min(random.randint(2, 10), max(1, dias_internado))
            
            for j in range(num_seguimientos):
                # Distribuir seguimientos a lo largo de la internación
                if fecha_alta:
                    tiempo_total = (fecha_alta - fecha_admision).total_seconds()
                else:
                    tiempo_total = (timezone.now() - fecha_admision).total_seconds()
                
                offset_segundos = (tiempo_total / num_seguimientos) * (j + 0.5)
                fecha_seguimiento = fecha_admision + timedelta(seconds=offset_segundos)
                
                enfermero = random.choice(enfermeros)
                
                # Crear seguimiento
                seguimiento = Seguimiento.objects.create(
                    idenfermero=enfermero,
                    idinternacion=internacion,
                    observacion=random.choice(OBSERVACIONES_SEGUIMIENTO),
                    cama_origen=cama if j > 0 and random.random() < 0.1 else None,
                    cama_destino=random.choice(camas) if j > 0 and random.random() < 0.1 else None
                )
                # Actualizar manualmente la fecha (auto_now_add no permite esto en create)
                Seguimiento.objects.filter(idseguimiento=seguimiento.idseguimiento).update(fecha=fecha_seguimiento)
                seguimientos_creados += 1
                
                # Agregar signos vitales (80% de probabilidad)
                if random.random() < 0.8:
                    signos = generar_signos_vitales()
                    SignosVitales.objects.create(
                        seguimiento=seguimiento,
                        temperatura_corporal=str(signos['temperatura']),  # CharField en el modelo
                        pulso=str(signos['pulso']),  # CharField en el modelo
                        frecuencia_respiratoria=str(signos['frecuencia_respiratoria'])  # CharField en el modelo
                    )
                
                # Agregar medicación (60% de probabilidad)
                if random.random() < 0.6:
                    medicamento = random.choice(MEDICAMENTOS)
                    Medicacion.objects.create(
                        seguimiento=seguimiento,
                        tipo=medicamento[0],
                        nombre=medicamento[1],
                        hora_medicacion=datetime.time(datetime.now().replace(
                            hour=random.randint(0, 23),
                            minute=random.choice([0, 30])
                        ))
                    )
            
            if (i + 1) % 10 == 0:
                print(f"  ✓ Procesadas {i + 1}/{cantidad} internaciones...")
        
        except Exception as e:
            print(f"  ✗ Error al crear internación {i + 1}: {e}")
            # Si hubo error, liberar la cama si fue reservada
            if 'cama' in locals() and not tiene_alta:
                camas_ocupadas.discard(cama.idcama)
            continue
    
    # SINCRONIZACIÓN FINAL: Asegurar consistencia entre camas y internaciones
    print(f"\n{'='*70}")
    print(f"SINCRONIZANDO ESTADOS DE CAMAS")
    print(f"{'='*70}\n")
    
    from habitaciones.models import Cama
    camas_corregidas = 0
    
    # 1. Verificar que todas las internaciones activas tengan la cama ocupada
    internaciones_activas = Internacion.objects.filter(fecha_alta__isnull=True)
    for internacion in internaciones_activas:
        if internacion.cama.estado != 'O':
            print(f"  Corrigiendo cama {internacion.cama.idcama}: marcando como ocupada")
            internacion.cama.estado = 'O'
            internacion.cama.save()
            camas_corregidas += 1
    
    # 2. Verificar que todas las camas ocupadas tengan internación activa
    camas_ocupadas_db = Cama.objects.filter(estado='O')
    for cama in camas_ocupadas_db:
        tiene_internacion = Internacion.objects.filter(cama=cama, fecha_alta__isnull=True).exists()
        if not tiene_internacion:
            print(f"  Corrigiendo cama {cama.idcama}: liberando (sin internación activa)")
            cama.estado = 'L'
            cama.save()
            camas_corregidas += 1
    
    if camas_corregidas > 0:
        print(f"\n  ✓ {camas_corregidas} camas corregidas")
    else:
        print(f"  ✓ No se requirieron correcciones")
    
    print(f"\n{'='*70}")
    print(f"✅ PROCESO COMPLETADO")
    print(f"{'='*70}")
    print(f"Internaciones creadas: {internaciones_creadas}")
    print(f"  - Con alta: {Internacion.objects.filter(fecha_alta__isnull=False).count()}")
    print(f"  - Activas: {Internacion.objects.filter(fecha_alta__isnull=True).count()}")
    print(f"Diagnósticos creados: {diagnosticos_creados}")
    print(f"Seguimientos creados: {seguimientos_creados}")
    print(f"{'='*70}\n")

def mostrar_estadisticas():
    """Muestra estadísticas de las internaciones generadas"""
    print(f"\n{'='*70}")
    print(f"ESTADÍSTICAS DE INTERNACIONES")
    print(f"{'='*70}\n")
    
    total = Internacion.objects.count()
    activas = Internacion.objects.filter(fecha_alta__isnull=True).count()
    finalizadas = Internacion.objects.filter(fecha_alta__isnull=False).count()
    
    print(f"Total de internaciones: {total}")
    print(f"  Activas: {activas} ({activas/total*100:.1f}%)" if total > 0 else "  Activas: 0")
    print(f"  Finalizadas: {finalizadas} ({finalizadas/total*100:.1f}%)" if total > 0 else "  Finalizadas: 0")
    
    # Verificar estado de camas
    from habitaciones.models import Cama
    camas_ocupadas = Cama.objects.filter(estado='O').count()
    camas_libres = Cama.objects.filter(estado='L').count()
    camas_reservadas = Cama.objects.filter(estado='R').count()
    total_camas = Cama.objects.count()
    
    print(f"\nEstado de camas:")
    print(f"  Ocupadas: {camas_ocupadas}")
    print(f"  Libres: {camas_libres}")
    print(f"  Reservadas: {camas_reservadas}")
    print(f"  Total: {total_camas}")
    
    # Verificar que internaciones activas coincidan con camas ocupadas
    if activas != camas_ocupadas:
        print(f"\n⚠️  ADVERTENCIA: Internaciones activas ({activas}) ≠ Camas ocupadas ({camas_ocupadas})")
    else:
        print(f"\n✅ Internaciones activas coinciden con camas ocupadas")
    
    # Estadísticas por mes
    from django.db.models import Count
    from django.db.models.functions import TruncMonth
    
    por_mes = Internacion.objects.annotate(
        mes=TruncMonth('fecha_admision')
    ).values('mes').annotate(
        total=Count('idinternacion')
    ).order_by('-mes')[:6]
    
    print(f"\nInternaciones por mes (últimos 6 meses):")
    for item in por_mes:
        mes_nombre = item['mes'].strftime('%B %Y')
        print(f"  {mes_nombre}: {item['total']}")
    
    # Rango de fechas
    primera = Internacion.objects.order_by('fecha_admision').first()
    ultima = Internacion.objects.order_by('-fecha_admision').first()
    
    if primera and ultima:
        print(f"\nRango de fechas:")
        print(f"  Primera internación: {primera.fecha_admision.strftime('%d/%m/%Y')}")
        print(f"  Última internación: {ultima.fecha_admision.strftime('%d/%m/%Y')}")
    
    print(f"\nSeguimientos totales: {Seguimiento.objects.count()}")
    print(f"Diagnósticos totales: {Diagnostico.objects.count()}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    print(f"\n{'='*70}")
    print(f"GENERADOR DE INTERNACIONES Y SEGUIMIENTOS HISTÓRICOS")
    print(f"{'='*70}\n")
    
    print("Este script generará internaciones con fechas de los últimos 90 días")
    print("para poder probar estadísticas y reportes.\n")
    
    cantidad = input("¿Cuántas internaciones desea generar? (default: 30): ").strip()
    cantidad = int(cantidad) if cantidad.isdigit() else 30
    
    incluir_altas = input("¿Incluir altas (70% tendrán alta)? (s/n, default: s): ").strip().lower()
    incluir_altas = incluir_altas != 'n'
    
    confirmar = input(f"\n¿Confirma la creación de {cantidad} internaciones? (s/n): ").strip().lower()
    
    if confirmar == 's':
        generar_internaciones(cantidad, incluir_altas)
        mostrar_estadisticas()
    else:
        print("Operación cancelada.")
