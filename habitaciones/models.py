from django.db import models
from pacientes.models import Paciente
from django.utils import timezone
from datetime import timedelta
# Create your models here.

class Sector(models.Model):
    
    TIPOS_SECTOR = [
        ('General', 'General'),
        ('Terapia', 'Terapia'),
        ('VIP', 'VIP'),
        ('Quirófano', 'Quirófano'),
    ]
    
    idsector = models.AutoField(db_column='idSector', primary_key=True)  # Field name made lowercase.
    tipo = models.CharField(max_length=15, choices=TIPOS_SECTOR)
    cantidad_habitaciones = models.IntegerField()
    piso = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'sector'
        
    def __str__(self):
        return f"{self.tipo}"

class Habitacion(models.Model):
    
    TIPOS_HABITACION = [
        ('VIP', 'VIP'),
        ('UCI', 'UCI'),
        ('FEM', 'Femenina'),
        ('MIX', 'Mixta'),
        ('PED', 'Pediátrica'),
        ('MAT', 'Maternidad'),
        ('PSI', 'Psiquiátrica'),
    ]
    
    idhabitacion = models.AutoField(db_column='idHabitacion', primary_key=True)  # Field name made lowercase.
    idsector = models.ForeignKey(Sector, related_name='habitaciones',on_delete=models.PROTECT, db_column='idSector')  # Field name made lowercase.
    numero = models.IntegerField()
    cantidad_camas = models.IntegerField()
    tipo = models.CharField(max_length=3, choices=TIPOS_HABITACION)
    
    def __str__(self):
        return f"{self.numero}"

    class Meta:
        managed= True
        db_table = 'habitacion'

class Cama(models.Model):
    
    ESTADOS = (
        ('L', 'Libre'),
        ('O', 'Ocupada'),
        ('R', 'Reservada'),
    )
    
    idcama = models.AutoField(db_column='idCama', primary_key=True)  # Field name made lowercase.
    habitacion = models.ForeignKey(Habitacion,on_delete=models.CASCADE, db_column='idHabitacion', related_name='camas')  # Relación inversa.
    estado = models.CharField(max_length=1, choices=ESTADOS, default='L')
    nro_cama = models.IntegerField(default=0)
    
    def liberar(self):
        self.estado = 'L'
        self.paciente = None
        self.save()
        
        # Importación diferida para evitar importación circular
        from internacion.models import Internacion
        # Actualizar la fecha de alta en la internación correspondiente
        internacion = Internacion.objects.filter(cama=self).last()
        if internacion:
            internacion.fecha_alta = timezone.now()
            internacion.save()

    def __str__(self):
        return f"N° cama {self.nro_cama }  N° habitacion {self.habitacion.numero}"
    class Meta:
        managed = True
        db_table = 'cama'

from personal.models import Medico

def default_expiracion():
    return timezone.now() + timedelta(days=2)

class Reserva(models.Model):
    cama = models.ForeignKey(Cama, on_delete=models.CASCADE, related_name='reservas')
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='reservas')
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField(default=default_expiracion)

    
    class Meta:
        managed = True
        db_table = 'reserva'