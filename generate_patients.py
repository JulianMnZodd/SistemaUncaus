import os
import django
import random
from faker import Faker
from django.utils import timezone

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uncausproject.settings')
django.setup()

from pacientes.models import Paciente, ObraSocial

# Inicializar Faker
fake = Faker('es_AR')  # Configuración para Argentina

def crear_obras_sociales():
    """Crea las obras sociales definidas en el modelo si no existen"""
    obras_sociales = []
    
    for nombre in ObraSocial.nombres.keys():
        obra_social, created = ObraSocial.objects.get_or_create(
            nombre=nombre,
            defaults={
                'telefono': fake.phone_number()
            }
        )
        obras_sociales.append(obra_social)
        if created:
            print(f"Obra social creada: {obra_social.nombre}")
        else:
            print(f"Obra social existente: {obra_social.nombre}")
    
    return obras_sociales

def generate_patients(n):
    # Crear obras sociales
    obras_sociales = crear_obras_sociales()
    
    # Lista de provincias argentinas
    provincias_argentinas = [
        'Buenos Aires', 'Catamarca', 'Chaco', 'Chubut', 'Córdoba', 
        'Corrientes', 'Entre Ríos', 'Formosa', 'Jujuy', 'La Pampa', 
        'La Rioja', 'Mendoza', 'Misiones', 'Neuquén', 'Río Negro', 
        'Salta', 'San Juan', 'San Luis', 'Santa Cruz', 'Santa Fe', 
        'Santiago del Estero', 'Tierra del Fuego', 'Tucumán'
    ]
    
    # Lista de países comunes en la región
    paises_comunes = ['AR', 'BR', 'CL', 'UY', 'PY', 'BO', 'PE']
    
    for _ in range(n):
        # Decidir si el paciente es argentino o extranjero
        es_argentino = random.random() < 0.85  # 85% de probabilidad de ser argentino
        
        # Datos personales básicos
        nombre = fake.first_name()
        apellido = fake.last_name()
        fecha_nacimiento = fake.date_of_birth(minimum_age=1, maximum_age=90)
        genero = random.choice(['M', 'F', 'O'])
        email = fake.email()
        telefono = fake.phone_number()
        
        # Información de ubicación
        domicilio = fake.street_address()
        localidad = fake.city()
        
        # Datos de identificación y nacionalidad
        if es_argentino:
            dni = random.randint(10000000, 45000000)
            pasaporte = None if random.random() < 0.7 else fake.unique.random_number(digits=9)
            pais = 'AR'
            provincia = random.choice(provincias_argentinas)
        else:
            dni = None
            pasaporte = fake.unique.random_number(digits=9)
            pais = random.choice(paises_comunes)
            provincia = fake.state() if pais != 'AR' else random.choice(provincias_argentinas)
        
        # Información médica
        diabetes = random.random() < 0.15  # 15% de probabilidad
        hipertension = random.random() < 0.20  # 20% de probabilidad
        fumador = random.random() < 0.30  # 30% de probabilidad
        
        # Información médica adicional (opcional)
        if random.random() < 0.4:
            alergias = ", ".join([fake.word() for _ in range(random.randint(1, 3))])
        else:
            alergias = None
            
        if random.random() < 0.5:
            antecedentes = fake.text(max_nb_chars=200)
        else:
            antecedentes = None
            
        if random.random() < 0.3:
            cirugias = fake.text(max_nb_chars=200)
        else:
            cirugias = None
        
        # Asignar obra social (70% de probabilidad)
        if random.random() < 0.7:
            obra_social = random.choice(obras_sociales)
            nro_afiliado = random.randint(10000, 999999)
        else:
            obra_social = None
            nro_afiliado = None
        
        # Estado (99% vivos, 1% difuntos para tener algunos casos)
        estado = 'Vivo' if random.random() < 0.99 else 'Difunto'
        
        # Crear el paciente
        paciente = Paciente(
            nombre=nombre,
            apellido=apellido,
            dni=dni,
            pais=pais,
            pasaporte=pasaporte,
            domicilio=domicilio,
            localidad=localidad,
            provincia=provincia,
            telefono=telefono,
            fecha_nacimiento=fecha_nacimiento,
            genero=genero,
            obra_social=obra_social,
            nro_afiliado=nro_afiliado,
            diabetes=diabetes,
            hipertension=hipertension,
            fumador=fumador,
            alergias=alergias,
            antecedentes=antecedentes,
            cirugias=cirugias,
            email=email,
            estado=estado
        )
        
        paciente.save()
        print(f'Paciente creado: {paciente.nombre} {paciente.apellido}, DNI: {paciente.dni}, ' +
              f'Obra Social: {paciente.obra_social.nombre if paciente.obra_social else "Ninguna"}')

if __name__ == '__main__':
    cantidad_pacientes = 30  # Puedes ajustar este número
    generate_patients(cantidad_pacientes)
    print(f"Se han generado {cantidad_pacientes} pacientes con datos completos.")