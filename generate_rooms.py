import os
import django
from random import choice, randint
from faker import Faker

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uncausproject.settings")  # Reemplaza 'tu_proyecto' con el nombre real
django.setup()

from habitaciones.models import Sector, Habitacion, Cama  # Ajusta el nombre de la app si es necesario

fake = Faker("es_ES")

NOMBRES_SECTOR = ["Terapia Intensiva", "Cardiología", "Pediatría", "Quirófano", "Maternidad", "Oncología"]
TIPOS_HABITACION = ["VIP", "UCI", "FEM", "MIX", "PED", "MAT", "PSI"]


def crear_sector():
    sector = Sector.objects.create(
        nombre=choice(NOMBRES_SECTOR),
        cantidad_habitaciones=randint(1, 5),
        piso=randint(1, 10),
    )
    print(f"Sector creado: {sector.nombre} en el piso {sector.piso}")
    return sector


def crear_habitacion(sector):
    habitacion = Habitacion.objects.create(
        idsector=sector,
        numero=randint(1, 25),
        cantidad_camas=2,
        tipo=choice(TIPOS_HABITACION),
    )
    print(f"Habitación creada: {habitacion.numero} en el sector {sector.nombre}")
    return habitacion


def crear_camas(habitacion):
    for numero_cama in [1, 2]:
        cama = Cama.objects.create(
            habitacion=habitacion,
            nro_cama=numero_cama,  # Asigna 1 y 2
            estado="L",
        )
        print(f"Cama {numero_cama} creada en habitación {habitacion.numero}, estado: {cama.estado}")


def generar_sectores_habitaciones(cant_sectores=3):
    for _ in range(cant_sectores):
        sector = crear_sector()
        for _ in range(sector.cantidad_habitaciones):
            habitacion = crear_habitacion(sector)
            crear_camas(habitacion)


if __name__ == "__main__":
    generar_sectores_habitaciones()
