# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class CamaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'camas_group'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_cama_update(self, event):
        idcama = event['idcama']
        estado = event['estado']
        paciente = event.get('paciente', None)  # Usa .get() para evitar el KeyError si no existe la clave

        await self.send(text_data=json.dumps({
            'idcama': idcama,
            'estado': estado,
            'paciente': paciente,  # Esto será None si no se incluye en el evento
        }))
