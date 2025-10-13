from django.db import models

class ServiceCategory(models.Model):
    service = models.ForeignKey("taskify_app.Service", on_delete=models.CASCADE)
    category = models.ForeignKey("taskify_app.Category", on_delete=models.CASCADE)

    class Meta:
        unique_together = (("service", "category"),)
        indexes = [
            models.Index(fields=["service"]),
            models.Index(fields=["category"]),
        ]
        verbose_name = "Service category"
        verbose_name_plural = "Service categories"

    def __str__(self):
        return f"{self.service} → {self.category}"
