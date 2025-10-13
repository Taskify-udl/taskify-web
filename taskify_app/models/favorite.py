from django.conf import settings
from django.db import models

class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    service = models.ForeignKey(
        "taskify_app.Service",
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )
    favorited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("user", "service"),)
        indexes = [
            models.Index(fields=["user", "service"]),
        ]

    def __str__(self):
        return f"{self.user} {self.service}"
