from .models import Product
from django.conf import settings
from django.core.cache import cache


def get_products_by_category(category_id):
    if getattr(settings, 'CACHE_ENABLED', True):
        cache_key = f'products_in_category_{category_id}'
        products = cache.get(cache_key)

        if products is None:
            products = list(Product.objects.filter(category_id=category_id))
            cache.set(cache_key, products, timeout=60 * 5)
        return products

    # если кеширование выключено — просто вернуть из БД
    return list(Product.objects.filter(category_id=category_id))
