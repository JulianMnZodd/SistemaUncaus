from django.db import models
from personal.models import Enfermero,Medico
from pacientes.models import Paciente
from habitaciones.models import Cama

# Create your models here.


class Diagnostico(models.Model):
    iddiagnostico = models.AutoField(db_column='idDiagnostico', primary_key=True)  # Field name made lowercase.
    idmedico = models.ForeignKey(Medico, models.PROTECT, db_column='idMedico')  # Field name made lowercase.
    idpaciente = models.ForeignKey(Paciente, models.PROTECT, db_column='idPaciente')
    idinternacion = models.ForeignKey('Internacion', models.CASCADE, db_column='idInternacion', blank=True, null=True)  # Field name made lowercase.
    fecha = models.DateTimeField(null=True, blank=True,default=None)
    idmedico_derivado= models.ForeignKey(Medico, models.PROTECT, db_column='idMedico_derivado', blank=True, null=True,related_name='diagnostico_como_derivado')  # Field name made lowercase.
    detalles = models.CharField(max_length=256,null=True, blank=True)
    gravedad = models.CharField(max_length=256,null=True, blank=True)
    tratamiento = models.CharField(max_length=256,null=True, blank=True)
    
    class Meta:
        managed = True
        db_table = 'diagnostico'
        
class Internacion(models.Model):
    idinternacion = models.AutoField(db_column='idInternacion', primary_key=True)  # Field name made lowercase.
    idpaciente = models.ForeignKey(Paciente, models.PROTECT, db_column='idPaciente')  # Field name made lowercase.
    cama = models.ForeignKey(Cama, on_delete=models.CASCADE)
    fecha_admision = models.DateTimeField()
    fecha_alta = models.DateTimeField(null=True, blank=True)
    nota_ingreso = models.CharField(max_length=256)

    class Meta:
        managed = True
        db_table = 'internacion'

class Medicacion(models.Model):
    idmedicacion = models.AutoField(db_column='idMedicacion', primary_key=True)  # Field name made lowercase.
    tipo = models.CharField(max_length=45)
    nombre = models.CharField(max_length=45)
    hora_medicacion = models.TimeField(max_length=45)
    seguimiento = models.ForeignKey('Seguimiento', on_delete=models.CASCADE, related_name='medicaciones', null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'medicacion'

class SignosVitales(models.Model):
    idsignos_vitales = models.AutoField(db_column='idSignos_vitales', primary_key=True)  # Field name made lowercase.
    temperatura_corporal = models.CharField(max_length=45)
    pulso = models.CharField(max_length=45)
    frecuencia_respiratoria = models.CharField(max_length=45)
    seguimiento = models.ForeignKey('Seguimiento', on_delete=models.CASCADE, related_name='signos_vitales', null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'signos_vitales'
        
from django.utils import timezone

class Seguimiento(models.Model):
    idseguimiento = models.AutoField(db_column='idSeguimiento', primary_key=True)  # Field name made lowercase.
    idenfermero = models.ForeignKey(Enfermero, models.PROTECT, db_column='idEnfermero')  # Field name made lowercase.
    observacion = models.CharField(max_length=200)
    idinternacion = models.ForeignKey(Internacion, models.CASCADE, db_column='idInternacion')  # Field name made lowercase.
    fecha = models.DateTimeField(auto_now_add=True)
    class Meta:
        managed = True
        db_table = 'seguimiento'
        
