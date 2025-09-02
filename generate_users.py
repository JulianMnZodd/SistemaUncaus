import os
import django
from random import choice, randint
from faker import Faker
from django.utils import timezone

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uncausproject.settings")
django.setup()

from personal.models import Persona, Medico, Enfermero, Recepcionista

fake = Faker("es_AR")  # Usar localizacion argentina

# Constantes según el modelo
GENEROS = ["M", "F"]  # Actualizado según las opciones del modelo
TURNOS = ["M", "T"]   # M: Mañana, T: Tarde
ESPECIALIDADES = [
    "Cardiología", "Pediatría", "Neurología", "Dermatología", "Cirugía", 
    "Traumatología", "Oftalmología", "Ginecología", "Urología", "Oncología",
    "Psiquiatría", "Otorrinolaringología", "Gastroenterología"
]

def tiene_rol(persona):
    """Verifica si una persona ya tiene un rol asignado"""
    return (Medico.objects.filter(persona=persona).exists() or 
            Enfermero.objects.filter(persona=persona).exists() or 
            Recepcionista.objects.filter(persona=persona).exists())

def crear_persona():
    """Crea una persona con datos aleatorios"""
    # Generar datos básicos
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = f"{first_name.lower()}.{last_name.lower()}@hospital.com".replace(" ", "")
    
    # Asegurar que el correo sea único
    counter = 1
    base_email = email
    while Persona.objects.filter(email=email).exists():
        email = f"{base_email.split('@')[0]}{counter}@hospital.com"
        counter += 1
    
    # Generar DNI único
    dni = randint(20000000, 45000000)
    while Persona.objects.filter(dni=dni).exists():
        dni = randint(20000000, 45000000)
    
    # Crear la persona con contraseña estándar
    password = "Password123"  # Contraseña por defecto
    
    persona = Persona.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        dni=dni,
        telefono=fake.phone_number(),
        domicilio=fake.address(),
        genero=choice(GENEROS),
        fecha_nacimiento=fake.date_of_birth(minimum_age=25, maximum_age=65),
        is_staff=False,
        is_active=True,
    )
    
    print(f"Persona creada: {persona.first_name} {persona.last_name} (Email: {persona.email}, Password: {password})")
    return persona

def crear_medico(cantidad=5):
    """Crea médicos con especialidades aleatorias"""
    medicos_creados = []
    
    for _ in range(cantidad):
        persona = crear_persona()
        especialidad = choice(ESPECIALIDADES)
        matricula = f"M-{randint(10000, 99999)}"
        
        medico = Medico.objects.create(
            persona=persona,
            especializacion=especialidad,
            matricula=matricula
        )
        
        medicos_creados.append(medico)
        print(f"Médico creado: {persona.first_name} {persona.last_name} - {especialidad} (Matrícula: {matricula})")
    
    return medicos_creados

def crear_enfermero(cantidad=5):
    """Crea enfermeros con matrículas aleatorias"""
    enfermeros_creados = []
    
    for _ in range(cantidad):
        persona = crear_persona()
        matricula = f"E-{randint(10000, 99999)}"
        
        enfermero = Enfermero.objects.create(
            persona=persona,
            matricula=matricula
        )
        
        enfermeros_creados.append(enfermero)
        print(f"Enfermero creado: {persona.first_name} {persona.last_name} (Matrícula: {matricula})")
    
    return enfermeros_creados

def crear_recepcionista(cantidad=5):
    """Crea recepcionistas con turnos aleatorios"""
    recepcionistas_creados = []
    
    for _ in range(cantidad):
        persona = crear_persona()
        turno = choice(TURNOS)
        turno_texto = "Mañana" if turno == "M" else "Tarde"
        
        recepcionista = Recepcionista.objects.create(
            persona=persona,
            turno=turno
        )
        
        recepcionistas_creados.append(recepcionista)
        print(f"Recepcionista creado: {persona.first_name} {persona.last_name} (Turno: {turno_texto})")
    
    return recepcionistas_creados

def crear_admin():
    """Crea un usuario administrador"""
    try:
        admin = Persona.objects.get(email='admin@hospital.com')
        print(f"Administrador ya existe: {admin.email}")
    except Persona.DoesNotExist:
        admin = Persona.objects.create_superuser(
            email='admin@hospital.com',
            password='admin123',
            first_name='Admin',
            last_name='Sistema',
            dni=11111111,
            telefono='123456789',
            domicilio='Hospital Central',
            is_staff=True,
            is_active=True,
        )
        print(f"Administrador creado: {admin.email} (Password: admin123)")
    
    return admin

def generar_usuarios(cant_medicos=5, cant_enfermeros=5, cant_recepcionistas=3):
    """Genera usuarios de diferentes roles"""
    print("=== Generando usuarios del sistema ===")
    
    # Crear admin primero
    crear_admin()
    
    # Crear usuarios de cada tipo
    medicos = crear_medico(cant_medicos)
    enfermeros = crear_enfermero(cant_enfermeros)
    recepcionistas = crear_recepcionista(cant_recepcionistas)
    
    # Imprimir resumen
    print("\n=== Resumen de usuarios generados ===")
    print(f"Administrador: 1")
    print(f"Médicos: {len(medicos)}")
    print(f"Enfermeros: {len(enfermeros)}")
    print(f"Recepcionistas: {len(recepcionistas)}")
    print(f"Total usuarios: {1 + len(medicos) + len(enfermeros) + len(recepcionistas)}")
    print("\nTodos los usuarios tienen la contraseña 'Password123' excepto el admin que usa 'admin123'")

if __name__ == "__main__":
    generar_usuarios()
