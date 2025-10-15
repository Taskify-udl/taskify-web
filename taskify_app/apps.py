from django.apps import AppConfig


class TaskifyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'taskify_app'

    def ready(self):
        import taskify_app.signals  # noqa
