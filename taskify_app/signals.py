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

# Debajo de CATEGORIES, por ejemplo:

PROFILE_SEED_DATA = {
    CustomUser.Roles.CUSTOMER: {
        "first_name": "Laura",
        "last_name": "García",
        "phone": "612345678",
        "location": "Barcelona, España",
        "website": "https://lauragarcia.example.com",
        "bio": "Usuario particular que contrata servicios de reformas y mantenimiento del hogar.",
        "profession": "Cliente particular",
        "avatar_file": "customer.jpg",
    },
    CustomUser.Roles.PROVIDER: {
        "first_name": "Carlos",
        "last_name": "López",
        "phone": "622334455",
        "location": "Madrid, España",
        "website": "https://carlos-servicios.example.com",
        "bio": "Proveedor profesional con años de experiencia coordinando equipos y proyectos.",
        "profession": "Proveedor profesional",
        "avatar_file": "provider.jpg",
    },
    CustomUser.Roles.FREELANCER: {
        "first_name": "Marta",
        "last_name": "Sánchez",
        "phone": "633445566",
        "location": "Valencia, España",
        "website": "https://marta-freelance.example.com",
        "bio": "Freelancer especializada en diseño gráfico y branding para pequeñas empresas.",
        "profession": "Diseñadora gráfica",
        "avatar_file": "freelancer.webp",
    },
    CustomUser.Roles.COMPANY_ADMIN: {
        "first_name": "Javier",
        "last_name": "Ruiz",
        "phone": "644556677",
        "location": "Sevilla, España",
        "website": "https://empresa-obras.example.com",
        "bio": "Administrador de empresa de construcción y reformas, responsable de la gestión de contratos.",
        "profession": "Administrador de empresa",
        "avatar_file": "company_admin.webp",
    },
    CustomUser.Roles.COMPANY_WORKER: {
        "first_name": "Ana",
        "last_name": "Fernández",
        "phone": "655667788",
        "location": "Bilbao, España",
        "website": "https://ana-tecnica.example.com",
        "bio": "Trabajadora de empresa especializada en instalaciones y mantenimiento técnico.",
        "profession": "Técnica de instalaciones",
        "avatar_file": "company_worker.jpg",
    },
}


def _assign_seed_avatar(user, profile, image_dir):
    """
    Asigna el avatar desde seed_images/users si existe el archivo.
    Elimina el avatar anterior si existe.
    """
    import os
    from django.core.files import File

    avatar_filename = profile.get("avatar_file")
    if not avatar_filename:
        print(f"[taskify_app] Usuario {user.username}: no hay avatar_file definido en PROFILE_SEED_DATA.")
        return

    avatar_path = os.path.join(image_dir, avatar_filename)
    print(f"[taskify_app] Usuario {user.username}: buscando avatar en: {avatar_path}")

    if not os.path.exists(avatar_path):
        print(f"[taskify_app] AVISO: archivo de avatar NO encontrado: {avatar_path}")
        return

    # Elimina el avatar anterior si existe
    if user.avatar and user.avatar.name:
        try:
            user.avatar.delete(save=False)
            print(f"[taskify_app] Avatar anterior eliminado para {user.username}.")
        except Exception as e:
            print(f"[taskify_app] ERROR eliminando avatar anterior de {user.username}: {e}")

    try:
        with open(avatar_path, "rb") as f:
            user.avatar.save(avatar_filename, File(f), save=True)
        print(f"[taskify_app] Usuario {user.username}: avatar asignado correctamente.")
    except Exception as e:
        print(f"[taskify_app] ERROR asignando avatar a {user.username}: {e}")


def create_default_users(sender=None, **kwargs):
    """
    Crea un usuario por cada rol en CustomUser.Roles con datos de ejemplo.
    - username: <role_lower>
    - email: <role_lower>@example.com
    - password (solo para usuarios creados): '1234'
    - role: el rol correspondiente
    - Rellena phone, bio, location, website y avatar si hay datos en PROFILE_SEED_DATA.
    """
    import os
    from django.contrib.auth import get_user_model

    User = get_user_model()
    created_count = 0
    updated_count = 0

    base_dir = os.path.dirname(__file__)
    image_dir = os.path.join(base_dir, "seed_images", "users")
    print(f"[taskify_app] Carpeta de avatares seed: {image_dir}")
    if not os.path.isdir(image_dir):
        print(f"[taskify_app] AVISO: la carpeta de avatares no existe: {image_dir}")

    for role_value, _ in CustomUser.Roles.choices:
        username = f"{role_value.lower()}"
        email = f"{role_value.lower()}@example.com"

        default_first_name = role_value.capitalize().replace("_", " ")
        profile = PROFILE_SEED_DATA.get(role_value, {})
        first_name = profile.get("first_name", default_first_name)
        last_name = profile.get("last_name", "")

        user = User.objects.filter(username=username).first()
        if not user:
            # Crear usuario nuevo
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role_value,
                is_active=True,
            )
            # Rellenar todos los campos posibles
            user.phone = profile.get("phone", "")
            user.location = profile.get("location", "")
            user.website = profile.get("website", "")
            user.bio = profile.get("bio", "")
            user.profession = profile.get("profession", "")
            user.set_password("1234")
            user.save()
            created_count += 1
            print(f"[taskify_app] Usuario creado: {username} ({role_value})")
            # Asignar avatar (siempre, elimina el anterior si hay)
            _assign_seed_avatar(user, profile, image_dir)
        else:
            # Usuario ya existía → actualizar datos de perfil
            changed = False

            if getattr(user, "role", None) != role_value:
                user.role = role_value
                changed = True

            if user.first_name != first_name:
                user.first_name = first_name
                changed = True

            if user.last_name != last_name:
                user.last_name = last_name
                changed = True

            if user.phone != profile.get("phone", ""):
                user.phone = profile.get("phone", "")
                changed = True

            if user.location != profile.get("location", ""):
                user.location = profile.get("location", "")
                changed = True

            if user.website != profile.get("website", ""):
                user.website = profile.get("website", "")
                changed = True

            if user.bio != profile.get("bio", ""):
                user.bio = profile.get("bio", "")
                changed = True

            if hasattr(user, "profession") and user.profession != profile.get("profession", ""):
                user.profession = profile.get("profession", "")
                changed = True

            if changed:
                user.save()
                updated_count += 1
                print(f"[taskify_app] Usuario actualizado: {username} ({role_value})")
            # Asignar avatar (siempre, elimina el anterior si hay)
            _assign_seed_avatar(user, profile, image_dir)

    if created_count or updated_count:
        print(
            f"[taskify_app] Usuarios por defecto -> "
            f"creados: {created_count}, actualizados: {updated_count}"
        )
    return {"created": created_count, "updated": updated_count}



# python
def create_default_services(image_dir=None, sender=None, **kwargs):
    """
    Crea 3 servicios de ejemplo y les asigna imágenes desde:
    taskify_app/seed_images/services/
    Archivos esperados: fontaneria.jpg, albanileria.jpg, diseno.jpg
    """
    import os
    from django.utils.text import slugify
    from django.core.files import File
    from django.contrib.auth import get_user_model

    try:
        from .models import Service, ServiceImage, Category
    except Exception as e:
        print("[taskify_app] No se pudieron importar modelos Service/ServiceImage/Category:", e)
        return {"created_services": 0, "created_images": 0, "errors": 1}

    User = get_user_model()

    # Ruta por defecto si no se proporciona
    if not image_dir:
        image_dir = os.path.join(os.path.dirname(__file__), "seed_images", "services")

    # Mapeo: (nombre_del_servicio, filename_imagen, descripcion, categoría_preferida, rol_asignado)
    items = [
        ("Fontanería", "fontaneria.jpg", "Reparación y mantenimiento de tuberías y grifería.", "Fontanería",
         CustomUser.Roles.FREELANCER),
        ("Albañilería", "albanileria.jpg", "Obras, reformas y pequeñas construcciones.", "Albañilería",
         CustomUser.Roles.COMPANY_ADMIN),
        ("Diseño gráfico", "diseno.jpg", "Diseño de logotipos, piezas gráficas y branding.", "Diseño gráfico",
         CustomUser.Roles.FREELANCER),
    ]

    created_services = 0
    created_images = 0
    errors = 0

    for name, filename, description, category_name, role_value in items:
        try:
            provider = User.objects.filter(role=role_value).first()
            if not provider:
                print(f"[taskify_app] No se encontró usuario con rol {role_value} para asignar el servicio {name}.")
                errors += 1
                continue

            # Buscar categoría asociada si existe
            category = None
            try:
                category = Category.objects.filter(name__iexact=category_name).first()
            except Exception:
                category = None

            slug = slugify(name)
            defaults = {"description": description, "price": 20.0}
            # Intenta crear el servicio (ajusta campos si tu modelo requiere otros)
            service, created = Service.objects.get_or_create(
                name=name,
                provider=provider,
                defaults={**defaults, "slug": slug} if "slug" in [f.name for f in Service._meta.fields] else defaults,
            )

            if created:
                created_services += 1
            else:
                # actualizar descripción/precio si es distinto
                changed = False
                if getattr(service, "description", None) != description:
                    service.description = description
                    changed = True
                if getattr(service, "price", None) != 20.0:
                    try:
                        service.price = 20.0
                        changed = True
                    except Exception:
                        pass
                if changed:
                    service.save()

            # Agregar categoría si existe y modelo tiene relación many-to-many llamada 'categories'
            try:
                if category and hasattr(service, "categories"):
                    if not service.categories.filter(pk=category.pk).exists():
                        service.categories.add(category)
            except Exception:
                pass

            # Adjuntar imagen si no tiene imágenes
            try:
                has_images = False
                if hasattr(service, "images"):
                    # si related_name es 'images'
                    has_images = service.images.exists()
                else:
                    # intenta ServiceImage por FK
                    has_images = ServiceImage.objects.filter(service=service).exists()

                image_path = os.path.join(image_dir, filename)
                if not has_images and os.path.exists(image_path):
                    with open(image_path, "rb") as f:
                        django_file = File(f, name=filename)
                        # intenta crear ServiceImage según firma esperada
                        si = ServiceImage.objects.create(service=service, image=django_file)
                        si.save()
                        created_images += 1
                elif not os.path.exists(image_path):
                    print(f"[taskify_app] Imagen no encontrada: {image_path}")
                    errors += 1
            except Exception as img_exc:
                print(f"[taskify_app] Error añadiendo imagen al servicio {name}: {img_exc}")
                errors += 1

        except Exception as exc:
            print(f"[taskify_app] Error creando servicio {name}: {exc}")
            errors += 1

    print(
        f"[taskify_app] Servicios creados: {created_services}, imágenes añadidas: {created_images}, errores: {errors}")
    return {"created_services": created_services, "created_images": created_images, "errors": errors}


def create_sample_conversations_and_messages(sender=None, **kwargs):
    """
    Crea conversaciones y mensajes de ejemplo entre todos los usuarios activos (no superusers).
    - Una conversación por cada par de usuarios (A-B).
    - Si la conversación ya existe, la reutiliza.
    - Si la conversación no tiene mensajes, se crean varios mensajes simulando un chat.
    """
    from django.contrib.auth import get_user_model
    from django.db.models import Count

    try:
        from .models import Conversation, Message  # ajusta si tus modelos están en otro módulo
    except Exception as e:
        print("[taskify_app] No se pudieron importar Conversation/Message:", e)
        return {"created_conversations": 0, "created_messages": 0, "errors": 1}

    User = get_user_model()

    # Cogemos solo usuarios activos y no superusers (para no meter al admin en todo)
    users = list(User.objects.filter(is_active=True, is_superuser=False))
    if len(users) < 2:
        print("[taskify_app] No hay suficientes usuarios para crear conversaciones.")
        return {"created_conversations": 0, "created_messages": 0, "errors": 0}

    created_conversations = 0
    created_messages = 0
    errors = 0

    # Mensajes “plantilla” para simular chats
    base_dialog = [
        "{sender}: Hola {receiver}, ¿qué tal? Quería comentarte un tema sobre un servicio.",
        "{receiver}: ¡Hola {sender}! Claro, dime, ¿en qué puedo ayudarte?",
        "{sender}: Estoy interesado en contratar uno de tus servicios. ¿Tienes disponibilidad esta semana?",
        "{receiver}: Sí, podría hacer un hueco el jueves por la tarde o el viernes por la mañana.",
        "{sender}: Perfecto, el jueves por la tarde me va genial. Muchas gracias.",
        "{receiver}: Genial, entonces lo agendamos. ¡Nos vemos pronto!",
    ]

    # Recorremos todas las parejas de usuarios (i < j)
    for i in range(len(users)):
        for j in range(i + 1, len(users)):
            u1 = users[i]
            u2 = users[j]

            try:
                # Buscar conversación que tenga SOLO a estos 2 participantes
                conv = (
                    Conversation.objects
                    .filter(participants=u1)
                    .filter(participants=u2)
                    .annotate(num_participants=Count("participants"))
                    .filter(num_participants=2)
                    .first()
                )

                if not conv:
                    conv = Conversation.objects.create()
                    conv.participants.add(u1, u2)
                    created_conversations += 1
                    print(f"[taskify_app] Conversación creada entre {u1.username} y {u2.username}")
                else:
                    print(f"[taskify_app] Conversación ya existía entre {u1.username} y {u2.username}")

                # Si ya tiene mensajes, no tocamos nada (idempotente)
                if conv.messages.exists():
                    continue

                # Creamos mensajes alternando sender/receiver
                # Índices pares: u1 habla; impares: u2 responde (o al revés)
                for idx, template in enumerate(base_dialog):
                    if idx % 2 == 0:
                        sender = u1
                        receiver = u2
                    else:
                        sender = u2
                        receiver = u1

                    text = template.format(sender=sender.first_name or sender.username,
                                           receiver=receiver.first_name or receiver.username)

                    Message.objects.create(
                        conversation=conv,
                        sender=sender,
                        content=text,
                    )
                    created_messages += 1

            except Exception as e:
                print(f"[taskify_app] Error creando conversación/mensajes entre {u1.username} y {u2.username}: {e}")
                errors += 1

    print(
        f"[taskify_app] Conversaciones de ejemplo -> "
        f"creadas: {created_conversations}, mensajes creados: {created_messages}, errores: {errors}"
    )
    return {
        "created_conversations": created_conversations,
        "created_messages": created_messages,
        "errors": errors,
    }



def create_default_categories(sender, **kwargs):
    from .models import Category

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
