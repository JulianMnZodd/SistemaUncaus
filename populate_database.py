"""
Script maestro para poblar la base de datos completa del sistema hospitalario
Ejecuta todos los generadores en el orden correcto
"""
import os
import sys
import django
import subprocess

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uncausproject.settings')
django.setup()

def ejecutar_script(nombre_archivo, descripcion):
    """Ejecuta un script de Python"""
    print(f"\n{'='*70}")
    print(f"EJECUTANDO: {descripcion}")
    print(f"{'='*70}\n")
    
    python_exe = sys.executable
    resultado = subprocess.run([python_exe, nombre_archivo], capture_output=False)
    
    if resultado.returncode != 0:
        print(f"\n⚠️  Error al ejecutar {nombre_archivo}")
        return False
    return True

def poblar_base_datos_completa():
    """Ejecuta todos los scripts de generación en orden"""
    print(f"\n{'#'*70}")
    print(f"{'#'*70}")
    print(f"  POBLACIÓN COMPLETA DE BASE DE DATOS - SISTEMA HOSPITALARIO")
    print(f"{'#'*70}")
    print(f"{'#'*70}\n")
    
    print("Este script ejecutará los siguientes pasos:")
    print("  1. Generar personal (médicos, enfermeros, recepcionistas)")
    print("  2. Generar infraestructura (sectores, habitaciones, camas)")
    print("  3. Generar pacientes")
    print("  4. Generar internaciones y seguimientos (con fechas históricas)")
    
    confirmar = input("\n¿Desea continuar? (s/n): ").strip().lower()
    
    if confirmar != 's':
        print("Operación cancelada.")
        return
    
    # Paso 1: Personal
    print("\n" + "="*70)
    print("PASO 1/4: GENERANDO PERSONAL")
    print("="*70)
    if not ejecutar_script('generate_users_improved.py', 'Personal Hospitalario'):
        print("❌ Fallo en la generación de personal. Deteniendo proceso.")
        return
    
    # Paso 2: Infraestructura
    print("\n" + "="*70)
    print("PASO 2/4: GENERANDO INFRAESTRUCTURA")
    print("="*70)
    if not ejecutar_script('generate_rooms_improved.py', 'Sectores, Habitaciones y Camas'):
        print("❌ Fallo en la generación de infraestructura. Deteniendo proceso.")
        return
    
    # Paso 3: Pacientes
    print("\n" + "="*70)
    print("PASO 3/4: GENERANDO PACIENTES")
    print("="*70)
    if not ejecutar_script('generate_patients_improved.py', 'Pacientes'):
        print("❌ Fallo en la generación de pacientes. Deteniendo proceso.")
        return
    
    # Paso 4: Internaciones
    print("\n" + "="*70)
    print("PASO 4/4: GENERANDO INTERNACIONES Y SEGUIMIENTOS")
    print("="*70)
    if not ejecutar_script('generate_internaciones.py', 'Internaciones Históricas'):
        print("❌ Fallo en la generación de internaciones. Deteniendo proceso.")
        return
    
    print(f"\n{'#'*70}")
    print(f"{'#'*70}")
    print(f"  ✅ POBLACIÓN COMPLETA FINALIZADA EXITOSAMENTE")
    print(f"{'#'*70}")
    print(f"{'#'*70}\n")
    
    mostrar_resumen()

def mostrar_resumen():
    """Muestra un resumen de los datos generados"""
    from personal.models import Medico, Enfermero, Recepcionista
    from habitaciones.models import Sector, Habitacion, Cama
    from pacientes.models import Paciente
    from internacion.models import Internacion, Diagnostico, Seguimiento
    
    print("\n" + "="*70)
    print("RESUMEN DE DATOS GENERADOS")
    print("="*70)
    
    print(f"\n📋 PERSONAL:")
    print(f"  • Médicos: {Medico.objects.count()}")
    print(f"  • Enfermeros: {Enfermero.objects.count()}")
    print(f"  • Recepcionistas: {Recepcionista.objects.count()}")
    
    print(f"\n🏥 INFRAESTRUCTURA:")
    print(f"  • Sectores: {Sector.objects.count()}")
    print(f"  • Habitaciones: {Habitacion.objects.count()}")
    print(f"  • Camas: {Cama.objects.count()}")
    camas_libres = Cama.objects.filter(estado='L').count()
    camas_ocupadas = Cama.objects.filter(estado='O').count()
    print(f"    - Libres: {camas_libres}")
    print(f"    - Ocupadas: {camas_ocupadas}")
    
    print(f"\n👥 PACIENTES:")
    print(f"  • Total: {Paciente.objects.count()}")
    print(f"  • Vivos: {Paciente.objects.filter(estado='Vivo').count()}")
    
    print(f"\n🏨 INTERNACIONES:")
    print(f"  • Total: {Internacion.objects.count()}")
    print(f"  • Activas: {Internacion.objects.filter(fecha_alta__isnull=True).count()}")
    print(f"  • Finalizadas: {Internacion.objects.filter(fecha_alta__isnull=False).count()}")
    
    print(f"\n📊 REGISTROS MÉDICOS:")
    print(f"  • Diagnósticos: {Diagnostico.objects.count()}")
    print(f"  • Seguimientos: {Seguimiento.objects.count()}")
    
    print(f"\n{'='*70}\n")

def menu_principal():
    """Muestra el menú principal"""
    print(f"\n{'='*70}")
    print(f"GENERADOR DE DATOS - SISTEMA HOSPITALARIO")
    print(f"{'='*70}\n")
    
    print("Opciones:")
    print("  1. Población completa (ejecutar todos los scripts)")
    print("  2. Solo personal (médicos, enfermeros, recepcionistas)")
    print("  3. Solo infraestructura (sectores, habitaciones, camas)")
    print("  4. Solo pacientes")
    print("  5. Solo internaciones y seguimientos")
    print("  6. Mostrar resumen actual")
    print("  0. Salir")
    
    opcion = input("\nSeleccione una opción: ").strip()
    
    if opcion == '1':
        poblar_base_datos_completa()
    elif opcion == '2':
        ejecutar_script('generate_users_improved.py', 'Personal Hospitalario')
    elif opcion == '3':
        ejecutar_script('generate_rooms_improved.py', 'Infraestructura')
    elif opcion == '4':
        ejecutar_script('generate_patients_improved.py', 'Pacientes')
    elif opcion == '5':
        ejecutar_script('generate_internaciones.py', 'Internaciones')
    elif opcion == '6':
        mostrar_resumen()
    elif opcion == '0':
        print("Saliendo...")
        return
    else:
        print("Opción inválida")
    
    # Volver al menú
    input("\nPresione Enter para continuar...")
    menu_principal()

if __name__ == "__main__":
    menu_principal()
