import uuid
from django.conf import settings
from django.db import models

class Contract(models.Model):
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contracts",
    )
    service = models.ForeignKey(
        "taskify_app.Service",
        on_delete=models.CASCADE,
        related_name="contracts",
    )
    start_date = models.DateField()
    status = models.CharField(
        max_length=30,
        default="active",
        help_text="active, paused, cancelled, finished",
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "service"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} ({self.user})"
