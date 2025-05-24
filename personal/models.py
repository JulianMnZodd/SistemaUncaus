from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class PersonaManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El correo electrónico es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class Persona(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    dni = models.IntegerField(unique=True, blank=True, null=True)
    domicilio = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    genero = models.CharField(max_length=10, choices=[('M', 'Masculino'), ('F', 'Femenino')], blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    objects = PersonaManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'dni']

    class Meta:
        db_table = 'persona'

# Ahora una persona puede tener más de un rol

class Medico(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, db_column='Persona_idPersona')
    especializacion = models.CharField(max_length=45)
    matricula = models.CharField(max_length=45)

    class Meta:
        managed = True
        db_table = 'medico'

class Enfermero(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, db_column='Persona_idPersona')
    matricula = models.CharField(max_length=45)

    class Meta:
        managed = True
        db_table = 'enfermero'

class Recepcionista(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, db_column='Persona_idPersona')
    turno = models.CharField(max_length=10, choices=[('M', 'Mañana'), ('T', 'Tarde')], blank=True)

    class Meta:
        managed = True
        db_table = 'recepcionista'
