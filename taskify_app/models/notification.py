from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('contract_created', 'Nuevo contrato creado'),
        ('contract_status_changed', 'Estado de contrato cambiado'),
        ('review_received', 'Nueva reseña recibida'),
        ('service_featured', 'Servicio destacado'),
        ('payment_received', 'Pago recibido'),
        ('system', 'Notificación del sistema'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        default='system'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional related objects
    contract = models.ForeignKey(
        'taskify_app.Contract',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    review = models.ForeignKey(
        'taskify_app.Review',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    service = models.ForeignKey(
        'taskify_app.Service',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"

    def mark_as_read(self):
        self.is_read = True
        self.save()