"""
Script mejorado para generar pacientes con validaciones correctas
"""
import os
import django
import random
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uncausproject.settings')
django.setup()

from pacientes.models import Paciente, ObraSocial

# Datos realistas argentinos
NOMBRES = [
    'Juan', 'Maria', 'Carlos', 'Ana', 'Roberto', 'Laura', 'Diego', 'Patricia',
    'Jorge', 'Silvia', 'Fernando', 'Marta', 'Ricardo', 'Elena', 'Pablo', 'Rosa',
    'Alberto', 'Carmen', 'Miguel', 'Beatriz', 'Raul', 'Gabriela', 'Daniel', 'Susana',
    'Oscar', 'Liliana', 'Eduardo', 'Monica', 'Sergio', 'Claudia', 'Marcelo', 'Adriana',
    'Luis', 'Graciela', 'Gustavo', 'Isabel', 'Hector', 'Norma', 'Martin', 'Teresa'
]

APELLIDOS = [
    'Gonzalez', 'Rodriguez', 'Fernandez', 'Lopez', 'Martinez', 'Garcia', 'Perez', 'Sanchez',
    'Romero', 'Diaz', 'Torres', 'Alvarez', 'Ruiz', 'Gomez', 'Hernandez', 'Jimenez',
    'Moreno', 'Castro', 'Ortiz', 'Molina', 'Silva', 'Vega', 'Ramos', 'Mendez',
    'Benitez', 'Acosta', 'Cabrera', 'Figueroa', 'Ramirez', 'Rojas', 'Gutierrez', 'Pereyra'
]

PROVINCIAS = [
    'Buenos Aires', 'Córdoba', 'Santa Fe', 'Mendoza', 'Tucumán', 'Entre Ríos',
    'Salta', 'Chaco', 'Corrientes', 'Misiones', 'Santiago del Estero', 'San Juan',
    'Jujuy', 'Río Negro', 'Neuquén', 'Formosa', 'Chubut', 'San Luis', 'Catamarca'
]

LOCALIDADES = {
    'Chaco': ['Resistencia', 'Presidencia Roque Sáenz Peña', 'Barranqueras', 'Fontana', 'Villa Ángela'],
    'Buenos Aires': ['La Plata', 'Mar del Plata', 'Bahía Blanca', 'Tandil', 'Quilmes'],
    'Córdoba': ['Córdoba', 'Villa María', 'Río Cuarto', 'San Francisco'],
    'Santa Fe': ['Rosario', 'Santa Fe', 'Rafaela', 'Venado Tuerto'],
}

CALLES = [
    'Av. San Martín', 'Calle Belgrano', 'Av. Rivadavia', 'Calle Mitre', 'Av. 9 de Julio',
    'Calle Sarmiento', 'Av. Corrientes', 'Calle Moreno', 'Av. Independencia', 'Calle Alberdi',
    'Av. Libertad', 'Calle Pellegrini', 'Av. Alem', 'Calle Irigoyen', 'Av. Castelli'
]

ALERGIAS_COMUNES = [
    'Penicilina', 'Ibuprofeno', 'Aspirina', 'Latex', 'Polen', 'Polvo', 
    'Ninguna', 'Ninguna', 'Ninguna', 'Ninguna'
]

ANTECEDENTES_COMUNES = [
    'Cirugía cardíaca previa', 'Fractura de cadera', 'Apendicitis', 'Hernia inguinal',
    'Colecistectomía', 'Cesárea', 'Ninguno', 'Ninguno', 'Ninguno'
]

def generar_dni_valido():
    """Genera un DNI argentino válido (7 u 8 dígitos entre 1.000.000 y 99.999.999)"""
    # 80% DNIs de 8 dígitos, 20% de 7 dígitos
    if random.random() < 0.8:
        return random.randint(10_000_000, 99_999_999)  # 8 dígitos
    else:
        return random.randint(1_000_000, 9_999_999)  # 7 dígitos

def generar_telefono():
    """Genera un teléfono argentino válido (8-15 dígitos, formato: XXXX-XXXXXXX)"""
    # Códigos de área argentinos (3-4 dígitos) + número local (6-7 dígitos)
    codigos_area = ['011', '0221', '0351', '0341', '0362', '0381', '0343', '0261']
    codigo = random.choice(codigos_area)
    # Generar número local de 6-7 dígitos
    numero = random.randint(400000, 9999999)
    telefono_completo = f"{codigo}{numero}"
    # Formatear: XXXX-XXXXXXX (total 10-11 dígitos)
    return f"{codigo}-{numero}"

def generar_fecha_nacimiento():
    """Genera una fecha de nacimiento válida (entre 1 y 100 años)"""
    hoy = date.today()
    edad = random.randint(1, 95)
    anios_atras = random.randint(edad, edad + 1)
    dias_atras = random.randint(0, 365)
    return hoy - timedelta(days=anios_atras * 365 + dias_atras)

def generar_email(nombre, apellido):
    """Genera un email válido"""
    dominios = ['gmail.com', 'hotmail.com', 'yahoo.com.ar', 'outlook.com']
    return f"{nombre.lower()}.{apellido.lower()}{random.randint(1, 999)}@{random.choice(dominios)}"

def generar_domicilio():
    """Genera un domicilio válido"""
    calle = random.choice(CALLES)
    numero = random.randint(100, 9999)
    return f"{calle} {numero}"

def crear_obras_sociales():
    """Crea las obras sociales si no existen"""
    obras = []
    for nombre in ObraSocial.nombres.keys():
        obra, created = ObraSocial.objects.get_or_create(
            nombre=nombre,
            defaults={'telefono': generar_telefono()}
        )
        obras.append(obra)
        if created:
            print(f"  ✓ Obra social creada: {nombre}")
    return obras

def crear_pacientes(cantidad=50):
    """Crea pacientes con datos válidos"""
    print(f"\n{'='*60}")
    print(f"GENERANDO {cantidad} PACIENTES")
    print(f"{'='*60}\n")
    
    # Crear obras sociales
    print("1. Verificando obras sociales...")
    obras_sociales = crear_obras_sociales()
    
    print(f"\n2. Generando pacientes...")
    dnis_usados = set(Paciente.objects.values_list('dni', flat=True).filter(dni__isnull=False))
    pacientes_creados = 0
    intentos = 0
    max_intentos = cantidad * 3
    
    while pacientes_creados < cantidad and intentos < max_intentos:
        intentos += 1
        
        # Generar DNI único
        dni = generar_dni_valido()
        if dni in dnis_usados:
            continue
        dnis_usados.add(dni)
        
        # Datos básicos
        nombre = random.choice(NOMBRES)
        apellido = random.choice(APELLIDOS)
        provincia = random.choice(PROVINCIAS)
        
        # Seleccionar localidad según provincia
        if provincia in LOCALIDADES:
            localidad = random.choice(LOCALIDADES[provincia])
        else:
            localidad = provincia
        
        # Crear paciente
        try:
            paciente = Paciente.objects.create(
                nombre=nombre,
                apellido=apellido,
                dni=dni,
                email=generar_email(nombre, apellido),
                pais='AR',
                provincia=provincia,
                localidad=localidad,
                domicilio=generar_domicilio(),
                telefono=generar_telefono(),
                fecha_nacimiento=generar_fecha_nacimiento(),
                genero=random.choice(['M', 'F', 'O']),
                obra_social=random.choice(obras_sociales) if random.random() < 0.7 else None,
                nro_afiliado=random.randint(100000, 999999) if random.random() < 0.7 else None,
                diabetes=random.choice([True, False, False, False]),
                hipertension=random.choice([True, False, False, False]),
                fumador=random.choice([True, False, False]),
                alergias=random.choice(ALERGIAS_COMUNES),
                antecedentes=random.choice(ANTECEDENTES_COMUNES),
                cirugias='Ninguna' if random.random() < 0.7 else random.choice([
                    'Apendicectomía', 'Cesárea', 'Hernia', 'Colecistectomía'
                ]),
                estado=random.choice(['Vivo', 'Vivo', 'Vivo', 'Vivo', 'Difunto'])
            )
            pacientes_creados += 1
            if pacientes_creados % 10 == 0:
                print(f"  ✓ Creados {pacientes_creados}/{cantidad} pacientes...")
        except Exception as e:
            print(f"  ✗ Error al crear paciente: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"✅ PROCESO COMPLETADO")
    print(f"{'='*60}")
    print(f"Pacientes creados: {pacientes_creados}")
    print(f"Intentos totales: {intentos}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    cantidad = input("¿Cuántos pacientes desea generar? (default: 50): ").strip()
    cantidad = int(cantidad) if cantidad.isdigit() else 50
    
    confirmar = input(f"¿Confirma la creación de {cantidad} pacientes? (s/n): ").strip().lower()
    
    if confirmar == 's':
        crear_pacientes(cantidad)
    else:
        print("Operación cancelada.")
