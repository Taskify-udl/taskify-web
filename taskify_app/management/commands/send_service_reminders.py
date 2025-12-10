from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from taskify_app.models import Contract, Notification


class Command(BaseCommand):
    help = 'Envía recordatorios de servicios que comienzan mañana'

    def handle(self, *args, **options):
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        # Buscar contratos aceptados que empiezan mañana
        contracts = Contract.objects.filter(
            status='accepted',
            start_date=tomorrow
        ).select_related('user', 'service__provider')
        
        notifications_created = 0
        
        for contract in contracts:
            # Notificación para el cliente
            start_time_str = contract.start_time.strftime('%H:%M') if contract.start_time else 'la hora acordada'
            
            Notification.objects.create(
                user=contract.user,
                title='Recordatorio: Servicio próximo',
                message=f'Mañana comienza tu servicio "{contract.service.name}" a las {start_time_str}. ¡No olvides estar preparado!',
                notification_type='service_reminder_1day',
                contract=contract,
            )
            notifications_created += 1
            
            # Notificación para el proveedor
            client_name = contract.user.get_full_name() or contract.user.username
            
            Notification.objects.create(
                user=contract.service.provider,
                title='Recordatorio: Servicio próximo',
                message=f'Mañana tienes programado el servicio "{contract.service.name}" a las {start_time_str} con {client_name}.',
                notification_type='service_reminder_1day',
                contract=contract,
            )
            notifications_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Se crearon {notifications_created} recordatorios de servicio'
            )
        )
