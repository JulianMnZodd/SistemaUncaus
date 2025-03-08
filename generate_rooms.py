import os
import django
from random import choice, randint
from faker import Faker

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uncausproject.settings")  # Reemplaza 'tu_proyecto' con el nombre real
django.setup()

from habitaciones.models import Sector, Habitacion, Cama  # Ajusta el nombre de la app si es necesario

fake = Faker("es_ES")

TIPOS_SECTOR = ["GEN", "TER", "VIP", "QUI", "NEO"]
TIPOS_HABITACION = ["VIP", "UCI", "FEM", "MIX", "PED", "MAT", "PSI"]


def crear_sector():
    sector = Sector.objects.create(
        tipo=choice(TIPOS_SECTOR),
        cantidad_habitaciones=randint(1, 5),
        piso=randint(1, 10),
    )
    print(f"Sector creado: {sector.tipo} en el piso {sector.piso}")
    return sector


def crear_habitacion(sector):
    habitacion = Habitacion.objects.create(
        idsector=sector,
        numero=randint(1, 25),
        cantidad_camas=2,
        tipo=choice(TIPOS_HABITACION),
    )
    print(f"Habitación creada: {habitacion.numero} en el sector {sector.tipo}")
    return habitacion


def crear_camas(habitacion):
    for _ in range(2):
        cama = Cama.objects.create(
            habitacion=habitacion,
            estado="L",  # Siempre libre
        )
        print(f"Cama creada en habitación {habitacion.numero}, estado: {cama.estado}")


def generar_sectores_habitaciones(cant_sectores=3):
    for _ in range(cant_sectores):
        sector = crear_sector()
        for _ in range(sector.cantidad_habitaciones):
            habitacion = crear_habitacion(sector)
            crear_camas(habitacion)


if __name__ == "__main__":
    generar_sectores_habitaciones()
