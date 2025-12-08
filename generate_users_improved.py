"""
Script mejorado para generar usuarios (médicos, enfermeros, recepcionistas) con validaciones correctas
"""
import os
import django
import random
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uncausproject.settings')
django.setup()

from personal.models import Persona, Medico, Enfermero, Recepcionista
from django.contrib.auth.hashers import make_password

# Datos realistas
NOMBRES = [
    'Juan', 'Maria', 'Carlos', 'Ana', 'Roberto', 'Laura', 'Diego', 'Patricia',
    'Jorge', 'Silvia', 'Fernando', 'Marta', 'Ricardo', 'Elena', 'Pablo', 'Rosa',
    'Alberto', 'Carmen', 'Miguel', 'Beatriz', 'Raul', 'Gabriela', 'Daniel', 'Susana',
    'Oscar', 'Liliana', 'Eduardo', 'Monica', 'Sergio', 'Claudia'
]

APELLIDOS = [
    'Gonzalez', 'Rodriguez', 'Fernandez', 'Lopez', 'Martinez', 'Garcia', 'Perez', 'Sanchez',
    'Romero', 'Diaz', 'Torres', 'Alvarez', 'Ruiz', 'Gomez', 'Hernandez', 'Jimenez',
    'Moreno', 'Castro', 'Ortiz', 'Molina'
]

ESPECIALIDADES_MEDICAS = [
    'Cardiología', 'Traumatología', 'Pediatría', 'Neurología', 'Cirugía General',
    'Clínica Médica', 'Ginecología', 'Oncología', 'Dermatología', 'Oftalmología',
    'Otorrinolaringología', 'Urología', 'Nefrología', 'Infectología'
]

CALLES = [
    'Av. San Martín', 'Calle Belgrano', 'Av. Rivadavia', 'Calle Mitre',
    'Calle Sarmiento', 'Av. Corrientes', 'Calle Moreno', 'Av. Independencia'
]

def generar_dni_valido():
    """Genera un DNI argentino válido (7 u 8 dígitos) entre 1.000.000 y 99.999.999"""
    return random.randint(1_000_000, 99_999_999)

def generar_telefono():
    """Genera un teléfono argentino válido (8-15 dígitos)"""
    codigos_area = ['011', '0221', '0351', '0341', '0362', '0381', '0343', '0261']
    codigo = random.choice(codigos_area)
    numero = random.randint(400000, 9999999)
    return f"{codigo}-{numero}"

def generar_fecha_nacimiento_adulto():
    """Genera una fecha de nacimiento para mayores de 18 años"""
    hoy = date.today()
    edad = random.randint(25, 65)  # Entre 25 y 65 años
    anios_atras = random.randint(edad, edad + 1)
    dias_atras = random.randint(0, 365)
    return hoy - timedelta(days=anios_atras * 365 + dias_atras)

def generar_email(nombre, apellido, dominio='hospital.com'):
    """Genera un email profesional"""
    return f"{nombre.lower()}.{apellido.lower()}{random.randint(1, 99)}@{dominio}"

def generar_domicilio():
    """Genera un domicilio válido"""
    calle = random.choice(CALLES)
    numero = random.randint(100, 9999)
    return f"{calle} {numero}"

def generar_matricula(tipo='medico'):
    """Genera un número de matrícula profesional"""
    if tipo == 'medico':
        return f"MN{random.randint(10000, 99999)}"  # Matrícula Nacional
    else:
        return f"ENF{random.randint(1000, 9999)}"

def crear_usuarios(medicos=5, enfermeros=5, recepcionistas=2, password='hospital123'):
    """
    Crea usuarios del sistema con validaciones correctas
    
    Args:
        medicos: Cantidad de médicos a crear
        enfermeros: Cantidad de enfermeros a crear
        recepcionistas: Cantidad de recepcionistas a crear
        password: Contraseña por defecto para todos los usuarios
    """
    print(f"\n{'='*70}")
    print(f"GENERANDO USUARIOS DEL SISTEMA")
    print(f"{'='*70}\n")
    print(f"Médicos: {medicos}")
    print(f"Enfermeros: {enfermeros}")
    print(f"Recepcionistas: {recepcionistas}")
    print(f"Contraseña por defecto: {password}\n")
    
    dnis_usados = set(Persona.objects.values_list('dni', flat=True).filter(dni__isnull=False))
    emails_usados = set(Persona.objects.values_list('email', flat=True))
    
    medicos_creados = 0
    enfermeros_creados = 0
    recepcionistas_creados = 0
    
    # Crear médicos
    print("1. Creando médicos...")
    for i in range(medicos):
        intentos = 0
        max_intentos = 10
        
        while intentos < max_intentos:
            intentos += 1
            
            # Generar DNI y email únicos
            dni = generar_dni_valido()
            if dni in dnis_usados:
                continue
            
            nombre = random.choice(NOMBRES)
            apellido = random.choice(APELLIDOS)
            email = generar_email(nombre, apellido)
            
            if email in emails_usados:
                continue
            
            try:
                # Crear usuario base (Persona)
                persona = Persona.objects.create_user(
                    email=email,
                    password=password,
                    first_name=nombre,
                    last_name=apellido,
                    dni=dni,
                    telefono=generar_telefono(),
                    domicilio=generar_domicilio(),
                    genero=random.choice(['M', 'F']),
                    fecha_nacimiento=generar_fecha_nacimiento_adulto(),
                    is_staff=False,  # No es staff, solo médico
                    is_active=True
                )
                
                # Crear médico
                medico = Medico.objects.create(
                    persona=persona,
                    matricula=generar_matricula('medico'),
                    especializacion=random.choice(ESPECIALIDADES_MEDICAS)
                )
                
                dnis_usados.add(dni)
                emails_usados.add(email)
                medicos_creados += 1
                
                print(f"  ✓ Dr/a. {nombre} {apellido} - {medico.especializacion}")
                print(f"    Email: {email}")
                print(f"    Matrícula: {medico.matricula}\n")
                break
                
            except Exception as e:
                print(f"  ✗ Error al crear médico: {e}")
                continue
    
    # Crear enfermeros
    print("\n2. Creando enfermeros...")
    for i in range(enfermeros):
        intentos = 0
        max_intentos = 10
        
        while intentos < max_intentos:
            intentos += 1
            
            dni = generar_dni_valido()
            if dni in dnis_usados:
                continue
            
            nombre = random.choice(NOMBRES)
            apellido = random.choice(APELLIDOS)
            email = generar_email(nombre, apellido)
            
            if email in emails_usados:
                continue
            
            try:
                persona = Persona.objects.create_user(
                    email=email,
                    password=password,
                    first_name=nombre,
                    last_name=apellido,
                    dni=dni,
                    telefono=generar_telefono(),
                    domicilio=generar_domicilio(),
                    genero=random.choice(['M', 'F']),
                    fecha_nacimiento=generar_fecha_nacimiento_adulto(),
                    is_staff=False,  # No es staff, solo enfermero
                    is_active=True
                )
                
                enfermero = Enfermero.objects.create(
                    persona=persona,
                    matricula=generar_matricula('enfermero')
                )
                
                dnis_usados.add(dni)
                emails_usados.add(email)
                enfermeros_creados += 1
                
                print(f"  ✓ Enf. {nombre} {apellido}")
                print(f"    Email: {email}")
                print(f"    Matrícula: {enfermero.matricula}\n")
                break
                
            except Exception as e:
                print(f"  ✗ Error al crear enfermero: {e}")
                continue
    
    # Crear recepcionistas
    print("\n3. Creando recepcionistas...")
    for i in range(recepcionistas):
        intentos = 0
        max_intentos = 10
        
        while intentos < max_intentos:
            intentos += 1
            
            dni = generar_dni_valido()
            if dni in dnis_usados:
                continue
            
            nombre = random.choice(NOMBRES)
            apellido = random.choice(APELLIDOS)
            email = generar_email(nombre, apellido)
            
            if email in emails_usados:
                continue
            
            try:
                persona = Persona.objects.create_user(
                    email=email,
                    password=password,
                    first_name=nombre,
                    last_name=apellido,
                    dni=dni,
                    telefono=generar_telefono(),
                    domicilio=generar_domicilio(),
                    genero=random.choice(['M', 'F']),
                    fecha_nacimiento=generar_fecha_nacimiento_adulto(),
                    is_staff=False,
                    is_active=True
                )
                
                recepcionista = Recepcionista.objects.create(
                    persona=persona
                )
                
                dnis_usados.add(dni)
                emails_usados.add(email)
                recepcionistas_creados += 1
                
                print(f"  ✓ {nombre} {apellido}")
                print(f"    Email: {email}\n")
                break
                
            except Exception as e:
                print(f"  ✗ Error al crear recepcionista: {e}")
                continue
    
    print(f"\n{'='*70}")
    print(f"✅ PROCESO COMPLETADO")
    print(f"{'='*70}")
    print(f"Médicos creados: {medicos_creados}/{medicos}")
    print(f"Enfermeros creados: {enfermeros_creados}/{enfermeros}")
    print(f"Recepcionistas creados: {recepcionistas_creados}/{recepcionistas}")
    print(f"\n📧 Datos de acceso:")
    print(f"   Email: nombre.apellido##@hospital.com (donde ## es un número)")
    print(f"   Contraseña: {password}")
    print(f"\n⚠️  IMPORTANTE - Permisos:")
    print(f"   • Usuarios creados NO son staff/administradores")
    print(f"   • Cada usuario solo tiene permisos de su rol específico")
    print(f"   • Médicos: diagnósticos, internaciones, estadísticas")
    print(f"   • Enfermeros: seguimientos, signos vitales, medicaciones")
    print(f"   • Recepcionistas: reservas, pacientes, habitaciones")
    print(f"\n🔑 Para crear un administrador:")
    print(f"   python manage.py createsuperuser")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    print(f"\n{'='*70}")
    print(f"GENERADOR DE PERSONAL HOSPITALARIO")
    print(f"{'='*70}\n")
    
    print("Este script creará usuarios para médicos, enfermeros y recepcionistas.\n")
    
    medicos = input("¿Cuántos médicos desea crear? (default: 5): ").strip()
    medicos = int(medicos) if medicos.isdigit() else 5
    
    enfermeros = input("¿Cuántos enfermeros desea crear? (default: 5): ").strip()
    enfermeros = int(enfermeros) if enfermeros.isdigit() else 5
    
    recepcionistas = input("¿Cuántos recepcionistas desea crear? (default: 2): ").strip()
    recepcionistas = int(recepcionistas) if recepcionistas.isdigit() else 2
    
    password = input("Contraseña por defecto (default: hospital123): ").strip()
    password = password if password else 'hospital123'
    
    confirmar = input(f"\n¿Confirma la creación de {medicos} médicos, {enfermeros} enfermeros y {recepcionistas} recepcionistas? (s/n): ").strip().lower()
    
    if confirmar == 's':
        crear_usuarios(medicos, enfermeros, recepcionistas, password)
    else:
        print("Operación cancelada.")
