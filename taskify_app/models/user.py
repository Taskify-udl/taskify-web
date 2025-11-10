import uuid
import os
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models


def avatar_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    date_path = timezone.now().strftime("%Y/%m/%d")
    user_part = instance.pk or "tmp"
    return f"avatars/user_{user_part}/{date_path}/{uuid.uuid4().hex}{ext}"


class CustomUser(AbstractUser):
    class Roles(models.TextChoices):
        BASE = "CUSTOMER", "Usuario base"
        PROVIDER = "PROVIDER", "Proveedor"

    phone = models.CharField(max_length=11, blank=True)

    # Rol
    role = models.CharField(
        max_length=10,
        choices=Roles.choices,
        default=Roles.BASE,
        db_index=True,
    )

    # Perfil
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=120, blank=True)
    website = models.URLField(blank=True)
    avatar = models.ImageField(upload_to=avatar_upload_to, blank=True, null=True)

    @property
    def avatar_url(self):
        return self.avatar.url if self.avatar else "/static/img/default-avatar.png"

    # Helpers cómodos
    @property
    def is_provider(self) -> bool:
        return self.role == self.Roles.PROVIDER

