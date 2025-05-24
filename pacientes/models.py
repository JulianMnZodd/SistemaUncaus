from django.db import models
from django_countries.fields import CountryField

class ObraSocial(models.Model):
    nombres ={
        'PAMI': 'PAMI',
        'OSDE': 'OSDE',
        'IOMA': 'IOMA',
        'INSSSEP': 'INSSSEP',
        'Otra': 'Otra'
    }
    
    idobra_social = models.AutoField(db_column='idObra_social', primary_key=True)  # Field name made lowercase.
    nombre = models.CharField(max_length=50, unique=True, choices=nombres.items())  # Nombre de la obra social
    telefono = models.CharField(max_length=15, blank=True, null=True)  # Teléfono de contacto

    class Meta:
        managed = True
        db_table = 'obra_social'

    def __str__(self):
        return self.nombre

class Paciente(models.Model):
    idpaciente = models.AutoField(db_column='idPaciente', primary_key=True)  # Clave primaria
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    dni = models.IntegerField(unique=True, blank=True, null=True)    
    pais = CountryField(blank=True, null=True)
    pasaporte = models.CharField(max_length=50, unique=True, blank=True, null=True)    
    domicilio = models.CharField(max_length=100, blank=True, null=True)
    localidad = models.CharField(max_length=50, blank=True, null=True)
    provincia = models.CharField(max_length=50, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    fecha_nacimiento = models.DateField()
    genero = models.CharField(max_length=10, choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')], blank=True)
    obra_social = models.ForeignKey(ObraSocial, models.SET_NULL, db_column='idObra_social', blank=True, null=True)  # Relación con ObraSocial
    nro_afiliado = models.IntegerField(blank=True, null=True)  # Número de afiliado
    diabetes = models.BooleanField()
    hipertension = models.BooleanField()
    fumador = models.BooleanField()
    alergias = models.CharField(max_length=256, blank=True, null=True)
    antecedentes = models.CharField(max_length=256, blank=True, null=True)
    cirugias = models.CharField(max_length=256, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)
    estado = models.CharField(max_length=10, choices=[('Vivo', 'Vivo'), ('Difunto', 'Difunto')], default='Vivo')
    
    class Meta:
        managed = True
        db_table = 'paciente'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


