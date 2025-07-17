import django_filters
from rest_framework import filters
from api.models import Product


class InStockFilterBackend(filters.BaseFilterBackend):
    """
    Filter that only allows users to see their own objects
    """

    def filter_queryset(self, request, queryset, view):
        return queryset.filter(stock__gt=0)


class ProductFilter(django_filters.FilterSet):
    class Meta:
        model = Product
        fields = {
            "name": ["iexact", "icontains"],
            "price": ["exact", "lt", "gt", "range"],
        }
