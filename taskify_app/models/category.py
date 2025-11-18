from django.db import models

from taskify_app.utils.fa6_choices import FA6_FREE_ICON_CHOICES


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    icon = models.CharField(
        max_length=64,
        choices=FA6_FREE_ICON_CHOICES,
        default="fa-solid fa-user",
    )
    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
