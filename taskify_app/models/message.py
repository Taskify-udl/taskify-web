from django.db import models
from .conversation import Conversation
from django.conf import settings

class Message(models.Model):
    """
    Un mensaje individual dentro de una conversación.
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Mensaje de {self.sender.username} a las {self.timestamp.strftime('%H:%M')}"