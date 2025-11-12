from django.apps import AppConfig
from django.db.models.signals import post_migrate



class TaskifyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'taskify_app'

    def ready(self):
        # Conectar el handler después de que se hayan aplicado las migraciones
        from . import signals

        post_migrate.connect(
            signals.create_default_categories,
            sender=self,
            dispatch_uid="taskify_create_default_categories",
        )
        post_migrate.connect(
            signals.create_default_users,
            sender=self,
            dispatch_uid="taskify_create_default_users",
        )


