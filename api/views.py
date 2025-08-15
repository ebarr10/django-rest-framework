from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_headers
from django.views.decorators.cache import cache_page
from django.db.models import Max
from api.serializers import (
    OrderSerializer,
    ProductSerializer,
    OrderItemSerializer,
    ProductInfoSerializer,
    OrderCreateSerializer,
    UserSerializer,
)
from api.models import Order, Product, OrderItem, User
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.views import APIView
from rest_framework import generics, filters
from api.filters import OrderFilter, ProductFilter, InStockFilterBackend
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework import viewsets
from rest_framework.throttling import ScopedRateThrottle
from api.throttles import GetThrottle, PostThrottle
from api.tasks import send_order_confirmation_email


class ProductListCreateAPIView(generics.ListCreateAPIView):
    throttle_scope = "products"
    throttle_classes = [ScopedRateThrottle]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
        InStockFilterBackend,
    ]
    search_fields = ["=name", "description"]
    ordering_fields = ["name", "price", "stock"]
    pagination_class = None
    # pagination_class = PageNumberPagination
    # pagination_class.page_size = 2
    # pagination_class.page_query_param = "pagenum"
    # pagination_class.page_size_query_param = "size"
    # pagination_class.max_page_size = 6

    @method_decorator(cache_page(60 * 15, key_prefix="product_list"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        import time

        time.sleep(2)
        return super().get_queryset()

    def get_permissions(self):
        self.permission_classes = [AllowAny]
        if self.request.method == "POST":
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()


class AvailableProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.filter(stock__gt=0)
    serializer_class = ProductSerializer


class OutOfStockProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.exclude(stock__gt=0)
    serializer_class = ProductSerializer


class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_url_kwarg = "product_id"

    def get_permissions(self):
        self.permission_classes = [AllowAny]
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()


class OrderViewSet(viewsets.ModelViewSet):
    # throttle_scope = "orders"
    throttle_classes = [GetThrottle, PostThrottle]
    queryset = Order.objects.prefetch_related("items__product")
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filterset_class = OrderFilter
    filter_backends = [DjangoFilterBackend]

    @method_decorator(cache_page(60 * 15, key_prefix="order_list"))
    @method_decorator(vary_on_headers("Authorization"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        order = serializer.save(user=self.request.user)
        send_order_confirmation_email.delay_on_commit(
            order.order_id, self.request.user.email
        )

    def get_serializer_class(self):
        # can also check if POST: if self.request.method == "POST"
        if self.action == "create" or self.action == "update":
            return OrderCreateSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs


# class UserOrderListAPIView(generics.ListAPIView):
#     queryset = Order.objects.prefetch_related("items__product")
#     serializer_class = OrderSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         qs = super().get_queryset()
#         return qs.filter(user=self.request.user)


class ProductInfoAPIView(APIView):
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductInfoSerializer(
            {
                "products": products,
                "count": len(products),
                "max_price": products.aggregate(max_price=Max("price"))["max_price"],
            },
        )
        return Response(serializer.data)


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = None
