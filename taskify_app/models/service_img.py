from django.db import models
from .service import Service
import os

def service_image_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"services/service_{instance.service.pk}/{filename}"

class ServiceImage(models.Model):
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to=service_image_upload_to)

    def __str__(self):
        return f"Imagen para {self.service.name}"

    def delete(self, *args, **kwargs):
        self.image.delete(save=False)
        super().delete(*args, **kwargs)