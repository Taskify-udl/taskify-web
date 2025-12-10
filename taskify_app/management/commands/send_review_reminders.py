from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from taskify_app.models import Contract, Notification, Review


class Command(BaseCommand):
    help = 'Envía recordatorios para dejar reseñas en servicios completados'

    def handle(self, *args, **options):
        # Buscar contratos finalizados hace 1-3 días que no tienen reseña
        date_from = timezone.now().date() - timedelta(days=3)
        date_to = timezone.now().date() - timedelta(days=1)
        
        contracts = Contract.objects.filter(
            status='finished',
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        ).select_related('user', 'service')
        
        notifications_created = 0
        
        for contract in contracts:
            # Verificar si ya tiene reseña
            has_review = Review.objects.filter(
                service=contract.service,
                user=contract.user
            ).exists()
            
            # Verificar si ya se envió recordatorio
            has_reminder = Notification.objects.filter(
                user=contract.user,
                notification_type='review_reminder',
                contract=contract
            ).exists()
            
            if not has_review and not has_reminder:
                Notification.objects.create(
                    user=contract.user,
                    title='¿Cómo fue tu experiencia?',
                    message=f'Has completado el servicio "{contract.service.name}". ¿Te gustaría dejar una reseña?',
                    notification_type='review_reminder',
                    contract=contract,
                )
                notifications_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Se crearon {notifications_created} recordatorios de reseña'
            )
        )
