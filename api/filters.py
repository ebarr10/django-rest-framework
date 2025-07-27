import django_filters
from rest_framework import filters
from api.models import Order, Product


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


class OrderFilter(django_filters.FilterSet):
    created = django_filters.DateFilter(field_name="created__date")

    class Meta:
        model = Order
        fields = {"status": ["exact"], "created": ["lt", "gt", "exact"]}
