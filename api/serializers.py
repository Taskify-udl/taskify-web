from rest_framework import serializers
from django.contrib.auth.models import User
from slugify import slugify

from taskify_app.models import Category, Service, Review, Contract, Favorite, CustomUser


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password']


class ServiceSerializer(serializers.ModelSerializer):
    provider = serializers.PrimaryKeyRelatedField(read_only=True)

    # lectura (mostrar nombres)
    category_names = serializers.SerializerMethodField()

    # escritura (seguir aceptando IDs)
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
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_category_names(self, obj):
        return [c.name for c in obj.categories.all()]

    def update(self, instance, validated_data):
        validated_data.pop("provider", None)
        return super().update(instance, validated_data)

class ReviewSerializer(serializers.ModelSerializer):
    # Solo lectura
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    user_username = serializers.SerializerMethodField()
    service_name = serializers.SerializerMethodField()

    # Escritura por ID
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
        # proteger campos inmutables
        validated_data.pop("user", None)
        validated_data.pop("service", None)
        return super().update(instance, validated_data)


class ContractSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    user_username = serializers.SerializerMethodField()
    service_name = serializers.SerializerMethodField()

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
            "price",
            "created_at",
        )
        read_only_fields = ("code", "created_at")

    def get_user_username(self, obj):
        return getattr(obj.user, "username", None)

    def get_service_name(self, obj):
        return getattr(obj.service, "name", None)

    def update(self, instance, validated_data):
        validated_data.pop("user", None)
        validated_data.pop("code", None)
        validated_data.pop("service", None)
        return super().update(instance, validated_data)

class CategorySerializer(serializers.ModelSerializer):
    # lectura extra: cuántos servicios usan la categoría (anotado en la vista)
    service_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "service_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def _ensure_slug(self, name, slug):
        # Genera slug si viene vacío; si viene, lo respeta
        base = slug or slugify(name or "")
        return base

    def validate(self, attrs):
        # Normaliza slug si no viene
        name = attrs.get("name", getattr(self.instance, "name", None))
        slug = attrs.get("slug", getattr(self.instance, "slug", ""))
        attrs["slug"] = self._ensure_slug(name, slug)
        return attrs

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Si cambian name y no mandan slug, regeneramos automáticamente
        if "name" in validated_data and "slug" not in validated_data:
            validated_data["slug"] = self._ensure_slug(validated_data["name"], instance.slug)
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
