from django.conf import settings
from django.db import models

class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    service = models.ForeignKey(
        "taskify_app.Service",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "service"]),
        ]
        unique_together = (("user", "service"),)
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.service} - {self.rating}/5"
