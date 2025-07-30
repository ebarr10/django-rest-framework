from django.shortcuts import get_object_or_404
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


class ProductListCreateAPIView(generics.ListCreateAPIView):
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
    pagination_class = LimitOffsetPagination
    # pagination_class = PageNumberPagination
    # pagination_class.page_size = 2
    # pagination_class.page_query_param = "pagenum"
    # pagination_class.page_size_query_param = "size"
    # pagination_class.max_page_size = 6

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
        if self.request.method in ["PUT", "DELETE"]:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related("items__product")
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filterset_class = OrderFilter
    filter_backends = [DjangoFilterBackend]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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


class UserListView(generics.ListView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = None
