from django.core.management.base import BaseCommand

from catalog.models import Product, Category


class Command(BaseCommand):
    help = 'Add products to the database'

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(name="Крупа", description="Рассыпчатые зерна")

        my_products = [
            {'name': "Пшено", 'description': "Желтая крупа для вкусных каш", 'category': category, 'purchase_price': 70},
            {'name': "Рис", 'description': "Белая крупа для плова", 'category': category, 'purchase_price': 120},
        ]

        for product in my_products:
            my_products, created = Product.objects.get_or_create(**product)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Успешное создание продукта: {my_products.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Продукт {my_products.name} уже существует'))
