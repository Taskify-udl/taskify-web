from rest_framework import serializers
from taskify_app.models import Category, Service, ServiceCategory, Contract, Review, Favorite


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class ServiceSerializer(serializers.ModelSerializer):
    # El provider lo fija el servidor (request.user) en perform_create
    provider = serializers.PrimaryKeyRelatedField(read_only=True)
    # categorías como lista de IDs
    categories = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Category.objects.all(), required=False
    )

    class Meta:
        model = Service
        fields = ("id", "name", "description", "provider", "categories", "created_at", "updated_at")
        read_only_fields = ("provider", "created_at", "updated_at")

    def update(self, instance, validated_data):
        # impedir cambiar el provider vía API
        validated_data.pop("provider", None)
        return super().update(instance, validated_data)


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ("id", "service", "category")


class ContractSerializer(serializers.ModelSerializer):
    # UUID se genera solo y el user lo fija el servidor
    code = serializers.UUIDField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Contract
        fields = ("id", "code", "user", "service", "start_date", "status", "price", "created_at")
        read_only_fields = ("code", "user", "created_at")

    def update(self, instance, validated_data):
        validated_data.pop("user", None)
        return super().update(instance, validated_data)


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ("id", "user", "service", "rating", "comment", "created_at", "updated_at")
        read_only_fields = ("user", "created_at", "updated_at")

    def update(self, instance, validated_data):
        validated_data.pop("user", None)
        return super().update(instance, validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Favorite
        fields = ("id", "user", "service", "favorited_at")
        read_only_fields = ("user", "favorited_at")

    def update(self, instance, validated_data):
        validated_data.pop("user", None)
        return super().update(instance, validated_data)

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import Group
from rest_framework import serializers
User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password2 = serializers.CharField(write_only=True, trim_whitespace=False)
    role = serializers.ChoiceField(choices=("base", "provider"), default="base")

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ese nombre de usuario ya existe.")
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ese email ya está en uso.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Las contraseñas no coinciden."})
        # Valida contra las políticas de Django (longitud, comunes, numéricas...)
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        role = validated_data.pop("role", "base")
        validated_data.pop("password2", None)
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # Asigna grupo (si existe). No permitimos crear admin aquí.
        group = Group.objects.filter(name=role).first()
        if group:
            user.groups.add(group)

        return user
