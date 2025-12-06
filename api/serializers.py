from rest_framework import serializers
from django.contrib.auth.models import User
from slugify import slugify

from taskify_app.models import Category, Service, Review, Contract, Favorite, CustomUser


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'icon']


# serializers.py
from rest_framework import serializers
from taskify_app.models import CustomUser


# Asegúrate de importar tu modelo de usuario correcto

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
        # Asegurar que username no se modifique aunque venga en los datos
        validated_data.pop("username", None)
        password = validated_data.pop("password", None)
        role = validated_data.pop("role", None)
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
            "price",
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