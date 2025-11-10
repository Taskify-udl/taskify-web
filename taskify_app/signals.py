# taskify_app/signals.py

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils.text import slugify

from .models import Contract, Review, Notification, CustomUser  # OK si se importa en ready()


@receiver(post_save, sender=Contract)
def create_contract_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.service.provider,
            title='Nuevo contrato creado',
            message=f'Has recibido un nuevo contrato para tu servicio "{instance.service.name}".',
            notification_type='contract_created',
            contract=instance,
        )


@receiver(post_save, sender=Review)
def create_review_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.service.provider,
            title='Nueva reseña recibida',
            message=f'Has recibido una reseña de {instance.rating} estrella(s) en tu servicio "{instance.service.name}".',
            notification_type='review_received',
            review=instance,
        )


@receiver(post_save, sender=Contract)
def update_contract_status_notification(sender, instance, created, **kwargs):
    if not created and instance.status != instance._original_status:
        status_messages = {
            'active': 'Tu contrato ha sido activado.',
            'paused': 'Tu contrato ha sido pausado.',
            'cancelled': 'Tu contrato ha sido cancelado.',
            'finished': 'Tu contrato ha sido completado.',
        }

        message = status_messages.get(
            instance.status,
            f'El estado de tu contrato ha cambiado a: {instance.status}',
        )

        Notification.objects.create(
            user=instance.user,
            title='Actualización de contrato',
            message=f'{message} Servicio: "{instance.service.name}".',
            notification_type='contract_status_changed',
            contract=instance,
        )


@receiver(pre_save, sender=CustomUser)
def delete_old_avatar_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    old_file = getattr(old, "avatar", None)
    new_file = getattr(instance, "avatar", None)
    if old_file and old_file.name and old_file != new_file:
        old_file.storage.delete(old_file.name)


@receiver(post_delete, sender=CustomUser)
def delete_avatar_on_delete(sender, instance, **kwargs):
    avatar = getattr(instance, "avatar", None)
    if avatar and avatar.name:
        avatar.storage.delete(avatar.name)


CATEGORIES = [
    # 🧱 Construcción y mantenimiento
    ("Ferretería", "fa-solid fa-screwdriver-wrench"),
    ("Fontanería", "fa-solid fa-faucet"),
    ("Electricidad", "fa-solid fa-bolt"),
    ("Pintura", "fa-solid fa-paint-roller"),
    ("Carpintería", "fa-solid fa-hammer"),
    ("Albañilería", "fa-solid fa-helmet-safety"),
    ("Reformas del hogar", "fa-solid fa-house"),
    ("Climatización", "fa-solid fa-fan"),
    ("Jardinería", "fa-solid fa-seedling"),
    ("Cerrajería", "fa-solid fa-key"),
    ("Limpieza", "fa-solid fa-broom"),
    ("Limpieza industrial", "fa-solid fa-soap"),
    ("Mudanzas", "fa-solid fa-truck-moving"),
    ("Decoración", "fa-solid fa-palette"),

    # 💻 Digital / creativo
    ("Diseño gráfico", "fa-solid fa-pen-nib"),
    ("Edición de imágenes", "fa-solid fa-image"),
    ("Fotografía", "fa-solid fa-camera"),
    ("Edición de vídeo", "fa-solid fa-film"),
    ("Animación 2D/3D", "fa-solid fa-cube"),
    ("Desarrollo web", "fa-solid fa-code"),
    ("Desarrollo móvil", "fa-solid fa-mobile-screen"),
    ("Marketing digital", "fa-solid fa-bullhorn"),
    ("SEO / SEM", "fa-solid fa-chart-line"),
    ("Community manager", "fa-solid fa-users"),
    ("Traducción", "fa-solid fa-language"),
    ("Redacción y copywriting", "fa-solid fa-pen"),
    ("Asistencia virtual", "fa-solid fa-headset"),

    # 🧒 Cuidado personal y familiar
    ("Niñeras", "fa-solid fa-baby"),
    ("Cuidado de mayores", "fa-solid fa-person-cane"),
    ("Asistencia a domicilio", "fa-solid fa-house-user"),
    ("Cuidado de mascotas", "fa-solid fa-paw"),
    ("Entrenador personal", "fa-solid fa-dumbbell"),
    ("Fisioterapia", "fa-solid fa-hand-holding-medical"),
    ("Peluquería", "fa-solid fa-scissors"),
    ("Estética y maquillaje", "fa-solid fa-face-smile-beam"),
    ("Masajes", "fa-solid fa-spa"),
    ("Nutrición", "fa-solid fa-apple-whole"),
    ("Psicología", "fa-solid fa-brain"),

    # 🧾 Profesionales / negocio
    ("Abogacía", "fa-solid fa-scale-balanced"),
    ("Asesoría fiscal y contable", "fa-solid fa-file-invoice-dollar"),
    ("Recursos humanos", "fa-solid fa-people-group"),
    ("Gestión de proyectos", "fa-solid fa-diagram-project"),
    ("Consultoría empresarial", "fa-solid fa-briefcase"),
    ("Arquitectura", "fa-solid fa-ruler-combined"),
    ("Ingeniería", "fa-solid fa-gears"),

    # 🎓 Educación
    ("Clases particulares", "fa-solid fa-book-open"),
    ("Mentoring", "fa-solid fa-user-graduate"),
    ("Formación online", "fa-solid fa-laptop"),
    ("Cursos técnicos", "fa-solid fa-chalkboard-user"),
    ("Idiomas", "fa-solid fa-language"),
    ("Clases de música", "fa-solid fa-guitar"),
    ("Clases de arte y dibujo", "fa-solid fa-palette"),

    # 🛠️ Reparaciones / tecnología
    ("Reparación de ordenadores", "fa-solid fa-computer"),
    ("Reparación de móviles", "fa-solid fa-mobile-screen-button"),
    ("Reparación de electrodomésticos", "fa-solid fa-screwdriver-wrench"),
    ("Instalación de redes", "fa-solid fa-network-wired"),
    ("Seguridad y CCTV", "fa-solid fa-video"),
    ("Impresoras y periféricos", "fa-solid fa-print"),

    # 🚗 Transporte / logística
    ("Taxi / VTC", "fa-solid fa-taxi"),
    ("Transporte de mercancías", "fa-solid fa-truck"),
    ("Mensajería", "fa-solid fa-envelope"),
    ("Alquiler de vehículos", "fa-solid fa-car"),
    ("Transporte en bici / moto", "fa-solid fa-bicycle"),
    ("Grúa y asistencia", "fa-solid fa-truck-pickup"),

    # 🏠 Hogar y estilo de vida
    ("Cocina a domicilio", "fa-solid fa-utensils"),
    ("Catering", "fa-solid fa-bell-concierge"),
    ("Pastelería personalizada", "fa-solid fa-cake-candles"),
    ("Organización de eventos", "fa-solid fa-calendar-check"),
    ("Wedding planner", "fa-solid fa-ring"),
    ("Decoración de interiores", "fa-solid fa-couch"),
    ("Mantenimiento general", "fa-solid fa-screwdriver"),

    # 🧳 Turismo y ocio
    ("Guía turístico", "fa-solid fa-map-location-dot"),
    ("Agencia de viajes", "fa-solid fa-plane"),
    ("Actividades al aire libre", "fa-solid fa-mountain"),
    ("Alojamiento y alquiler vacacional", "fa-solid fa-bed"),
    ("Deportes acuáticos", "fa-solid fa-water"),

    # 🛍️ Comercio / artesanía
    ("Tienda minorista", "fa-solid fa-store"),
    ("E-commerce", "fa-solid fa-cart-shopping"),
    ("Artesanía", "fa-solid fa-hand-sparkles"),
    ("Moda y ropa", "fa-solid fa-shirt"),
    ("Joyería", "fa-solid fa-gem"),
    ("Floristería", "fa-solid fa-fan"),  # o fa-solid fa-seedling si prefieres
    ("Librería", "fa-solid fa-book"),

    # 💡 Tecnología avanzada
    ("Consultoría IT", "fa-solid fa-laptop-code"),
    ("Servicios cloud", "fa-solid fa-cloud"),
    ("Ciberseguridad", "fa-solid fa-shield-halved"),
    ("Soporte técnico", "fa-solid fa-headset"),
    ("Automatización e IA", "fa-solid fa-robot"),
]



def create_default_categories(sender, **kwargs):
    from .models import Category  # import aquí, seguro

    created_count = 0
    updated_count = 0

    for name, icon in CATEGORIES:
        slug = slugify(name)

        obj, created = Category.objects.get_or_create(
            name=name,
            defaults={
                "slug": slug,
                "icon": icon,
                "description": "",
            },
        )

        if created:
            created_count += 1
        else:
            changed = False

            if not obj.slug:
                obj.slug = slug
                changed = True

            if obj.icon != icon:
                obj.icon = icon
                changed = True

            if changed:
                obj.save()
                updated_count += 1

    if created_count or updated_count:
        print(
            f"[taskify_app] Categorías por defecto -> "
            f"creadas: {created_count}, actualizadas: {updated_count}"
        )




