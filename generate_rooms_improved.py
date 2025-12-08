"""
Script mejorado para generar habitaciones, sectores y camas con validaciones correctas
"""
import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uncausproject.settings')
django.setup()

from habitaciones.models import Sector, Habitacion, Cama, Reserva
from personal.models import Medico
from django.utils import timezone
from datetime import timedelta

# Nombres de sectores hospitalarios realistas
NOMBRES_SECTORES = [
    'Terapia Intensiva',
    'Cardiología',
    'Pediatría',
    'Maternidad',
    'Cirugía General',
    'Traumatología',
    'Oncología',
    'Neurología',
    'Infectología',
    'Nefrología',
    'Clínica Médica',
    'Geriatría',
    'Quirófano',
    'Emergencias',
    'Cuidados Paliativos'
]

def crear_sectores(cantidad=5):
    """Crea sectores hospitalarios"""
    print(f"\n{'='*60}")
    print(f"CREANDO {cantidad} SECTORES")
    print(f"{'='*60}\n")
    
    sectores_creados = []
    nombres_disponibles = NOMBRES_SECTORES.copy()
    random.shuffle(nombres_disponibles)
    
    for i in range(min(cantidad, len(nombres_disponibles))):
        nombre = nombres_disponibles[i]
        piso = random.randint(1, 5)  # Pisos del 1 al 5
        cantidad_habitaciones = random.randint(3, 6)  # Máximo 6 habitaciones por sector
        
        try:
            sector = Sector.objects.create(
                nombre=nombre,
                piso=piso,
                cantidad_habitaciones=cantidad_habitaciones
            )
            sectores_creados.append(sector)
            print(f"  ✓ Sector '{nombre}' - Piso {piso} - {cantidad_habitaciones} habitaciones")
        except Exception as e:
            print(f"  ✗ Error al crear sector '{nombre}': {e}")
    
    print(f"\n✅ {len(sectores_creados)} sectores creados\n")
    return sectores_creados

def crear_habitaciones_y_camas():
    """Crea habitaciones y camas para todos los sectores"""
    print(f"{'='*60}")
    print(f"CREANDO HABITACIONES Y CAMAS")
    print(f"{'='*60}\n")
    
    sectores = Sector.objects.all()
    
    if not sectores.exists():
        print("⚠️  No hay sectores creados. Creando sectores primero...")
        sectores = crear_sectores(5)
    
    habitaciones_creadas = 0
    camas_creadas = 0
    
    for sector in sectores:
        print(f"\nSector: {sector.nombre} (Piso {sector.piso})")
        print(f"  Creando {sector.cantidad_habitaciones} habitaciones...")
        
        for num_hab in range(1, sector.cantidad_habitaciones + 1):
            # Tipo de habitación según el sector
            if 'Intensiva' in sector.nombre or 'UCI' in sector.nombre:
                tipo = 'UCI'
            elif 'Quirófano' in sector.nombre:
                tipo = 'UCI'  # Quirófanos también como UCI
            elif 'Pediatr' in sector.nombre:
                tipo = 'PED'
            elif 'Maternidad' in sector.nombre:
                tipo = 'MAT'
            elif 'Psiquiátr' in sector.nombre:
                tipo = 'PSI'
            else:
                tipo = random.choice(['VIP', 'MIX', 'FEM', 'MIX', 'MIX'])  # Más probabilidad de MIX
            
            # Cantidad de camas según tipo
            if tipo == 'VIP':
                cantidad_camas = 1
            elif tipo == 'UCI':
                cantidad_camas = random.randint(2, 4)
            elif tipo == 'PED':
                cantidad_camas = random.randint(2, 4)
            elif tipo == 'MAT':
                cantidad_camas = random.randint(2, 4)
            elif tipo == 'PSI':
                cantidad_camas = random.randint(2, 4)
            else:  # MIX, FEM
                cantidad_camas = random.randint(2, 4)
            
            try:
                habitacion = Habitacion.objects.create(
                    idsector=sector,
                    numero=num_hab,
                    cantidad_camas=cantidad_camas,
                    tipo=tipo
                )
                habitaciones_creadas += 1
                
                # Crear camas para la habitación
                for nro_cama in range(1, cantidad_camas + 1):
                    # Distribución de estados: 70% Libre, 20% Ocupada, 5% Reservada, 5% Mantenimiento
                    rand = random.random()
                    if rand < 0.70:
                        estado = 'L'
                    elif rand < 0.90:
                        estado = 'O'
                    elif rand < 0.95:
                        estado = 'R'
                    else:
                        estado = 'M'
                    
                    try:
                        cama = Cama.objects.create(
                            habitacion=habitacion,
                            nro_cama=nro_cama,
                            estado=estado
                        )
                        camas_creadas += 1
                        
                        # Si la cama está reservada, crear una reserva con médico
                        if estado == 'R':
                            medicos = Medico.objects.all()
                            if medicos.exists():
                                medico = random.choice(medicos)
                                dias_exp = random.randint(1, 7)
                                Reserva.objects.create(
                                    cama=cama,
                                    medico=medico,
                                    fecha_expiracion=timezone.now() + timedelta(days=dias_exp)
                                )
                    except Exception as e:
                        print(f"    ✗ Error al crear cama {nro_cama} en habitación {num_hab}: {e}")
                
                if habitaciones_creadas % 10 == 0:
                    print(f"  ✓ {habitaciones_creadas} habitaciones creadas...")
                    
            except Exception as e:
                print(f"    ✗ Error al crear habitación {num_hab}: {e}")
    
    print(f"\n{'='*60}")
    print(f"✅ PROCESO COMPLETADO")
    print(f"{'='*60}")
    print(f"Habitaciones creadas: {habitaciones_creadas}")
    print(f"Camas creadas: {camas_creadas}")
    print(f"{'='*60}\n")

def limpiar_datos():
    """Elimina todos los datos existentes"""
    print(f"\n{'='*60}")
    print(f"LIMPIANDO DATOS EXISTENTES")
    print(f"{'='*60}\n")
    
    camas = Cama.objects.count()
    habitaciones = Habitacion.objects.count()
    sectores = Sector.objects.count()
    
    print(f"  Camas a eliminar: {camas}")
    print(f"  Habitaciones a eliminar: {habitaciones}")
    print(f"  Sectores a eliminar: {sectores}")
    
    Cama.objects.all().delete()
    Habitacion.objects.all().delete()
    Sector.objects.all().delete()
    
    print(f"\n✅ Datos eliminados\n")

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"GENERADOR DE INFRAESTRUCTURA HOSPITALARIA")
    print(f"{'='*60}\n")
    
    print("Opciones:")
    print("1. Crear sectores, habitaciones y camas (mantener existentes)")
    print("2. Limpiar todo y crear desde cero")
    print("3. Solo crear sectores")
    
    opcion = input("\nSeleccione una opción (1-3): ").strip()
    
    if opcion == '1':
        cantidad_sectores = input("¿Cuántos sectores desea crear? (default: 5): ").strip()
        cantidad_sectores = int(cantidad_sectores) if cantidad_sectores.isdigit() else 5
        
        crear_sectores(cantidad_sectores)
        crear_habitaciones_y_camas()
        
    elif opcion == '2':
        confirmar = input("⚠️  ¿Confirma eliminar TODOS los datos existentes? (s/n): ").strip().lower()
        if confirmar == 's':
            limpiar_datos()
            cantidad_sectores = input("¿Cuántos sectores desea crear? (default: 8): ").strip()
            cantidad_sectores = int(cantidad_sectores) if cantidad_sectores.isdigit() else 8
            
            crear_sectores(cantidad_sectores)
            crear_habitaciones_y_camas()
        else:
            print("Operación cancelada.")
            
    elif opcion == '3':
        cantidad_sectores = input("¿Cuántos sectores desea crear? (default: 5): ").strip()
        cantidad_sectores = int(cantidad_sectores) if cantidad_sectores.isdigit() else 5
        crear_sectores(cantidad_sectores)
    else:
        print("Opción inválida.")
