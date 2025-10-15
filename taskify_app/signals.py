from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Contract, Review, Notification

@receiver(post_save, sender=Contract)
def create_contract_notification(sender, instance, created, **kwargs):
    if created:
        # Notificar al proveedor del servicio
        Notification.objects.create(
            user=instance.service.provider,
            title='Nuevo contrato creado',
            message=f'Has recibido un nuevo contrato para tu servicio "{instance.service.name}".',
            notification_type='contract_created',
            contract=instance
        )

@receiver(post_save, sender=Review)
def create_review_notification(sender, instance, created, **kwargs):
    if created:
        # Notificar al proveedor del servicio
        Notification.objects.create(
            user=instance.service.provider,
            title='Nueva reseña recibida',
            message=f'Has recibido una reseña de {instance.rating} estrella(s) en tu servicio "{instance.service.name}".',
            notification_type='review_received',
            review=instance
        )

@receiver(post_save, sender=Contract)
def update_contract_status_notification(sender, instance, created, **kwargs):
    if not created and instance.status != instance._original_status:
        # Notificar al usuario sobre cambios de estado
        status_messages = {
            'active': 'Tu contrato ha sido activado.',
            'paused': 'Tu contrato ha sido pausado.',
            'cancelled': 'Tu contrato ha sido cancelado.',
            'finished': 'Tu contrato ha sido completado.',
        }

        message = status_messages.get(instance.status, f'El estado de tu contrato ha cambiado a: {instance.status}')

        Notification.objects.create(
            user=instance.user,
            title='Actualización de contrato',
            message=f'{message} Servicio: "{instance.service.name}".',
            notification_type='contract_status_changed',
            contract=instance
        )