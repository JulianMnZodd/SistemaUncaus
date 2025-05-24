import os
import django
from random import choice, randint
from faker import Faker

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uncausproject.settings")
django.setup()

from personal.models import Persona, Medico, Enfermero, Recepcionista

fake = Faker("es_ES")

GENEROS = ["M", "F", "O"]
TURNOS = ["Mañana", "Tarde", "Noche"]
ESPECIALIDADES = ["Cardiología", "Pediatría", "Neurología", "Dermatología", "Cirugía"]

def tiene_rol(persona):
    return Medico.objects.filter(persona=persona).exists() or \
           Enfermero.objects.filter(persona=persona).exists() or \
           Recepcionista.objects.filter(persona=persona).exists()

def crear_persona_unica_rol():
    while True:
        persona = Persona.objects.create(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.unique.email(),
            dni=randint(20000000, 45000000),
            telefono=fake.phone_number(),
            domicilio=fake.address(),
            genero=choice(GENEROS),
            fecha_nacimiento=fake.date_of_birth(minimum_age=20, maximum_age=60),
        )
        # Como recién se creó, no tiene rol; devolvemos
        return persona

def crear_medico(persona=None):
    if not persona:
        persona = crear_persona_unica_rol()
    elif tiene_rol(persona):
        print(f"La persona {persona.first_name} {persona.last_name} ya tiene un rol asignado, no se puede crear médico.")
        return
    Medico.objects.create(persona=persona, especializacion=choice(ESPECIALIDADES), matricula=str(randint(10000, 99999)))
    print(f"Médico creado: {persona.first_name} {persona.last_name}")

def crear_enfermero(persona=None):
    if not persona:
        persona = crear_persona_unica_rol()
    elif tiene_rol(persona):
        print(f"La persona {persona.first_name} {persona.last_name} ya tiene un rol asignado, no se puede crear enfermero.")
        return
    Enfermero.objects.create(persona=persona, matricula=str(randint(10000, 99999)))
    print(f"Enfermero creado: {persona.first_name} {persona.last_name}")

def crear_recepcionista(persona=None):
    if not persona:
        persona = crear_persona_unica_rol()
    elif tiene_rol(persona):
        print(f"La persona {persona.first_name} {persona.last_name} ya tiene un rol asignado, no se puede crear recepcionista.")
        return
    Recepcionista.objects.create(persona=persona, turno=choice(TURNOS))
    print(f"Recepcionista creado: {persona.first_name} {persona.last_name}")

def generar_usuarios(cant_medicos=5, cant_enfermeros=5, cant_recepcionistas=5):
    for _ in range(cant_medicos):
        crear_medico()

    for _ in range(cant_enfermeros):
        crear_enfermero()

    for _ in range(cant_recepcionistas):
        crear_recepcionista()

if __name__ == "__main__":
    generar_usuarios()
