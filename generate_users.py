import os
import django
from random import choice, randint
from faker import Faker

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uncausproject.settings")  # Reemplaza 'tu_proyecto' con el nombre real
django.setup()

from personal.models import Persona, Medico, Enfermero, Recepcionista  # Ajusta el nombre de la app si es necesario

fake = Faker("es_ES")

GENEROS = ["M", "F", "O"]  # Opcionalmente puedes cambiar los valores
TURNOS = ["Mañana", "Tarde", "Noche"]
ESPECIALIDADES = ["Cardiología", "Pediatría", "Neurología", "Dermatología", "Cirugía"]


def crear_medico():
    email = fake.unique.email()
    persona = Persona.objects.create(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=email,
        dni=randint(20000000, 45000000),
        telefono=fake.phone_number(),
        domicilio=fake.address(),
        genero=choice(GENEROS),
        fecha_nacimiento=fake.date_of_birth(minimum_age=25, maximum_age=60),
    )
    medico = Medico.objects.create(persona=persona, especializacion=choice(ESPECIALIDADES), matricula=str(randint(10000, 99999)))
    print(f"Médico creado: {persona.first_name} {persona.last_name} - {medico.especializacion}")


def crear_enfermero():
    email = fake.unique.email()
    persona = Persona.objects.create(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=email,
        dni=randint(20000000, 45000000),
        telefono=fake.phone_number(),
        domicilio=fake.address(),
        genero=choice(GENEROS),
        fecha_nacimiento=fake.date_of_birth(minimum_age=22, maximum_age=55),
    )
    enfermero = Enfermero.objects.create(persona=persona, matricula=str(randint(10000, 99999)))
    print(f"Enfermero creado: {persona.first_name} {persona.last_name}")


def crear_recepcionista():
    email = fake.unique.email()
    persona = Persona.objects.create(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=email,
        dni=randint(20000000, 45000000),
        telefono=fake.phone_number(),
        domicilio=fake.address(),
        genero=choice(GENEROS),
        fecha_nacimiento=fake.date_of_birth(minimum_age=20, maximum_age=50),
    )
    recepcionista = Recepcionista.objects.create(persona=persona, turno=choice(TURNOS))
    print(f"Recepcionista creado: {persona.first_name} {persona.last_name} - Turno {recepcionista.turno}")


def generar_usuarios(cant_medicos=5, cant_enfermeros=5, cant_recepcionistas=5):
    for _ in range(cant_medicos):
        crear_medico()
    for _ in range(cant_enfermeros):
        crear_enfermero()
    for _ in range(cant_recepcionistas):
        crear_recepcionista()

if __name__ == "__main__":
    generar_usuarios()
