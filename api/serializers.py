from rest_framework import serializers
from django.contrib.auth.models import User
from slugify import slugify

from taskify_app.models import Category, Service, Review, Contract, Favorite, CustomUser, ServiceImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon']


# serializers.py
from rest_framework import serializers
from taskify_app.models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password', 'role']

    def create(self, validated_data):
        password = validated_data.pop('password')

        user = CustomUser.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    avatar = serializers.ImageField(required=False, allow_null=True)
    username = serializers.CharField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
            "bio",
            "location",
            "website",
            "avatar",
            "password",
        ]
        read_only_fields = ["id", "is_superuser", "is_staff", "username"]

    def update(self, instance, validated_data):
        validated_data.pop("username", None)
        password = validated_data.pop("password", None)
        validated_data.pop("role", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class PublicUserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone",
            "role",
            "bio",
            "location",
            "website",
            "avatar",
        ]


# --- Nuevo Serializer para las imágenes ---
class ServiceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceImage
        fields = ['id', 'image']


# --- Modificación del ServiceSerializer ---
class ServiceSerializer(serializers.ModelSerializer):
    provider = serializers.PrimaryKeyRelatedField(read_only=True)

    images = ServiceImageSerializer(many=True, read_only=True)

    uploaded_images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )

    category_names = serializers.SerializerMethodField()
    categories = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Category.objects.all(), required=False
    )

    class Meta:
        model = Service
        fields = (
            "id",
            "name",
            "description",
            "provider",
            "categories",
            "category_names",
            "price",
            "images",
            "uploaded_images",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_category_names(self, obj):
        return [c.name for c in obj.categories.all()]

    # --- Lógica para CREAR servicio + imágenes ---
    def create(self, validated_data):
        # 1. Sacamos las imágenes (esto ya lo tenías)
        uploaded_images = validated_data.pop("uploaded_images", [])

        # 2. SACAR LAS CATEGORÍAS (¡ESTA ES LA CLAVE!)
        # Si no hacemos esto, Django intenta guardarlas en el .create() y explota
        categories = validated_data.pop("categories", [])

        # 3. Creamos el servicio LIMPIO (sin imágenes ni categorías, solo campos simples)
        service = Service.objects.create(**validated_data)

        # 4. AHORA que el servicio tiene ID, asignamos las categorías
        service.categories.set(categories)

        # 5. Creamos las imágenes asociadas
        for image in uploaded_images:
            ServiceImage.objects.create(service=service, image=image)

        return service

    # --- Lógica para ACTUALIZAR servicio + agregar nuevas imágenes ---
    def update(self, instance, validated_data):
        validated_data.pop("provider", None)

        uploaded_images = validated_data.pop("uploaded_images", [])
        for image in uploaded_images:
            ServiceImage.objects.create(service=instance, image=image)

        return super().update(instance, validated_data)


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    user_username = serializers.SerializerMethodField()
    service_name = serializers.SerializerMethodField()

    service = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        required=True
    )

    rating = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = Review
        fields = (
            "id",
            "user",
            "user_username",
            "service",
            "service_name",
            "rating",
            "comment",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_user_username(self, obj):
        return getattr(obj.user, 'username', None)

    def get_service_name(self, obj):
        return getattr(obj.service, 'name', None)

    def update(self, instance, validated_data):
        validated_data.pop("user", None)
        validated_data.pop("service", None)
        return super().update(instance, validated_data)


class ContractSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    user_username = serializers.SerializerMethodField()
    service_name = serializers.SerializerMethodField()

    # Limitar el campo status a las opciones definidas en Contract.Status
    status = serializers.ChoiceField(choices=list(Contract.Status.choices), required=False)

    # Exponer los códigos alfanuméricos solo en condiciones controladas
    start_code_alpha = serializers.SerializerMethodField(read_only=True)
    end_code_alpha = serializers.SerializerMethodField(read_only=True)

    service = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        required=True
    )

    class Meta:
        model = Contract
        fields = (
            "id",
            "code",
            "user",
            "user_username",
            "service",
            "service_name",
            "start_date",
            "status",
            "start_code_alpha",
            "end_code_alpha",
            "price",
            "created_at",
        )
        read_only_fields = ("code", "created_at")

    def get_user_username(self, obj):
        return getattr(obj.user, "username", None)

    def get_service_name(self, obj):
        return getattr(obj.service, "name", None)

    def _request_user_is_service_provider_with_role(self, request_user, obj):
        """
        Devuelve True si `request_user` tiene un rol proveedor y es el proveedor del servicio del contrato.
        """
        if not request_user or not getattr(request_user, 'is_authenticated', False):
            return False
        provider_roles = [
            CustomUser.Roles.PROVIDER,
            CustomUser.Roles.FREELANCER,
            CustomUser.Roles.COMPANY_ADMIN,
            CustomUser.Roles.COMPANY_WORKER,
        ]
        user_role = getattr(request_user, 'role', None)
        # además comprobar que es el proveedor del service
        is_provider_of_service = getattr(obj.service, 'provider_id', None) == getattr(request_user, 'id', None)
        return user_role in provider_roles and is_provider_of_service

    def get_start_code_alpha(self, obj):
        request = self.context.get('request')
        # Mostrar código si el contrato está ACCEPTED o ACTIVE y el request.user es el proveedor con rol adecuado
        if obj.status in (Contract.Status.ACCEPTED, Contract.Status.ACTIVE) and self._request_user_is_service_provider_with_role(getattr(request, 'user', None), obj):
            return obj.start_code_alpha
        return None

    def get_end_code_alpha(self, obj):
        request = self.context.get('request')
        # Mostrar código si el contrato está ACCEPTED o ACTIVE y el request.user es el proveedor con rol adecuado
        if obj.status in (Contract.Status.ACCEPTED, Contract.Status.ACTIVE) and self._request_user_is_service_provider_with_role(getattr(request, 'user', None), obj):
            return obj.end_code_alpha
        return None

    def update(self, instance, validated_data):
        validated_data.pop("user", None)
        validated_data.pop("code", None)
        validated_data.pop("service", None)
        return super().update(instance, validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    service_name = serializers.SerializerMethodField()

    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())

    class Meta:
        model = Favorite
        fields = ("id", "user", "service", "service_name", "favorited_at")
        read_only_fields = ("favorited_at",)

    def get_service_name(self, obj):
        return getattr(obj.service, "name", None)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        raise serializers.ValidationError("Editar favoritos no está permitido.")


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
