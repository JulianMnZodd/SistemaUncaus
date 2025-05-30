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
        await self.send(text_data=json.dumps({
            'idcama': event['idcama'],
            'estado': event['estado'],
            'paciente_nombre': event.get('paciente_nombre', ''),
            'paciente_apellido': event.get('paciente_apellido', ''),
        }))
