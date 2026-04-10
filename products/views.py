from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Category, Product
from .serializers import CategorySerializer, ProductListSerializer, ProductDetailSerializer
from .filters import ProductFilter
import django_filters


class CategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.filter(is_active=True, parent=None)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class ProductListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images', 'variants')

        # Manual filter application
        filterset = ProductFilter(request.GET, queryset=queryset)
        queryset = filterset.qs

        # Search
        search = request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search) | queryset.filter(description__icontains=search)
            queryset = queryset.distinct()

        # Ordering
        ordering = request.GET.get('ordering', '-created_at')
        allowed_orderings = ['price', '-price', '-created_at', 'created_at', 'name']
        if ordering in allowed_orderings:
            if 'price' in ordering:
                queryset = queryset.order_by(ordering.replace('price', 'variants__price')).distinct()
            else:
                queryset = queryset.order_by(ordering)

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = int(request.GET.get('page_size', 20))
        page = paginator.paginate_queryset(queryset, request)
        serializer = ProductListSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


class ProductDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            product = Product.objects.get(slug=slug, is_active=True)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductDetailSerializer(product, context={'request': request})
        return Response(serializer.data)
