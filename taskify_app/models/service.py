from django.conf import settings
from django.db import models


class Service(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="provided_services",
    )
    categories = models.ManyToManyField(
        "taskify_app.Category",
        through="taskify_app.ServiceCategory",
        related_name="services",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name