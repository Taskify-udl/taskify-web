# accounts/models.py
from django.db import models
from django.conf import settings
import random

class EmailVerification(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_code(self):
        self.code = f"{random.randint(0, 999999):06d}"  # 6 dígitos
        self.save()
