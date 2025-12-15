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
        post_migrate.connect(
            signals.create_default_services,
            sender=self,
            dispatch_uid="taskify_create_default_services",
        )
        post_migrate.connect(
            signals.create_sample_conversations_and_messages,
            sender=self,
            dispatch_uid="create_sample_conversations_and_messages",
        )
        post_migrate.connect(
            signals.create_random_favorites,
            sender=self,
            dispatch_uid="create_random_favorites",
        )

        # Cargar modelo CLIP para detección NSFW
        try:
            from transformers import CLIPProcessor, CLIPModel
            print("Cargando modelo CLIP (esto puede tardar un poco)...")
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            print("Modelo CLIP cargado correctamente.")
        except ImportError:
            print("Advertencia: 'transformers' no está instalado. La detección NSFW no funcionará.")
            self.clip_model = None
            self.clip_processor = None
        except Exception as e:
            print(f"Error al cargar modelo CLIP: {e}")
            self.clip_model = None
            self.clip_processor = None


