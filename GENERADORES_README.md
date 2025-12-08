# Scripts de Generación de Datos - BedWise Hospital System

Este conjunto de scripts permite poblar la base de datos con datos de prueba realistas para el sistema hospitalario BedWise.

## 📋 Scripts Disponibles

### 1. **populate_database.py** (⭐ RECOMENDADO)
Script maestro que ejecuta todos los generadores en el orden correcto.

```bash
python populate_database.py
```

**Características:**
- Menú interactivo
- Ejecuta todos los scripts en orden correcto
- Muestra resumen de datos generados
- Validación de dependencias

---

### 2. **generate_users_improved.py**
Genera personal hospitalario (médicos, enfermeros, recepcionistas).

```bash
python generate_users_improved.py
```

**Datos generados:**
- ✓ Usuarios con DNI válido (7-8 dígitos)
- ✓ Emails únicos profesionales
- ✓ Mayores de 18 años
- ✓ Matrículas profesionales
- ✓ Especialidades médicas realistas

**Datos de acceso:**
- Email: `nombre.apellido@hospital.com`
- Contraseña: `hospital123` (configurable)

**⚠️ IMPORTANTE - Permisos:**
- Los usuarios generados **NO tienen permisos de staff/administrador**
- Cada usuario solo tiene los permisos de su rol (médico, enfermero o recepcionista)
- Para crear un usuario administrador, usar el comando de Django:
  ```bash
  python manage.py createsuperuser
  ```

**Roles y permisos:**
- **Médicos**: Pueden crear/editar diagnósticos, ver internaciones, estadísticas médicas
- **Enfermeros**: Pueden crear seguimientos, actualizar signos vitales, medicaciones
- **Recepcionistas**: Pueden reservar camas, gestionar pacientes, ver habitaciones
- **Staff/Admin**: Acceso completo a todas las funciones del sistema

---

### 3. **generate_rooms_improved.py**
Genera infraestructura hospitalaria (sectores, habitaciones, camas).

```bash
python generate_rooms_improved.py
```

**Datos generados:**
- ✓ Sectores con nombres realistas (Terapia Intensiva, Cardiología, etc.)
- ✓ Habitaciones por sector (5-15 por sector)
- ✓ Camas con estados distribuidos (70% Libre, 20% Ocupada, 5% Reservada, 5% Mantenimiento)
- ✓ Tipos de habitaciones (Individual, Doble, Compartida, Suite, Quirófano)

**Opciones:**
1. Crear sectores y habitaciones (mantener existentes)
2. Limpiar todo y crear desde cero
3. Solo crear sectores

---

### 4. **generate_patients_improved.py**
Genera pacientes con datos válidos.

```bash
python generate_patients_improved.py
```

**Datos generados:**
- ✓ DNI argentino válido (10.000.000 - 45.000.000)
- ✓ Fechas de nacimiento válidas (1-95 años)
- ✓ Teléfonos con formato correcto (XXXX-XXXXXXX)
- ✓ Emails únicos
- ✓ Obras sociales (PAMI, OSDE, IOMA, INSSSEP)
- ✓ Datos médicos (diabetes, hipertensión, alergias, etc.)
- ✓ Provincias y localidades argentinas

---

### 5. **generate_internaciones.py** (⭐ IMPORTANTE PARA ESTADÍSTICAS)
Genera internaciones y seguimientos con **fechas históricas** (hasta 90 días atrás).

```bash
python generate_internaciones.py
```

**Datos generados:**
- ✓ Internaciones con fechas de los últimos 90 días
- ✓ 70% con fecha de alta (finalizadas)
- ✓ 30% activas (sin alta)
- ✓ **Actualiza estado de camas** (Ocupadas para activas, Libres para finalizadas)
- ✓ Diagnósticos médicos realistas
- ✓ Seguimientos distribuidos durante la internación
- ✓ Signos vitales (temperatura, pulso, frecuencia respiratoria)
- ✓ Medicaciones con horarios
- ✓ Observaciones de enfermería

**⚠️ IMPORTANTE - Estadísticas:**
Las estadísticas del dashboard muestran datos de los **últimos 30 días** por defecto.
Para ver todos los datos generados (90 días):
1. Ve a Estadísticas en el menú
2. Cambia el selector de período a **90 días**
3. Verás todas las internaciones históricas generadas

**Útil para probar:**
- Estadísticas de los últimos 3 meses
- Reportes trimestrales
- Gráficos de tendencias mensuales
- Ocupación de camas en el tiempo
- Informe de internaciones (seleccionar últimos 90 días)

---

## 🚀 Uso Recomendado

### Población Completa (Primera vez)

1. **Ejecutar el script maestro:**
```bash
python populate_database.py
```

2. **Seleccionar opción 1** (Población completa)

3. **Ingresar cantidades deseadas:**
   - Médicos: 10
   - Enfermeros: 10
   - Recepcionistas: 3
   - Sectores: 8
   - Pacientes: 100
   - Internaciones: 50

### Agregar Más Datos

Para agregar datos sin borrar los existentes, ejecutar scripts individuales:

```bash
# Agregar más pacientes
python generate_patients_improved.py

# Agregar más internaciones históricas
python generate_internaciones.py
```

---

## 📊 Orden de Ejecución

**IMPORTANTE:** Los scripts deben ejecutarse en este orden:

1. `generate_users_improved.py` → Personal (médicos y enfermeros)
2. `generate_rooms_improved.py` → Infraestructura (sectores, habitaciones, camas)
3. `generate_patients_improved.py` → Pacientes
4. `generate_internaciones.py` → Internaciones y seguimientos

**Dependencias:**
- Las internaciones requieren: médicos, enfermeros, pacientes y camas
- Las habitaciones requieren: sectores
- Los seguimientos requieren: enfermeros e internaciones

---

## ✅ Validaciones Implementadas

### Pacientes
- DNI: 7-8 dígitos únicos
- Email: formato válido y único
- Teléfono: 8-15 dígitos
- Fecha nacimiento: no futuro, máximo 120 años

### Personal
- DNI: >= 1.000.000
- Edad: >= 18 años
- Email: único en el sistema
- Nombres/Apellidos: solo letras

### Internaciones
- Fecha admisión: hasta 90 días atrás
- Fecha alta: posterior a admisión
- No permite duplicados (paciente ya internado)

---

## 🔧 Troubleshooting

### Error: "No hay médicos/enfermeros disponibles"
**Solución:** Ejecutar primero `generate_users_improved.py`

### Error: "No hay camas disponibles"
**Solución:** Ejecutar primero `generate_rooms_improved.py`

### Error: "No hay pacientes disponibles"
**Solución:** Ejecutar primero `generate_patients_improved.py`

### Error: DNI duplicado
**Solución:** El script intentará generar otro DNI automáticamente

---

## 📈 Datos Generados por Defecto

| Tipo | Cantidad Default | Personalizable |
|------|------------------|----------------|
| Médicos | 5 | ✅ |
| Enfermeros | 5 | ✅ |
| Recepcionistas | 2 | ✅ |
| Sectores | 8 | ✅ |
| Habitaciones | 5-15 por sector | Automático |
| Camas | 1-4 por habitación | Según tipo |
| Pacientes | 50 | ✅ |
| Internaciones | 30 | ✅ |

---

## 💡 Tips

1. **Para probar estadísticas:** Usar `generate_internaciones.py` con cantidad alta (50-100)
2. **Para ambiente de desarrollo:** Usar cantidades pequeñas (10-20)
3. **Para demo:** Ejecutar población completa con valores default
4. **Para limpiar:** Usar opción 2 en `generate_rooms_improved.py` (⚠️ elimina datos)

---

## 📝 Ejemplos de Uso

### Caso 1: Setup Inicial
```bash
python populate_database.py
# Opción 1: Población completa
# Seguir instrucciones interactivas
```

### Caso 2: Agregar Más Internaciones Históricas
```bash
python generate_internaciones.py
# Ingresar: 100 internaciones
# Confirmar: s
```

### Caso 3: Resetear Solo Infraestructura
```bash
python generate_rooms_improved.py
# Opción 2: Limpiar y crear desde cero
# Confirmar: s
# Ingresar: 10 sectores
```

---

## 🎯 Scripts Antiguos

Los siguientes scripts originales están disponibles pero **no se recomiendan** (sin validaciones):
- `generate_patients.py` (usar `generate_patients_improved.py`)
- `generate_rooms.py` (usar `generate_rooms_improved.py`)
- `generate_users.py` (usar `generate_users_improved.py`)

---

## 📞 Soporte

Para problemas o mejoras, contactar al equipo de desarrollo.

**Última actualización:** Noviembre 2025
