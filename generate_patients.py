import os
import django
import random
from faker import Faker

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uncausproject.settings')
django.setup()

from pacientes.models import Paciente

# Inicializar Faker
fake = Faker()

def generate_patients(n):
    for _ in range(n):
        nombre = fake.first_name()
        apellido = fake.last_name()
        dni = fake.unique.random_number(digits=8)
        domicilio = fake.address()
        localidad = fake.city()
        provincia = fake.state()
        telefono = fake.phone_number()
        fecha_nacimiento = fake.date_of_birth(minimum_age=18, maximum_age=90)
        genero = random.choice(['M', 'F'])
        diabetes = random.choice([True, False])
        hipertension = random.choice([True, False])
        fumador = random.choice([True, False])

        paciente = Paciente(
            nombre=nombre,
            apellido=apellido,
            dni=dni,
            domicilio=domicilio,
            localidad=localidad,
            provincia=provincia,
            telefono=telefono,
            fecha_nacimiento=fecha_nacimiento,
            genero=genero,
            diabetes=diabetes,
            hipertension=hipertension,
            fumador=fumador
        )
        paciente.save()
        print(f'Paciente {nombre} {apellido} creado.')

if __name__ == '__main__':
    generate_patients(10)  # Generar 10 pacientes