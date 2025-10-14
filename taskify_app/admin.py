from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Avg, Count
from django import forms

from .models import (
    Category,
    Favorite,
    Review,
    Service,
    ServiceCategory,
    Contract, CustomUser
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # añade aquí tus campos extra si tienes
    # Ejemplo si añadiste 'company' y 'phone':
    fieldsets = UserAdmin.fieldsets + (
        ('Extra', {'fields': ('company', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets
    # MUY IMPORTANTE para que el autocompletado funcione:
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('id',)


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ("code", "user", "service", "status", "start_date", "price", "created_at")
    list_filter = ("status", "service", "created_at")
    search_fields = ("code", "user__username", "service__name")


# ---------- Utilities ----------

class ReviewAdminForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = "__all__"

    def clean_rating(self):
        rating = self.cleaned_data["rating"]
        if rating < 1 or rating > 5:
            raise forms.ValidationError("El rating debe estar entre 1 y 5.")
        return rating


# ---------- Inlines ----------

class ServiceCategoryInline(admin.TabularInline):
    model = ServiceCategory
    extra = 1
    autocomplete_fields = ("category",)
    verbose_name = "Categoría del servicio"
    verbose_name_plural = "Categorías del servicio"


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")


class FavoriteInline(admin.TabularInline):
    model = Favorite
    extra = 0
    autocomplete_fields = ("user",)
    readonly_fields = ("favorited_at",)


# ---------- ModelAdmins ----------

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "description_short", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)

    @admin.display(description="Descripción", ordering="description")
    def description_short(self, obj):
        return (obj.description[:60] + "…") if obj.description and len(obj.description) > 60 else obj.description


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "provider",
        "categories_list",
        "avg_rating",
        "ratings_count",
        "created_at",
    )
    list_filter = ("created_at", "updated_at", "categories")
    search_fields = ("name", "description", "provider__username", "provider__email")
    autocomplete_fields = ("provider",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [ServiceCategoryInline, ReviewInline, FavoriteInline]
    ordering = ("name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _avg_rating=Avg("reviews__rating"),
            _ratings_count=Count("reviews"),
        ).prefetch_related("categories")

    @admin.display(description="Categorías")
    def categories_list(self, obj):
        # evita consultas N+1 gracias a prefetch_related en get_queryset
        names = [c.name for c in obj.categories.all()]
        return ", ".join(names) if names else "-"

    @admin.display(description="★ Media", ordering="_avg_rating")
    def avg_rating(self, obj):
        return f"{obj._avg_rating:.2f}" if obj._avg_rating is not None else "-"

    @admin.display(description="# Valoraciones", ordering="_ratings_count")
    def ratings_count(self, obj):
        return obj._ratings_count


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("service", "category")
    search_fields = ("service__name", "category__name")
    autocomplete_fields = ("service", "category")
    list_select_related = ("service", "category")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    form = ReviewAdminForm
    list_display = ("service", "user", "rating", "comment_short", "created_at")
    list_filter = ("rating", "created_at", "updated_at", "service")
    search_fields = ("service__name", "user__username", "user__email", "comment")
    autocomplete_fields = ("user", "service")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    @admin.display(description="Comentario", ordering="comment")
    def comment_short(self, obj):
        return (obj.comment[:60] + "…") if obj.comment and len(obj.comment) > 60 else obj.comment


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "service", "favorited_at")
    list_filter = ("favorited_at", "service")
    search_fields = ("user__username", "user__email", "service__name")
    autocomplete_fields = ("user", "service")
    readonly_fields = ("favorited_at",)
    ordering = ("-favorited_at",)
