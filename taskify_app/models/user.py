import uuid
import os
import uuid
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models

def avatar_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()  # p.ej. ".jpg"
    date_path = timezone.now().strftime("%Y/%m/%d")
    user_part = instance.pk or "tmp"
    return f"avatars/user_{user_part}/{date_path}/{uuid.uuid4().hex}{ext}"



class CustomUser(AbstractUser):
    phone = models.CharField(max_length=11, blank=True)

    # Nuevos campos “de perfil” en el propio usuario
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=120, blank=True)
    website = models.URLField(blank=True)
    avatar = models.ImageField(upload_to=avatar_upload_to,
                               blank=True, null=True)



    @property
    def avatar_url(self):
        # Fallback elegante si no hay avatar
        if self.avatar:
            return self.avatar.url
        return "/static/img/default-avatar.png"
