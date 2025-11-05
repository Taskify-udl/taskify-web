from django.db import models
from django.conf import settings

class Conversation(models.Model):
    """
    Una conversación entre dos usuarios.
    """
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_other_participant(self, user):
        return self.participants.exclude(id=user.id).first()

    def __str__(self):
        usernames = ", ".join([user.username for user in self.participants.all()])
        return f"Conversación entre {usernames}"