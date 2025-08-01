from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from api.models import Product
from django.core.cache import cache


@receiver([post_save, post_delete], sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    """
    Invalidate product list caches when a product is created, updated, or deleted
    """
    print("Clearing Product Cache")

    # Clear product list caches
    cache.delete_pattern("*product_list*")
