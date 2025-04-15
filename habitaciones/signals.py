from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Cama
from internacion.models import Internacion
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Cama)
def cama_post_save(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    # Obtener el paciente asociado a la cama, si existe
    paciente = None
    if instance.estado == 'O':  # Solo si la cama está ocupada
        internacion = Internacion.objects.filter(cama=instance, fecha_alta__isnull=True).last()
        if internacion:
            paciente = f"{internacion.idpaciente.nombre} {internacion.idpaciente.apellido}"

    async_to_sync(channel_layer.group_send)(
        "camas_group",
        {
            "type": "send_cama_update",
            "idcama": instance.idcama,
            "estado": instance.estado,
            "paciente": paciente,  # Incluye el paciente en el evento
        }
    )
