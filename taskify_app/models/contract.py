import uuid
from django.conf import settings
from django.db import models
from datetime import timedelta
from django.utils import timezone

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
    start_time = models.TimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        ACTIVE = 'active', 'Active'
        FINISHED = 'finished', 'Finished'
        REJECTED = 'rejected', 'Rejected'
        CANCELLED = 'cancelled', 'Cancelled'

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text="pending, accepted, active, finished, rejected, cancelled",
    )

    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    start_token = models.CharField(max_length=64, unique=True, blank=True, null=True)
    end_token = models.CharField(max_length=64, unique=True, blank=True, null=True)
    start_code_alpha = models.CharField(max_length=8, blank=True, null=True)
    end_code_alpha = models.CharField(max_length=8, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "service"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} ({self.user})"

    def can_be_cancelled_by(self, user):
        """
        Verifica si un usuario puede cancelar este contrato.
        Solo el cliente puede cancelar, y solo si está en estado pending o accepted.
        """
        if self.user == user:
            return self.status in [self.Status.PENDING, self.Status.ACCEPTED]
        elif self.service.provider == user:
            return self.status == self.Status.ACCEPTED
        return False

    def can_be_accepted_by(self, user):
        """
        Verifica si un usuario puede aceptar/rechazar este contrato.
        Solo el proveedor del servicio puede hacerlo, y solo si está pendiente.
        """
        return (
            self.service.provider == user and
            self.status == self.Status.PENDING
        )

    def get_total_duration(self):
        total = timedelta()
        for session in self.sessions.all():
            total += session.duration()
        return total

    def get_formatted_duration(self):
        duration = self.get_total_duration()
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    def save(self, *args, **kwargs):
        if not self.start_token:
            self.start_token = uuid.uuid4().hex
            self.start_code_alpha = self.start_token[:6].upper()
        if not self.end_token:
            self.end_token = uuid.uuid4().hex
            self.end_code_alpha = self.end_token[:6].upper()
        super().save(*args, **kwargs)

class ServiceSession(models.Model):
    contract = models.ForeignKey(Contract, related_name='sessions', on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return timezone.now() - self.start_time
