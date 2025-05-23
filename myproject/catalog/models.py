from django.db import models


class Category(models.Model):
    name = models.CharField(
        max_length=150,
        verbose_name="Название категории",
        help_text="Введите название категории",
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Описание категории",
        help_text="Введите описание категории",
    )
    category_updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Последняя модификация"
    )

    def __str__(self):
        return f"name: {self.name}, description: {self.description}"

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"
        ordering = ["name", "description"]
